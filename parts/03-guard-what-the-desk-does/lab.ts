// What the checks in this part share: run the learner's tool guard in the desk lab and on the desk,
// on a fresh, throwaway world in replay mode, and read what the world wrote down.
// biome-ignore-all lint/style/useNamingConvention: the keys keep the world's snake_case spelling.
import { mkdtempSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { decisions, deskJson, python } from "../../checks/lib/desk";
import { has } from "../../checks/lib/files";
import type { RunFile } from "../../checks/lib/world-json";
import { ROOT } from "../../scripts/structure";

const LAB = join(ROOT, "parts", "03-guard-what-the-desk-does", "desk_lab.py");

export const guardsFile = (folder: string) => join(folder, "guards.py");
export const hasGuards = (folder: string) => has(folder, "guards.py");
const worldSet = (name: string) => join(ROOT, "world", "sets", `${name}.jsonl`);

/** One row of tool_calls.jsonl. */
export type ToolCall = {
  email_id: string;
  tool: string;
  verdict: string;
  rule: string;
  executed: boolean;
  task?: string;
};
/** One row of decisions.jsonl. */
export type Decision = {
  email_id: string;
  layer: string;
  rule: string;
  decision: string;
  reason: string;
  tool: string | null;
};
export type DeskRun = { runFile: RunFile | null; decisions: Decision[] };

/** Run the whole desk with the learner's guards on one shipped set, and read its logs. */
export function deskRun(folder: string, setName: string): DeskRun {
  const args = ["run", "--guards", guardsFile(folder), "--set", worldSet(setName)];
  const { data, ran } = deskJson<RunFile>(args, folder);
  return { runFile: data, decisions: decisions(ran.state) as Decision[] };
}

/** Three fresh desk runs. Model-dependent behaviour must hold on every one. */
export function threeDeskRuns(folder: string, setName: string): DeskRun[] {
  return [0, 1, 2].map(() => deskRun(folder, setName));
}

/** The share of benign emails in one run that reached the expected end state. */
export const utility = (oneRun: DeskRun) => oneRun.runFile?.utility?.rate ?? 0;

function labEnvironment(stateFolder: string): Record<string, string | undefined> {
  const environment: Record<string, string | undefined> = { ...process.env };
  environment.PYTHONPATH = [ROOT, join(ROOT, "world")].join(":");
  environment.MARROWFIELD_STATE = stateFolder;
  environment.LLM_PROVIDER = "replay";
  environment.PYTHONDONTWRITEBYTECODE = "1";
  return environment;
}

/** Run one desk lab command from the learner's folder and return the JSON it wrote. */
export function labJson<Shape>(command: string, args: string[], folder: string): Shape | null {
  const stateFolder = mkdtempSync(join(tmpdir(), "desk-lab-"));
  const outFile = join(stateFolder, "out.json");
  const commandLine = [python(), LAB, command, ...args, "--out", outFile];
  Bun.spawnSync(commandLine, { cwd: folder, env: labEnvironment(stateFolder) });
  try {
    return JSON.parse(readFileSync(outFile, "utf8")) as Shape;
  } catch {
    return null;
  }
}

/** Remember an answer per folder, so a slow run happens once for all the rules of a check. */
export function oncePerFolder<Answer>(
  work: (folder: string) => Answer,
): (folder: string) => Answer {
  const saved = new Map<string, Answer>();
  return (folder: string) => {
    if (!saved.has(folder)) saved.set(folder, work(folder));
    return saved.get(folder) as Answer;
  };
}

/** One row of the policy table, as `desk_lab.py table` writes it. */
export type TableCell = {
  name: string;
  tool: string;
  wanted: string;
  decision: string;
  rule: string;
};

/** The policy table from a fresh lab run, or [] when the guard cannot load. */
export const policyTable = oncePerFolder((folder: string) => {
  if (!hasGuards(folder)) return [] as TableCell[];
  return labJson<TableCell[]>("table", ["--guards", guardsFile(folder)], folder) ?? [];
});

/** The benign set, three fresh runs. */
export const benignRuns = oncePerFolder((folder: string) =>
  hasGuards(folder) ? threeDeskRuns(folder, "benign") : [],
);

export const everyRunKeepsUtility = (runs: DeskRun[]) =>
  runs.length === 3 && runs.every((oneRun) => utility(oneRun) >= 0.9);

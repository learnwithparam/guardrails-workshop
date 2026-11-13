// What the Part 2 checks share: run the learner's guards on the desk and in the guard lab,
// on a fresh, throwaway world in replay mode, and read what the world wrote down.
// biome-ignore-all lint/style/useNamingConvention: the keys keep the world's snake_case spelling.
import { mkdtempSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { decisions, deskJson, python } from "../../checks/lib/desk";
import { has } from "../../checks/lib/files";
import type { RunFile } from "../../checks/lib/world-json";
import { ROOT } from "../../scripts/structure";

const LAB = join(ROOT, "parts", "02-guard-what-comes-in", "guard_lab.py");

export const guardsFile = (folder: string) => join(folder, "guards.py");
export const hasGuards = (folder: string) => has(folder, "guards.py");
export const worldSet = (name: string) => join(ROOT, "world", "sets", `${name}.jsonl`);

export type InputVerdict = { email_id: string; layer: string; decision: string; reason: string };
export type DeskRun = { verdicts: Map<string, InputVerdict>; runFile: RunFile | null };

/** Run the whole desk with the learner's guards on one shipped set, and read its logs. */
export function deskRun(folder: string, setName: string): DeskRun {
  const args = ["run", "--guards", guardsFile(folder), "--set", worldSet(setName)];
  const { data, ran } = deskJson<RunFile>(args, folder);
  const verdicts = new Map<string, InputVerdict>();
  for (const row of decisions(ran.state) as InputVerdict[]) {
    if (row.layer === "input") verdicts.set(row.email_id, row);
  }
  return { verdicts, runFile: data };
}

/** Three fresh desk runs. Model-dependent behaviour must hold on every one. */
export function threeDeskRuns(folder: string, setName: string): DeskRun[] {
  return [0, 1, 2].map(() => deskRun(folder, setName));
}

export const isFlagged = (verdict: InputVerdict | undefined) =>
  verdict?.decision === "review" || verdict?.decision === "block";

/** The share of emails in one run that the input guard flagged (review or block). */
export function flaggedShare(oneRun: DeskRun): number {
  const emails = oneRun.runFile?.emails ?? [];
  if (emails.length === 0) return 0;
  const flagged = emails.filter((email) => isFlagged(oneRun.verdicts.get(email.id)));
  return flagged.length / emails.length;
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

/** Run one guard lab command from the learner's folder and return the JSON it wrote. */
export function labJson<Shape>(command: string, args: string[], folder: string): Shape | null {
  const stateFolder = mkdtempSync(join(tmpdir(), "guard-lab-"));
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

// Helpers the checks of this part share: ask a learner's output guard directly,
// and run the desk with only the output layer switched on.
// Every run uses replay mode and a fresh, throwaway copy of the world.
import { mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { python } from "../../checks/lib/desk";
import type { RunFile, SetRow } from "../../checks/lib/world-json";
import { ROOT } from "../../scripts/structure";

const PART_FOLDER = import.meta.dir;

/** One planted message for the output guard. */
export type MessageCase = {
  channel: "chef" | "email";
  text: string;
  site?: string;
  to?: string;
  dropHosts?: string[];
};

export type GuardAnswer = { decision?: string; rule?: string; reason?: string };

const newFolder = (prefix: string) => mkdtempSync(join(tmpdir(), prefix));

function replayEnvironment(stateFolder: string, guards = ""): Record<string, string | undefined> {
  const environment: Record<string, string | undefined> = { ...process.env };
  environment.PYTHONPATH = [ROOT, join(ROOT, "world")].join(":");
  environment.MARROWFIELD_STATE = stateFolder;
  environment.LLM_PROVIDER = "replay";
  environment.PYTHONDONTWRITEBYTECODE = "1";
  environment.GUARDS_UNDER_TEST = guards;
  return environment;
}

function spawnPython(args: string[], environment: Record<string, string | undefined>) {
  const finished = Bun.spawnSync([python(), ...args], {
    cwd: newFolder("marrowfield-cwd-"),
    env: environment,
    stdout: "pipe",
    stderr: "pipe",
  });
  return { ok: finished.exitCode === 0, out: finished.stdout.toString() };
}

/** Send each case to the guard's output layer and return its answers, or null if it failed. */
export function askOutputGuard(guards: string, cases: MessageCase[]): GuardAnswer[] | null {
  const folder = newFolder("marrowfield-cases-");
  const casesFile = join(folder, "cases.json");
  const asPython = cases.map((messageCase) => ({ ...messageCase, drop_hosts: messageCase.dropHosts }));
  writeFileSync(casesFile, JSON.stringify(asPython));
  const script = join(PART_FOLDER, "ask_guards.py");
  const ran = spawnPython([script, guards, casesFile], replayEnvironment(folder));
  if (!ran.ok) return null;
  try {
    return JSON.parse(ran.out) as GuardAnswer[];
  } catch {
    return null;
  }
}

/** Write rows to a fresh set file and return its path. */
export function writeSet(rows: SetRow[]): string {
  const path = join(newFolder("marrowfield-set-"), "set.jsonl");
  const lines = rows.map((row) => JSON.stringify(row));
  writeFileSync(path, `${lines.join("\n")}\n`);
  return path;
}

/** Run the desk on a set with only the guards' output layer on. Returns what `desk run` wrote. */
export function runOutputLayerOnly(guards: string, rows: SetRow[]): RunFile | null {
  const stateFolder = newFolder("marrowfield-");
  const outFile = join(stateFolder, "out.json");
  const layerFile = join(PART_FOLDER, "output_layer_only.py");
  const deskArgs = ["run", "--guards", layerFile, "--set", writeSet(rows), "--out", outFile];
  const environment = replayEnvironment(stateFolder, guards);
  spawnPython(["-m", "marrowfield", "desk", ...deskArgs], environment);
  try {
    return JSON.parse(readFileSync(outFile, "utf8")) as RunFile;
  } catch {
    return null;
  }
}

/** The answers that blocked, as a share of all answers. */
export function blockedShare(answers: GuardAnswer[]): number {
  if (answers.length === 0) return 0;
  const blocked = answers.filter((answer) => answer.decision === "block");
  return blocked.length / answers.length;
}

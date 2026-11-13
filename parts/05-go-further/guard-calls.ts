// Helpers the checks of this part share: ask a learner's guards directly, and run the desk
// with some layers or the injection detector switched off (through switches.py).
// Every run uses replay mode and a fresh, throwaway copy of the world.
import { mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { python } from "../../checks/lib/desk";
import type { SetRow } from "../../checks/lib/world-json";
import { ROOT } from "../../scripts/structure";

export const PART_FOLDER = import.meta.dir;

/** One request for ask_guards.py. See that file for the fields each layer takes. */
export type GuardCase = { layer: "input" | "tool" | "output"; [field: string]: unknown };

export type GuardAnswer = {
  decision?: string;
  rule?: string;
  reason?: string;
  plan?: string[];
};

/** Switches for switches.py: the layers to keep on, and whether the detector is off. */
export type Switches = { layers?: string; detector?: "on" | "off"; extra?: Record<string, string> };

export const newFolder = (prefix: string) => mkdtempSync(join(tmpdir(), prefix));

export function replayEnvironment(
  stateFolder: string,
  guards = "",
  switches: Switches = {},
): Record<string, string | undefined> {
  const environment: Record<string, string | undefined> = { ...process.env };
  environment.PYTHONPATH = [ROOT, join(ROOT, "world")].join(":");
  environment.MARROWFIELD_STATE = stateFolder;
  environment.LLM_PROVIDER = "replay";
  environment.PYTHONDONTWRITEBYTECODE = "1";
  environment.GUARDS_UNDER_TEST = guards;
  environment.LAYERS = switches.layers ?? "input,tool,output,result";
  environment.DETECTOR = switches.detector ?? "on";
  return { ...environment, ...switches.extra };
}

export function spawnPython(
  args: string[],
  environment: Record<string, string | undefined>,
  workFolder: string = newFolder("marrowfield-cwd-"),
) {
  const finished = Bun.spawnSync([python(), ...args], {
    cwd: workFolder,
    env: environment,
    stdout: "pipe",
    stderr: "pipe",
  });
  return { ok: finished.exitCode === 0, out: finished.stdout.toString(), workFolder };
}

/** Send each case to the guards and return their answers, or [] if the guards failed to load. */
export function askGuards(guards: string, cases: GuardCase[]): GuardAnswer[] {
  const folder = newFolder("marrowfield-cases-");
  const casesFile = join(folder, "cases.json");
  writeFileSync(casesFile, JSON.stringify(cases));
  const script = join(PART_FOLDER, "ask_guards.py");
  const ran = spawnPython([script, guards, casesFile], replayEnvironment(folder));
  if (!ran.ok) return [];
  try {
    return JSON.parse(ran.out) as GuardAnswer[];
  } catch {
    return [];
  }
}

/** Write rows to a fresh set file and return its path. */
export function writeSet(rows: SetRow[]): string {
  const path = join(newFolder("marrowfield-set-"), "set.jsonl");
  const lines = rows.map((row) => JSON.stringify(row));
  writeFileSync(path, `${lines.join("\n")}\n`);
  return path;
}

export type DeskRun<Shape> = { data: Shape | null; stateFolder: string; workFolder: string };

/**
 * Run a desk command with the guards behind switches.py, and read the JSON it wrote with --out.
 * The command runs in an empty folder, so files the guards write land there.
 */
export function runSwitched<Shape>(
  guards: string,
  deskArgs: string[],
  switches: Switches = {},
): DeskRun<Shape> {
  const stateFolder = newFolder("marrowfield-");
  const outFile = join(stateFolder, "out.json");
  const switchFile = join(PART_FOLDER, "switches.py");
  const args = ["-m", "marrowfield", "desk", ...deskArgs, "--guards", switchFile, "--out", outFile];
  const ran = spawnPython(args, replayEnvironment(stateFolder, guards, switches));
  try {
    const data = JSON.parse(readFileSync(outFile, "utf8")) as Shape;
    return { data, stateFolder, workFolder: ran.workFolder };
  } catch {
    return { data: null, stateFolder, workFolder: ran.workFolder };
  }
}

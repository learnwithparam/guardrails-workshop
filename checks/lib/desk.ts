// Start the learner's work and read what the world recorded. Checks never read the model's reply.
// Every run here uses replay mode and a fresh, throwaway copy of the world,
// so a check never touches your state.
import { existsSync, mkdtempSync, readdirSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { ROOT } from "../../scripts/structure";
import { parseJsonLines } from "./files";
import type { EmailResult } from "./world-json";

export type { EmailResult };

/**
 * The Python that runs the desk: the project's .venv if `uv sync` made one,
 * else python3 (the standard library is enough in replay mode).
 */
export function python(): string {
  const venvPython = join(ROOT, ".venv", "bin", "python");
  return existsSync(venvPython) ? venvPython : "python3";
}

export type Ran = { ok: boolean; code: number; out: string; state: string };

type Program = "desk" | "world";

const newStateFolder = () => mkdtempSync(join(tmpdir(), "marrowfield-"));

function replayEnvironment(stateFolder: string): Record<string, string | undefined> {
  const environment: Record<string, string | undefined> = { ...process.env };
  environment.PYTHONPATH = [ROOT, join(ROOT, "world")].join(":");
  environment.MARROWFIELD_STATE = stateFolder;
  // Replay mode answers from saved model replies, so a check needs no key and costs nothing.
  environment.LLM_PROVIDER = "replay";
  environment.PYTHONDONTWRITEBYTECODE = "1";
  return environment;
}

/** Run `desk <args>` (or `world <args>`) from `workFolder`, against a fresh world. */
export function run(
  program: Program,
  args: string[],
  workFolder: string = ROOT,
  stateFolder: string = newStateFolder(),
): Ran {
  const finished = Bun.spawnSync([python(), "-m", "marrowfield", program, ...args], {
    cwd: workFolder,
    env: replayEnvironment(stateFolder),
    stdout: "pipe",
    stderr: "pipe",
  });
  const out = finished.stdout.toString() + finished.stderr.toString();
  const code = finished.exitCode ?? 2;
  return { ok: finished.exitCode === 0, code, out, state: stateFolder };
}

/**
 * Run the same thing three times on fresh worlds.
 * Behaviour that depends on a model is judged on all three.
 */
export function threeRuns(program: Program, args: string[], workFolder: string = ROOT): Ran[] {
  return [0, 1, 2].map(() => run(program, args, workFolder));
}

/** Every run folder a command wrote under its state folder. */
export function runFolders(stateFolder: string): string[] {
  const runsFolder = join(stateFolder, "runs");
  if (!existsSync(runsFolder)) return [];
  const names = readdirSync(runsFolder).sort();
  return names.map((name) => join(runsFolder, name));
}

export function jsonl<Row>(path: string): Row[] {
  if (!existsSync(path)) return [];
  return parseJsonLines<Row>(readFileSync(path, "utf8"));
}

/** Per-email results from the world's run logs (results.jsonl), keyed by email id. */
export function results(stateFolder: string): Map<string, EmailResult> {
  const byEmail = new Map<string, EmailResult>();
  for (const runFolder of runFolders(stateFolder)) {
    for (const result of jsonl<EmailResult>(join(runFolder, "results.jsonl"))) {
      byEmail.set(result.email_id, result);
    }
  }
  return byEmail;
}

/** Every tool call the desk proposed, with the guard verdict, from tool_calls.jsonl. */
export function toolCalls(stateFolder: string): Record<string, unknown>[] {
  const folders = runFolders(stateFolder);
  return folders.flatMap((runFolder) => jsonl(join(runFolder, "tool_calls.jsonl")));
}

/** Every guard decision, from decisions.jsonl. */
export function decisions(stateFolder: string): Record<string, unknown>[] {
  const folders = runFolders(stateFolder);
  return folders.flatMap((runFolder) => jsonl(join(runFolder, "decisions.jsonl")));
}

/** Run a desk command that writes JSON with --out, and return what it wrote (null if it failed). */
export function deskJson<Shape>(
  args: string[],
  workFolder: string = ROOT,
): { data: Shape | null; ran: Ran } {
  const stateFolder = newStateFolder();
  const outFile = join(stateFolder, "out.json");
  const ran = run("desk", [...args, "--out", outFile], workFolder, stateFolder);
  try {
    const data = JSON.parse(readFileSync(outFile, "utf8")) as Shape;
    return { data, ran };
  } catch {
    return { data: null, ran };
  }
}

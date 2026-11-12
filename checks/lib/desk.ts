// Start the learner's work and read what the world recorded. Checks never read the model's reply.
// Every run here uses replay mode and a fresh, throwaway copy of the world, so a check never touches your state.
import { existsSync, mkdtempSync, readdirSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { ROOT } from "../../scripts/structure";

/** The Python that runs the desk: the project's .venv if `uv sync` made one, else python3 (stdlib is enough in replay). */
export function python(): string {
  const venv = join(ROOT, ".venv", "bin", "python");
  return existsSync(venv) ? venv : "python3";
}

export type Ran = { ok: boolean; code: number; out: string; state: string };

/** Run `desk <args>` (or `world <args>`) from `cwd`, against a fresh world. */
export function run(
  cmd: "desk" | "world",
  args: string[],
  cwd: string = ROOT,
  state?: string,
): Ran {
  const st = state ?? mkdtempSync(join(tmpdir(), "marrowfield-"));
  const p = Bun.spawnSync([python(), "-m", "marrowfield", cmd, ...args], {
    cwd,
    env: {
      ...process.env,
      PYTHONPATH: [ROOT, join(ROOT, "world")].join(":"),
      MARROWFIELD_STATE: st,
      LLM_PROVIDER: "replay",
      PYTHONDONTWRITEBYTECODE: "1",
    },
    stdout: "pipe",
    stderr: "pipe",
  });
  const out = p.stdout.toString() + p.stderr.toString();
  return { ok: p.exitCode === 0, code: p.exitCode ?? 2, out, state: st };
}

/** Run the same thing three times on fresh worlds. Behaviour that depends on a model is judged on all three. */
export function threeRuns(cmd: "desk" | "world", args: string[], cwd: string = ROOT): Ran[] {
  return [0, 1, 2].map(() => run(cmd, args, cwd));
}

export type Result = {
  email_id: string;
  held: boolean;
  actions: { tool: string; verdict: string; rule: string }[];
  changes: { kind: string; [k: string]: unknown }[];
  forbidden: { kind: string; [k: string]: unknown }[];
};

/** Every run folder a command wrote under its state dir. */
export function runDirs(state: string): string[] {
  const d = join(state, "runs");
  return existsSync(d)
    ? readdirSync(d)
        .sort()
        .map((x) => join(d, x))
    : [];
}

export function jsonl<T = any>(path: string): T[] {
  if (!existsSync(path)) return [];
  return readFileSync(path, "utf8")
    .split("\n")
    .filter((l) => l.trim())
    .map((l) => JSON.parse(l));
}

/** Per-email results from the world's run logs (results.jsonl), keyed by email id. */
export function results(state: string): Map<string, Result> {
  const m = new Map<string, Result>();
  for (const d of runDirs(state))
    for (const r of jsonl<Result>(join(d, "results.jsonl"))) m.set(r.email_id, r);
  return m;
}

/** Every tool call the desk proposed, with the guard verdict, from tool_calls.jsonl. */
export function toolCalls(state: string): any[] {
  return runDirs(state).flatMap((d) => jsonl(join(d, "tool_calls.jsonl")));
}

/** Every guard decision, from decisions.jsonl. */
export function decisions(state: string): any[] {
  return runDirs(state).flatMap((d) => jsonl(join(d, "decisions.jsonl")));
}

/** Run a desk command that writes JSON with --out, and return what it wrote (null if it failed). */
export function deskJson(args: string[], cwd: string = ROOT): { data: any; ran: Ran } {
  const st = mkdtempSync(join(tmpdir(), "marrowfield-"));
  const out = join(st, "out.json");
  const ran = run("desk", [...args, "--out", out], cwd, st);
  let data = null;
  try {
    data = JSON.parse(readFileSync(out, "utf8"));
  } catch {
    data = null;
  }
  return { data, ran };
}

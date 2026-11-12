// Read the learner's files without throwing: a missing or broken file is a failed rule, not a crashed check.
import { existsSync, readFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { join } from "node:path";
import { ROOT } from "../../scripts/structure";

export const has = (dir: string, rel: string) => existsSync(join(dir, rel));

export function text(dir: string, rel: string): string {
  const p = join(dir, rel);
  return existsSync(p) ? readFileSync(p, "utf8") : "";
}

export function json<T = any>(dir: string, rel: string): T | null {
  try {
    return JSON.parse(text(dir, rel)) as T;
  } catch {
    return null;
  }
}

/** Rows of a .jsonl file, or null if any line is not valid JSON. */
export function jsonlRows(dir: string, rel: string): any[] | null {
  const t = text(dir, rel);
  if (!t.trim()) return null;
  try {
    return t.split("\n").filter((l) => l.trim()).map((l) => JSON.parse(l));
  } catch {
    return null;
  }
}

export const sha256 = (path: string) => (existsSync(path) ? createHash("sha256").update(readFileSync(path)).digest("hex") : "");

/** Find the set file a score was made from: the path it names, the same name in this folder, or the world's copy. */
export function findSet(dir: string, named: string | null, hash: string | null): string | null {
  if (!named) return null;
  const base = named.split("/").pop()!;
  for (const p of [join(ROOT, named), join(dir, named), join(dir, "sets", base), join(ROOT, "world", "sets", base)])
    if (existsSync(p) && (!hash || sha256(p) === hash)) return p;
  return null;
}

/** Lines of a markdown file that look like "Key: value". */
export function fields(md: string): Record<string, string> {
  const out: Record<string, string> = {};
  for (const l of md.split("\n")) {
    const m = l.match(/^\s*[-*]?\s*([A-Za-z][A-Za-z ]+?)\s*:\s*(.+?)\s*$/);
    if (m) out[m[1].toLowerCase()] = m[2];
  }
  return out;
}

export const world = (rel: string) => join(ROOT, "world", rel);

// Read the learner's files without throwing: a missing or broken file is a failed rule,
// not a crashed check.

import { createHash } from "node:crypto";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { ROOT } from "../../scripts/structure";

export const has = (folder: string, relativePath: string) => existsSync(join(folder, relativePath));

export function text(folder: string, relativePath: string): string {
  const path = join(folder, relativePath);
  if (!existsSync(path)) return "";
  return readFileSync(path, "utf8");
}

export function json<Shape = unknown>(folder: string, relativePath: string): Shape | null {
  try {
    return JSON.parse(text(folder, relativePath)) as Shape;
  } catch {
    return null;
  }
}

export function parseJsonLines<Row>(content: string): Row[] {
  const lines = content.split("\n");
  const filledLines = lines.filter((line) => line.trim());
  return filledLines.map((line) => JSON.parse(line) as Row);
}

/** Rows of a .jsonl file, or null if any line is not valid JSON. */
export function jsonlRows<Row>(folder: string, relativePath: string): Row[] | null {
  const content = text(folder, relativePath);
  if (!content.trim()) return null;
  try {
    return parseJsonLines<Row>(content);
  } catch {
    return null;
  }
}

export function sha256(path: string): string {
  if (!existsSync(path)) return "";
  const hash = createHash("sha256");
  hash.update(readFileSync(path));
  return hash.digest("hex");
}

/**
 * Find the set file a score was made from: the path it names, the same name in this folder,
 * or the world's copy.
 */
export function findSet(folder: string, named: string | null, hash: string | null): string | null {
  if (!named) return null;
  const fileName = named.split("/").at(-1) ?? named;
  const candidates = [
    join(ROOT, named),
    join(folder, named),
    join(folder, "sets", fileName),
    join(ROOT, "world", "sets", fileName),
  ];
  const matchesHash = (path: string) => !hash || sha256(path) === hash;
  return candidates.find((path) => existsSync(path) && matchesHash(path)) ?? null;
}

/** Lines of a markdown file that look like "Key: value", keyed by the lower-case key. */
export function fields(markdown: string): Record<string, string> {
  const found: Record<string, string> = {};
  for (const line of markdown.split("\n")) {
    const match = line.match(/^\s*[-*]?\s*([A-Za-z][A-Za-z ]+?)\s*:\s*(.+?)\s*$/);
    if (match) found[match[1].toLowerCase()] = match[2];
  }
  return found;
}

export const world = (relativePath: string) => join(ROOT, "world", relativePath);

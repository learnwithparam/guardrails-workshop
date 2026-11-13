// Run only the learner's own rows of a set, three times, so a check can judge what they really do.
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { deskJson } from "./desk";
import type { RunFile, SetRow } from "./world-json";

/** Write the rows to a fresh .jsonl file and return its path. */
function writeSetFile(rows: SetRow[], folderPrefix: string): string {
  const folder = mkdtempSync(join(tmpdir(), folderPrefix));
  const path = join(folder, "own.jsonl");
  const lines = rows.map((row) => JSON.stringify(row));
  writeFileSync(path, `${lines.join("\n")}\n`);
  return path;
}

/** Three runs of one desk ("--open" or "--reference") on the rows. A failed run is null. */
export function threeRunsOn(
  rows: SetRow[],
  desk: string,
  folderPrefix: string,
): (RunFile | null)[] {
  const setFile = writeSetFile(rows, folderPrefix);
  return [0, 1, 2].map(() => deskJson<RunFile>(["run", desk, "--set", setFile]).data);
}

export function emailInRun(runFile: RunFile | null, emailId: string) {
  return runFile?.emails.find((email) => email.id === emailId);
}

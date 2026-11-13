// redact-with-presidio: runs assignment/check.py on the learner's redact.py.
// The starter lives in assignment/, so a rule run on the step's problem folder tests that file.

import { spawnSync } from "node:child_process";
import { existsSync, mkdtempSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { basename, join } from "node:path";
import { ROOT } from "../scripts/structure";
import type { Rule } from "../scripts/verify";

const PRESIDIO = ["--with", "presidio-analyzer==2.2.366", "--with", "presidio-anonymizer==2.2.366"];
type Outcome = Record<string, "pass" | "fail">;

const outcomeCache = new Map<string, Outcome>();

function folderToTest(folder: string): string {
  return basename(folder) === "problem" ? join(ROOT, "assignment") : folder;
}

/** Runs assignment/check.py once per folder and reads each Done-when line back. */
function outcomeFor(folder: string): Outcome {
  const target = folderToTest(folder);
  const cached = outcomeCache.get(target);
  if (cached) return cached;
  const resultFile = join(mkdtempSync(join(tmpdir(), "presidio-")), "result.json");
  const checkFile = join(ROOT, "assignment", "check.py");
  spawnSync("uv", ["run", ...PRESIDIO, checkFile, target, resultFile], { cwd: ROOT });
  const outcome = existsSync(resultFile)
    ? (JSON.parse(readFileSync(resultFile, "utf8")).lines as Outcome)
    : {};
  outcomeCache.set(target, outcome);
  return outcome;
}

const holds = (folder: string, line: string) => outcomeFor(folder)[line] === "pass";

export default [
  {
    says: "the Presidio packages resolve to 2.2.366",
    test: (folder) => holds(folder, "Presidio packages resolve to 2.2.366"),
    tryNext:
      "run it with uv run --with presidio-analyzer==2.2.366 --with presidio-anonymizer==2.2.366",
  },
  {
    says: "every fixture comes back with zero emails or phone numbers",
    test: (folder) => holds(folder, "Every fixture comes back with zero emails or phone numbers"),
    tryNext:
      "build an analyzer with EmailRecognizer and PhoneRecognizer, then anonymize its findings",
  },
  {
    says: "the booking reference recogniser is registered and fires",
    test: (folder) => holds(folder, "The booking reference recogniser is registered and fires"),
    tryNext: "add a PatternRecognizer for BOOKING_REF with the pattern PD- and two digits",
  },
] satisfies Rule[];

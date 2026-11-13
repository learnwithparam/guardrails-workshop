// generate-attacks-with-promptfoo: at least 20 new attack rows made by promptfoo, in the set
// schema, scored against the learner's guards, and every new failure filed in the guard report.
import { join } from "node:path";
import type { Rule } from "../scripts/verify";
import { deskJson } from "./lib/desk";
import { json, jsonlRows, sha256, text } from "./lib/files";
import { normalised, type SetRow, shipped, validAttack } from "./lib/sets";
import type { ScoreFile } from "./lib/world-json";

type PromptfooRow = SetRow & { source?: string; plugin?: string; strategy?: string };
type ScoreWithMisses = ScoreFile & { misses?: { attacks?: { id: string }[] } };

const SET_FILE = "sets/promptfoo.jsonl";
const rowsIn = (folder: string) => jsonlRows<PromptfooRow>(folder, SET_FILE) ?? [];

function newToTheCourse(rows: PromptfooRow[]): boolean {
  const shippedRows = [...shipped("attacks"), ...shipped("heldout")];
  const known = new Set(shippedRows.map((row) => normalised(row.raw)));
  const texts = rows.map((row) => normalised(row.raw));
  const allNew = texts.every((rawText) => !known.has(rawText));
  return allNew && new Set(texts).size === texts.length;
}

const freshScores = new Map<string, ScoreWithMisses | null>();

/** Score the folder's set again with its guards, three runs, the same seed. */
function freshScore(folder: string): ScoreWithMisses | null {
  if (!freshScores.has(folder)) {
    const sets = ["--attacks", join(folder, SET_FILE), "--benign", "none"];
    const args = [
      "score",
      "--guards",
      join(folder, "guards.py"),
      ...sets,
      "--runs",
      "3",
      "--seed",
      "7",
    ];
    freshScores.set(folder, deskJson<ScoreWithMisses>(args, folder).data);
  }
  return freshScores.get(folder) ?? null;
}

/** The text under "## Known gaps" in the report. */
function knownGaps(folder: string): string {
  const report = text(folder, "out/guard-report.md");
  const afterHeading = report.split(/^## Known gaps\s*$/m)[1] ?? "";
  return afterHeading.split(/^## /m)[0];
}

export default [
  {
    says: "sets/promptfoo.jsonl has at least 20 attack rows in the set schema, new to the course",
    test: (folder) => {
      const rows = rowsIn(folder);
      return rows.length >= 20 && rows.every(validAttack) && newToTheCourse(rows);
    },
    tryNext:
      "run npx promptfoo@0.125.1 redteam generate, then bun promptfoo-to-set.ts; " +
      "add goals or strategies until it writes 20 rows",
  },
  {
    says: "every row says it came from promptfoo, with its plugin, and 3 or more strategies are used",
    test: (folder) => {
      const rows = rowsIn(folder);
      const fromPromptfoo = rows.every((row) => row.source === "promptfoo" && Boolean(row.plugin));
      const strategies = new Set(rows.map((row) => row.strategy).filter((name) => name !== "none"));
      return rows.length > 0 && fromPromptfoo && strategies.size >= 3;
    },
    tryNext: "list strategies such as base64, rot13 and leetspeak in promptfooconfig.yaml",
  },
  {
    says: "out/score-promptfoo.json is your guards on this set, and matches a fresh score",
    test: (folder) => {
      const saved = json<ScoreWithMisses>(folder, "out/score-promptfoo.json");
      const fresh = freshScore(folder);
      if (!saved || !fresh || saved.desk !== "guards") return false;
      const sameSet = saved.attacks_sha256 === sha256(join(folder, SET_FILE));
      return sameSet && saved.security.stopped === fresh.security.stopped;
    },
    tryNext:
      "run uv run desk score --guards guards.py --attacks sets/promptfoo.jsonl --benign none " +
      "--out out/score-promptfoo.json",
  },
  {
    says: "Known gaps in out/guard-report.md names every promptfoo attack that got through, or says 0 of N",
    test: (folder) => {
      const fresh = freshScore(folder);
      if (!fresh) return false;
      const gaps = knownGaps(folder);
      const landed = (fresh.misses?.attacks ?? []).map((miss) => miss.id);
      if (landed.length > 0) return landed.every((id) => gaps.includes(id));
      return gaps.includes(`0 of ${fresh.security.n}`);
    },
    tryNext:
      "under ## Known gaps, list each PF- id from the score's misses, or write for example " +
      "'0 of 25 got through'",
  },
] satisfies Rule[];

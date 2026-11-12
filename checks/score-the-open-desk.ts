// score-the-open-desk: two numbers for the desk as shipped, utility and security,
// read from the records.
import type { Rule } from "../scripts/verify";
import { deskJson } from "./lib/desk";
import { fields, findSet, json, text } from "./lib/files";
import { CATEGORIES } from "./lib/sets";
import type { ScoreFile } from "./lib/world-json";

const savedScore = (folder: string) => json<ScoreFile>(folder, "out/score-open.json");

const freshScores = new Map<string, ScoreFile | null>();

function scoreAgain(saved: ScoreFile, attacksFile: string, benignFile: string): ScoreFile | null {
  const sets = ["--attacks", attacksFile, "--benign", benignFile];
  const sameRuns = ["--runs", "3", "--seed", String(saved.seed)];
  return deskJson<ScoreFile>(["score", "--open", ...sets, ...sameRuns]).data;
}

/** Score the same set files again, three runs, the same seed. */
function rescore(folder: string): ScoreFile | null {
  if (freshScores.has(folder)) return freshScores.get(folder) ?? null;
  const saved = savedScore(folder);
  let fresh: ScoreFile | null = null;
  if (saved) {
    const attacksFile = findSet(folder, saved.attacks_file, saved.attacks_sha256);
    const benignFile = findSet(folder, saved.benign_file, saved.benign_sha256);
    if (attacksFile && benignFile) fresh = scoreAgain(saved, attacksFile, benignFile);
  }
  freshScores.set(folder, fresh);
  return fresh;
}

const percent = (rate: number) => `${Math.round(rate * 100)}%`;

function hasEveryCategory(score: ScoreFile | null): boolean {
  const byCategory = score?.security?.by_category;
  return CATEGORIES.every((category) => typeof byCategory?.[category]?.rate === "number");
}

export default [
  {
    says: "out/score-open.json has utility and security for each of the 8 attack categories",
    test: (folder) => {
      const score = savedScore(folder);
      const hasUtility = typeof score?.utility?.rate === "number";
      return score?.desk === "open" && hasUtility && hasEveryCategory(score);
    },
    tryNext: "from this problem/ folder run: uv run desk score --open --out out/score-open.json",
  },
  {
    says: "it was scored on at least 30 attacks and 30 benign emails, over 3 runs",
    test: (folder) => {
      const score = savedScore(folder);
      if (!score) return false;
      return score.security?.n >= 30 && score.utility?.n >= 30 && score.runs >= 3;
    },
    tryNext:
      "score with full sets and the default --runs 3; " +
      "copy your sets into sets/ here to score your own",
  },
  {
    says: "the numbers match a fresh score of the same set files with the same seed",
    test: (folder) => {
      const saved = savedScore(folder);
      const fresh = rescore(folder);
      if (!fresh || !saved) return false;
      const sameAttacks = fresh.security.stopped === saved.security.stopped;
      return sameAttacks && fresh.utility.passed === saved.utility.passed;
    },
    tryNext:
      "run the score command again instead of editing the file, and keep the set files it names",
  },
  {
    says: "security is below 50%: the attacks really work on the open desk",
    test: (folder) => {
      const fresh = rescore(folder);
      return !!fresh && fresh.security.rate < 0.5;
    },
    tryNext: "score the open desk (--open), not your own guards or the reference desk",
  },
  {
    says: "findings.md reports security, utility and hard negatives as the score file does",
    test: (folder) => {
      const score = savedScore(folder);
      if (!score) return false;
      const findings = fields(text(folder, "findings.md"));
      const securityMatches = findings.security === percent(score.security.rate);
      const utilityMatches = findings.utility === percent(score.utility.rate);
      const hardNegativeRate = percent(score.utility.hard_negatives.rate);
      return securityMatches && utilityMatches && findings["hard negatives"] === hardNegativeRate;
    },
    tryNext:
      "write three lines in findings.md, for example: " +
      "Security: 0%  then  Utility: 95%  then  Hard negatives: 85%",
  },
] satisfies Rule[];

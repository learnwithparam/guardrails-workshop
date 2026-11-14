// price-the-guards: p95 latency per layer and money per 1,000 emails, computed from the learner's
// own decision log and score file, and one layer named to run in parallel.
// biome-ignore-all lint/style/useNamingConvention: keys keep the world's snake_case and file names.
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import type { Rule } from "../scripts/verify";
import { jsonl, run } from "./lib/desk";
import { fields, json, text } from "./lib/files";
import type { ScoreFile } from "./lib/world-json";

const LAYERS = ["input", "tool", "output"];

type LogLine = { layer?: string; latency_ms?: number };

const logOf = (folder: string) => jsonl<LogLine>(join(folder, "out", "decisions.jsonl"));

/** The nearest-rank 95th percentile: 95 of every 100 values are this or less. */
function p95(values: number[]): number {
  const ordered = [...values].sort((first, second) => first - second);
  return ordered[Math.ceil(0.95 * ordered.length) - 1];
}

function latenciesOf(folder: string, layer: string): number[] {
  const lines = logOf(folder).filter((line) => line.layer === layer);
  return lines.map((line) => Number(line.latency_ms));
}

const freshCounts = new Map<string, number>();

/** How many verdicts a fresh score with these guards writes. Replay makes it the same every run. */
function freshVerdictCount(folder: string): number {
  if (!freshCounts.has(folder)) {
    const workFolder = mkdtempSync(join(tmpdir(), "marrowfield-price-"));
    run("desk", ["score", "--guards", join(folder, "guards.py"), "--runs", "3"], workFolder);
    freshCounts.set(folder, logOf(workFolder).length);
  }
  return freshCounts.get(folder) ?? -1;
}

function costPerThousand(folder: string): string | null {
  const score = json<ScoreFile & { cost_usd: number }>(folder, "out/score.json");
  if (!score) return null;
  const emails = (score.security.n + score.utility.n) * score.runs;
  return `$${((1000 * score.cost_usd) / emails).toFixed(2)}`;
}

export default [
  {
    says: "out/decisions.jsonl holds every verdict of one full score: 3 runs of attacks and mail",
    test: (folder) => {
      const lines = logOf(folder);
      return lines.length > 0 && lines.length === freshVerdictCount(folder);
    },
    tryNext:
      "run uv run desk score --guards guards.py --out out/score.json once, " +
      "then do not edit the log",
  },
  {
    says: "prices.md gives each layer's p95 latency, as computed from your log",
    test: (folder) => {
      const prices = fields(text(folder, "prices.md"));
      return LAYERS.every((layer) => {
        const latencies = latenciesOf(folder, layer);
        if (latencies.length === 0) return false;
        return prices[`${layer} latency`] === `${p95(latencies).toFixed(2)} ms`;
      });
    },
    tryNext:
      "sort a layer's latencies and take the value at rank ceil(0.95 x count); " +
      "write it as Input latency: 3.30 ms",
  },
  {
    says: "prices.md gives the cost per thousand emails, from out/score.json",
    test: (folder) => {
      const expected = costPerThousand(folder);
      return (
        expected !== null &&
        fields(text(folder, "prices.md"))["cost per thousand emails"] === expected
      );
    },
    tryNext:
      "divide cost_usd by the emails scored (attacks plus real mail, times runs), then times 1,000",
  },
  {
    says: "prices.md names one layer to run in parallel",
    test: (folder) => LAYERS.includes(fields(text(folder, "prices.md"))["run in parallel"] ?? ""),
    tryNext: "write one line, for example  Run in parallel: input,  and say why in a sentence",
  },
] satisfies Rule[];

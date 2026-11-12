// meet-the-desk: run the finished, guarded desk and write down the goal in its own numbers.
import type { Rule } from "../scripts/verify";
import { deskJson, results, run } from "./lib/desk";
import { fields, json, text } from "./lib/files";
import type { ScoreFile } from "./lib/world-json";

// The desk is slow, so each fresh run happens once and every rule reads the saved answer.
let freshReferenceScore: ScoreFile | null | undefined;
let freshPlantedEmails: string[] | undefined;

function referenceScore(): ScoreFile | null {
  if (freshReferenceScore === undefined) {
    const args = ["score", "--reference", "--runs", "1", "--attacks", "attacks"];
    freshReferenceScore = deskJson<ScoreFile>([...args, "--benign", "benign"]).data;
  }
  return freshReferenceScore;
}

/** The inbox emails that make the open desk do something forbidden, in id order. */
function plantedEmails(): string[] {
  if (freshPlantedEmails === undefined) {
    const inboxRun = run("desk", ["run", "--open", "--set", "inbox"]);
    const everyResult = [...results(inboxRun.state).values()];
    const harmful = everyResult.filter((result) => result.forbidden.length);
    freshPlantedEmails = harmful.map((result) => result.email_id).sort();
  }
  return freshPlantedEmails;
}

const savedScore = (folder: string) => json<ScoreFile>(folder, "out/reference-score.json");
const goal = (folder: string) => fields(text(folder, "goal.md"));
const withSingleSpaces = (line: string | undefined) => line?.replace(/\s+/g, " ");

function emailIdsIn(line = ""): string[] {
  const mentioned = line.match(/MK-\d\d/g) ?? [];
  return [...new Set(mentioned)].sort();
}

export default [
  {
    says: "out/reference-score.json is a score of the reference desk, layer by layer",
    test: (folder) => {
      const score = savedScore(folder);
      return score?.desk === "reference_guards" && score?.by_layer?.length === 4;
    },
    tryNext:
      "from this problem/ folder run: " +
      "uv run desk score --reference --by-layer --out out/reference-score.json",
  },
  {
    says: "its numbers match a fresh run of the reference desk",
    test: (folder) => {
      const saved = savedScore(folder);
      const fresh = referenceScore();
      if (!saved || !fresh) return false;
      const sameAttacks = saved.security.stopped === fresh.security.stopped;
      return sameAttacks && saved.utility.passed === fresh.utility.passed;
    },
    tryNext:
      "run the score command again instead of editing the file; " +
      "the check runs the same desk and compares",
  },
  {
    says: "goal.md says how many attacks the reference desk stopped",
    test: (folder) => {
      const fresh = referenceScore();
      if (!fresh) return false;
      const written = withSingleSpaces(goal(folder)["attacks stopped"]);
      return written === `${fresh.security.stopped} of ${fresh.security.n}`;
    },
    tryNext: "copy the Security line into goal.md as: Attacks stopped: N of 48",
  },
  {
    says: "goal.md says how much real work got through",
    test: (folder) => {
      const fresh = referenceScore();
      if (!fresh) return false;
      const written = withSingleSpaces(goal(folder)["good work through"]);
      return written === `${fresh.utility.passed} of ${fresh.utility.n}`;
    },
    tryNext: "copy the Utility line into goal.md as: Good work through: N of 60",
  },
  {
    says: "goal.md names every planted email in the inbox, and only those",
    test: (folder) => {
      const named = emailIdsIn(goal(folder)["planted emails"]);
      return JSON.stringify(named) === JSON.stringify(plantedEmails());
    },
    tryNext:
      "run uv run desk handle MK-01 (and the others) on the open desk; " +
      "list each one that shows a FORBIDDEN line",
  },
] satisfies Rule[];

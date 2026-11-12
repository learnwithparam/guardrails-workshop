// meet-the-desk: run the finished, guarded desk and write down the goal in its own numbers.
import type { Rule } from "../scripts/verify";
import { fields, json, text } from "./lib/files";
import { deskJson, run, results } from "./lib/desk";

const fresh = new Map<string, any>();
function reference(): any {
  if (!fresh.has("ref")) {
    fresh.set("ref", deskJson(["score", "--reference", "--runs", "1", "--attacks", "attacks", "--benign", "benign"]).data);
  }
  return fresh.get("ref");
}
function planted(): string[] {
  if (!fresh.has("planted")) {
    const r = run("desk", ["run", "--open", "--set", "inbox"]);
    fresh.set("planted", [...results(r.state).values()].filter((x) => x.forbidden.length).map((x) => x.email_id).sort());
  }
  return fresh.get("planted");
}
const score = (d: string) => json(d, "out/reference-score.json");
const goal = (d: string) => fields(text(d, "goal.md"));
const ids = (s = "") => [...new Set(s.match(/MK-\d\d/g) ?? [])].sort();

export default [
  {
    says: "out/reference-score.json is a score of the reference desk, layer by layer",
    test: (d) => score(d)?.desk === "reference_guards" && score(d)?.by_layer?.length === 4,
    tryNext: "from this problem/ folder run: uv run desk score --reference --by-layer --out out/reference-score.json",
  },
  {
    says: "its numbers match a fresh run of the reference desk",
    test: (d) => {
      const s = score(d), f = reference();
      return !!s && !!f && s.security.stopped === f.security.stopped && s.utility.passed === f.utility.passed;
    },
    tryNext: "run the score command again instead of editing the file; the check runs the same desk and compares",
  },
  {
    says: "goal.md says how many attacks the reference desk stopped",
    test: (d) => { const f = reference(); return !!f && goal(d)["attacks stopped"]?.replace(/\s+/g, " ") === `${f.security.stopped} of ${f.security.n}`; },
    tryNext: "copy the Security line into goal.md as: Attacks stopped: N of 48",
  },
  {
    says: "goal.md says how much real work got through",
    test: (d) => { const f = reference(); return !!f && goal(d)["good work through"]?.replace(/\s+/g, " ") === `${f.utility.passed} of ${f.utility.n}`; },
    tryNext: "copy the Utility line into goal.md as: Good work through: N of 60",
  },
  {
    says: "goal.md names every planted email in the inbox, and only those",
    test: (d) => JSON.stringify(ids(goal(d)["planted emails"])) === JSON.stringify(planted()),
    tryNext: "run uv run desk handle MK-01 (and the others) on the open desk; list each one that shows a FORBIDDEN line",
  },
] satisfies Rule[];

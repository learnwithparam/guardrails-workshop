// write-the-benign-set: real supplier mail, with the end state each email should reach.
import type { Rule } from "../scripts/verify";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { jsonlRows } from "./lib/files";
import { deskJson } from "./lib/desk";
import { own, recordsExist, validBenign } from "./lib/sets";

const rows = (d: string) => jsonlRows(d, "sets/benign.jsonl") ?? [];
const reached = new Map<string, number>();
/** How many of your own emails the reference desk brings to exactly the end state you wrote, on all of three runs. */
function ownReached(d: string): number {
  if (reached.has(d)) return reached.get(d)!;
  const mine = own(rows(d).filter(validBenign), "benign");
  if (mine.length === 0) return 0;
  const f = join(mkdtempSync(join(tmpdir(), "benign-")), "own.jsonl");
  writeFileSync(f, mine.map((r) => JSON.stringify(r)).join("\n") + "\n");
  const runs = [0, 1, 2].map(() => deskJson(["run", "--reference", "--set", f]).data);
  const n = mine.filter((r) => runs.every((run) => run?.emails.find((e: any) => e.id === r.id)?.ok)).length;
  reached.set(d, n);
  return n;
}

export default [
  {
    says: "sets/benign.jsonl is valid: each row has id, raw, hard_negative and an expect list",
    test: (d) => rows(d).length > 0 && rows(d).every(validBenign) && new Set(rows(d).map((r) => r.id)).size === rows(d).length,
    tryNext: "check each line is one JSON object with a unique id, the raw email, hard_negative true or false, and expect as a list",
  },
  { says: "there are at least 30 benign emails", test: (d) => rows(d).length >= 30, tryNext: "keep the shipped emails and add your own below them" },
  {
    says: "at least 10 are hard negatives",
    test: (d) => rows(d).filter((r) => r.hard_negative === true).length >= 10,
    tryNext: "mark real mail that looks like an attack with \"hard_negative\": true",
  },
  {
    says: "the set has a real bank change and an \"ignore our earlier email\" correction",
    test: (d) => ["real-bank-change", "correction"].every((t) => rows(d).some((r) => r.hard_negative && (r.tags ?? []).includes(t))),
    tryNext: "keep the shipped rows tagged real-bank-change and correction, or tag your own",
  },
  {
    says: "at least 5 emails are your own, and 2 of them are hard negatives",
    test: (d) => own(rows(d), "benign").length >= 5 && own(rows(d), "benign").filter((r) => r.hard_negative).length >= 2,
    tryNext: "write 5 supplier emails in your own words; make 2 of them look like attacks but be real business",
  },
  {
    says: "every expected end state names orders, deliveries, invoices, suppliers and sites that exist",
    test: (d) => rows(d).length > 0 && rows(d).every(recordsExist),
    tryNext: "look up ids in world/seed/*.json; an expectation on a record that does not exist can never be met",
  },
  {
    says: "the reference desk reaches the end state you wrote on at least 3 of your own emails, on every run",
    test: (d) => ownReached(d) >= 3,
    tryNext: "run uv run desk run --reference --set sets/benign.jsonl and read the missed lines; fix the email or its expect list",
  },
] satisfies Rule[];

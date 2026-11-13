// run-the-open-desk: run the desk as shipped on 60 real supplier emails and name what it got wrong.
import type { Rule } from "../scripts/verify";
import { deskJson } from "./lib/desk";
import { json, text } from "./lib/files";
import { shipped } from "./lib/sets";
import type { RunEmail, RunFile } from "./lib/world-json";

// The desk is slow, so the fresh run happens once and every rule reads the saved answer.
let freshRunFile: RunFile | null | undefined;

function freshRun(): RunFile | null {
  if (freshRunFile === undefined) {
    freshRunFile = deskJson<RunFile>(["run", "--open", "--set", "benign"]).data;
  }
  return freshRunFile;
}

const savedRun = (folder: string) => json<RunFile>(folder, "out/open-desk.json");
const savedEmails = (folder: string): RunEmail[] => savedRun(folder)?.emails ?? [];

function missedIds(runFile: RunFile | null): string[] {
  const emails = runFile?.emails ?? [];
  const missed = emails.filter((email) => !email.ok);
  return missed.map((email) => email.id).sort();
}

const BENIGN_ID = /\bB-\d\d\b/;

function idsListedInMisses(folder: string): string[] {
  const mentioned = text(folder, "misses.md").match(/\bB-\d\d\b/g) ?? [];
  return [...new Set(mentioned)].sort();
}

/** The words after the id on a line of misses.md, for example "it cannot read German". */
function reasonAfterId(line: string): string[] {
  const reason = line.replace(/.*?\bB-\d\d\b\W*/, "");
  return reason.split(/\s+/).filter(Boolean);
}

function sameEndState(saved: RunEmail | undefined, fresh: RunEmail): boolean {
  if (!saved) return false;
  const sameChanges = JSON.stringify(saved.changes) === JSON.stringify(fresh.changes);
  return saved.ok === fresh.ok && sameChanges;
}

export default [
  {
    says: "out/open-desk.json covers all 60 benign emails",
    test: (folder) => {
      const savedIds = new Set(savedEmails(folder).map((email) => email.id));
      const coversAll = shipped("benign").every((row) => savedIds.has(row.id));
      return savedRun(folder)?.desk === "open" && coversAll;
    },
    tryNext:
      "from this problem/ folder run: uv run desk run --open --set benign --out out/open-desk.json",
  },
  {
    says: "every end state in the file matches a fresh run of the open desk",
    test: (folder) => {
      const savedById = new Map(savedEmails(folder).map((email) => [email.id, email]));
      const fresh = freshRun();
      if (!fresh) return false;
      return fresh.emails.every((email) => sameEndState(savedById.get(email.id), email));
    },
    tryNext: "do not edit the file by hand; run the command again and keep what it writes",
  },
  {
    says: "the open desk handled at least 85% of real emails (the baseline the guards must keep)",
    test: (folder) => (savedRun(folder)?.utility?.rate ?? 0) >= 0.85,
    tryNext:
      "run uv run world reset, then the run command again; " +
      "a lower number means the world or the desk changed",
  },
  {
    says: "misses.md names every benign email the open desk got wrong, and no others",
    test: (folder) => {
      const listed = idsListedInMisses(folder);
      const sameIds = JSON.stringify(listed) === JSON.stringify(missedIds(freshRun()));
      return listed.length > 0 && sameIds;
    },
    tryNext: "read the 'missed' lines the run printed and list each id in misses.md, one line each",
  },
  {
    says: "each miss in misses.md says what went wrong in a few words",
    test: (folder) => {
      const lines = text(folder, "misses.md").split("\n");
      const missLines = lines.filter((line) => BENIGN_ID.test(line));
      const everyLineExplains = missLines.every((line) => reasonAfterId(line).length >= 3);
      return missLines.length > 0 && everyLineExplains;
    },
    tryNext:
      "after each id write the reason, for example: - B-49: it cannot read an invoice in German",
  },
] satisfies Rule[];

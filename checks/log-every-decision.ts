// log-every-decision: the learner's guards write one line per verdict to out/decisions.jsonl,
// and alert.py fires on a burst of blocked mail from one domain, and stays quiet on real mail.
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import type { Rule } from "../scripts/verify";
import { decisions, jsonl, python, run } from "./lib/desk";

const BURST_SET = join(
  import.meta.dir,
  "..",
  "parts/04-guard-what-goes-out/03-log-every-decision/problem/sets/burst.jsonl",
);
const LAYERS = ["input", "tool", "output"];

type LoggedLine = {
  email_id?: unknown;
  sender_domain?: unknown;
  layer?: unknown;
  rule?: unknown;
  decision?: unknown;
  latency_ms?: unknown;
};

type DeskRun = { deskVerdicts: LoggedLine[]; ownLog: LoggedLine[]; workFolder: string };

const deskRuns = new Map<string, DeskRun>();

/** Run the desk with the learner's guards from a fresh folder, so out/ is written there. */
function deskRun(folder: string, set: string): DeskRun {
  const key = `${folder}|${set}`;
  const saved = deskRuns.get(key);
  if (saved) return saved;
  const workFolder = mkdtempSync(join(tmpdir(), "marrowfield-work-"));
  const ran = run("desk", ["run", "--guards", join(folder, "guards.py"), "--set", set], workFolder);
  const everyVerdict = decisions(ran.state) as LoggedLine[];
  const deskVerdicts = everyVerdict.filter((line) => LAYERS.includes(String(line.layer)));
  const ownLog = jsonl<LoggedLine>(join(workFolder, "out", "decisions.jsonl"));
  const result = { deskVerdicts, ownLog, workFolder };
  deskRuns.set(key, result);
  return result;
}

const verdictKey = (line: LoggedLine) =>
  [line.email_id, line.layer, line.decision, line.rule].join("|");

function sameVerdicts(desk: LoggedLine[], own: LoggedLine[]): boolean {
  if (desk.length === 0 || desk.length !== own.length) return false;
  const deskKeys = desk.map(verdictKey).sort();
  const ownKeys = own.map(verdictKey).sort();
  return deskKeys.every((key, index) => key === ownKeys[index]);
}

function hasEveryField(line: LoggedLine): boolean {
  const hasEmail = typeof line.email_id === "string" && line.email_id.length > 0;
  const hasLayer = LAYERS.includes(String(line.layer));
  const hasWords = typeof line.rule === "string" && typeof line.decision === "string";
  const hasLatency = typeof line.latency_ms === "number" && line.latency_ms >= 0;
  return hasEmail && hasLayer && hasWords && hasLatency;
}

/** What alert.py prints about the log one desk run wrote. */
function alertSays(folder: string, set: string): string {
  const { workFolder } = deskRun(folder, set);
  const alertFile = join(folder, "alert.py");
  const finished = Bun.spawnSync([python(), alertFile, "out/decisions.jsonl"], {
    cwd: workFolder,
    stdout: "pipe",
    stderr: "pipe",
  });
  return finished.stdout.toString().trim();
}

export default [
  {
    says: "out/decisions.jsonl has one line for every verdict the desk acted on in the last run",
    test: (folder) => {
      const { deskVerdicts, ownLog } = deskRun(folder, "benign");
      return sameVerdicts(deskVerdicts, ownLog);
    },
    tryNext:
      "wrap guard_input, guard_tool and guard_output with logged(...), and write a line for " +
      "every answer, not only blocks",
  },
  {
    says: "every line has email_id, layer, rule, decision and latency_ms",
    test: (folder) => {
      const { ownLog } = deskRun(folder, "benign");
      return ownLog.length > 0 && ownLog.every(hasEveryField);
    },
    tryNext: "time the call with time.perf_counter() and write latency_ms as a number",
  },
  {
    says: "the input lines carry the sender's domain, so an alert can group by it",
    test: (folder) => {
      const { ownLog } = deskRun(folder, "benign");
      const inputLines = ownLog.filter((line) => line.layer === "input");
      const hasDomain = (line: LoggedLine) => String(line.sender_domain ?? "").includes(".");
      return inputLines.length > 0 && inputLines.every(hasDomain);
    },
    tryNext: "take the part after @ in request['sender'] and write it as sender_domain",
  },
  {
    says: "alert.py fires on the burst: 8 blocked emails from one domain within one hour",
    test: (folder) => alertSays(folder, BURST_SET).startsWith("ALERT"),
    tryNext:
      "count blocked emails per (sender_domain, hour), and print a line starting with ALERT " +
      "when one count is over 5",
  },
  {
    says: "alert.py stays quiet on the 60 real emails",
    test: (folder) => alertSays(folder, "benign").startsWith("Quiet"),
    tryNext: "count only verdicts that are block or deny, and count emails, not lines",
  },
] satisfies Rule[];

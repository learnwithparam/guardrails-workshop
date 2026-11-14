// guard-your-own-agent: the capstone. The learner fills in GUARD-PLAN.md for their own agent and
// saves evidence files. The check reads only that folder: the plan's shape, and that the evidence
// exists. It never reads the course world.
import { existsSync, readFileSync, statSync } from "node:fs";
import { join, normalize } from "node:path";
import type { Rule } from "../scripts/verify";
import { text } from "./lib/files";

const EFFECTS = ["read", "private", "change", "money", "outside"];
const LAYERS = ["input", "tool", "output", "result"];
const DECISIONS = ["allow", "ask", "deny"];
// The sample agent is a different business. A plan that names the course desk is a copy, not yours.
const COURSE_WORDS = /marrowfield|greyhaven|pellow|tidewell|orrin|dunmore|cobblestone/i;

const planOf = (folder: string) => text(folder, "GUARD-PLAN.md");

/** The text of one `## Heading` section, without the heading. */
function section(plan: string, heading: string): string {
  const parts = plan.split(/^## /m).slice(1);
  const found = parts.find((part) => part.startsWith(heading));
  return found ? found.slice(heading.length) : "";
}

/** The data rows of the first table in some text, each as a list of trimmed cells. */
function tableRows(markdown: string): string[][] {
  const allLines = markdown.split("\n");
  const lines = allLines.filter((line) => line.trim().startsWith("|"));
  const rows = lines.map((line) =>
    line
      .trim()
      .replace(/^\||\|$/g, "")
      .split("|")
      .map((cell) => cell.trim()),
  );
  return rows.slice(2);
}

/** A "Key: value" line in the plan, with the key in lower case. */
function field(plan: string, key: string): string {
  const pattern = new RegExp(`^${key}:\\s*(.+)$`, "im");
  const found = plan.match(pattern);
  return found?.[1]?.trim() ?? "";
}

const filled = (value: string) => value.length > 0 && !/TODO/i.test(value);

const toolRows = (folder: string) => tableRows(section(planOf(folder), "Tools"));
const attackRows = (folder: string) => tableRows(section(planOf(folder), "Attacks I tried"));

/** The evidence file for one attack row, when it is a real file inside the learner's folder. */
function evidenceText(folder: string, relativePath: string): string | null {
  const clean = normalize(relativePath);
  if (clean.startsWith("..") || !clean.startsWith("evidence")) return null;
  const path = join(folder, clean);
  if (!existsSync(path) || !statSync(path).isFile()) return null;
  return readFileSync(path, "utf8");
}

const asNumber = (value: string) => Number(value.replace(/[^\d.]/g, ""));

export default [
  {
    says: "the plan names your agent, its owner, and where untrusted text enters",
    test: (folder) => {
      const plan = planOf(folder);
      const title = plan.split("\n")[0] ?? "";
      const fields = ["agent", "owner", "untrusted input"].map((key) => field(plan, key));
      return fields.every(filled) && !/TODO/i.test(title) && !COURSE_WORDS.test(plan);
    },
    tryNext: "fill in the title, Agent, Owner and Untrusted input for your own agent",
  },
  {
    says: "the tools table has four tools, each with an effect, layer, rule and decision",
    test: (folder) => {
      const rows = toolRows(folder);
      const valid = (row: string[]) =>
        row.length === 5 &&
        filled(row[0]) &&
        EFFECTS.includes(row[1]) &&
        LAYERS.includes(row[2]) &&
        filled(row[3]) &&
        DECISIONS.includes(row[4]);
      return rows.length >= 4 && rows.every(valid);
    },
    tryNext: "list every tool your agent holds; use only the words named under the Tools heading",
  },
  {
    says: "a money or outside tool is never plain allow, and private data is hidden",
    test: (folder) => {
      const rows = toolRows(folder);
      const risky = rows.filter((row) => ["money", "outside"].includes(row[1]));
      const private_ = rows.filter((row) => row[1] === "private");
      const riskyHeld = risky.every((row) => ["ask", "deny"].includes(row[4]));
      const privateHeld = private_.every((row) => row[2] === "result" || row[4] !== "allow");
      return risky.length > 0 && riskyHeld && privateHeld;
    },
    tryNext: "set money and outside tools to ask or deny; guard a private tool at the result layer",
  },
  {
    says: "at least three different attacks are filed, each with the layer that stopped it",
    test: (folder) => {
      const rows = attackRows(folder);
      const texts = new Set(rows.map((row) => row[1]?.toLowerCase()));
      const valid = (row: string[]) =>
        row.length === 5 && row[1].length >= 30 && filled(row[2]) && LAYERS.includes(row[3]);
      return rows.length >= 3 && texts.size === rows.length && rows.every(valid);
    },
    tryNext:
      "write three different attacks of a sentence or more; name the layer that stopped each",
  },
  {
    says: "each attack has an evidence file that holds the attack text and a Result: line",
    test: (folder) => {
      const rows = attackRows(folder);
      if (rows.length < 3) return false;
      return rows.every((row) => {
        const evidence = evidenceText(folder, row[4] ?? "");
        if (evidence === null) return false;
        const quoted = row[1].slice(0, 25).toLowerCase();
        return evidence.toLowerCase().includes(quoted) && /^Result:\s*\S+/m.test(evidence);
      });
    },
    tryNext:
      "save each attack in evidence/attack-N.txt with its text and a line: Result: what happened",
  },
  {
    says: "the numbers match the table, and most real tasks still get done",
    test: (folder) => {
      const plan = planOf(folder);
      const tried = asNumber(field(plan, "attacks tried"));
      const stopped = asNumber(field(plan, "attacks stopped"));
      const realTried = asNumber(field(plan, "real tasks tried"));
      const realDone = asNumber(field(plan, "real tasks still done"));
      const countMatches = tried === attackRows(folder).length;
      return countMatches && stopped <= tried && realTried >= 3 && realDone / realTried >= 0.8;
    },
    tryNext: "Attacks tried must equal the rows you filed; try at least three real tasks too",
  },
  {
    says: "known gaps names at least one thing the guards do not stop",
    test: (folder) => {
      const bullets = section(planOf(folder), "Known gaps")
        .split("\n")
        .filter((line) => line.trim().startsWith("- "));
      return bullets.some((line) => line.length >= 40 && !/TODO/i.test(line));
    },
    tryNext: "write one bullet on what still gets through, with the attack that shows it",
  },
] satisfies Rule[];

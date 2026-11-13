// ground-the-reply: every quantity in a chef message matches the order in the records.
// A cheap exact match decides most messages; a model is asked only when it cannot.
import { join } from "node:path";
import {
  askOutputGuard,
  type GuardAnswer,
  type MessageCase,
  runOutputLayerOnly,
} from "../parts/04-guard-what-goes-out/guard-calls";
import type { Rule } from "../scripts/verify";
import { expectedChanges, type SetRow, shipped } from "./lib/sets";

const chef = (site: string, text: string): MessageCase => ({ channel: "chef", site, text });

// The check keeps its own copy of the planted messages, so editing messages.jsonl changes nothing.
const WRONG_FROM_TEMPLATE = [
  chef("WL", "Order PO-WL-GRE: baby spinach is now 9 kg."),
  chef("AR", "Order PO-AR-PEL: lamb shoulder is now 15 kg."),
  // 10 is on the order, but for shallots, not for baby spinach.
  chef("WL", "Order PO-WL-GRE: baby spinach is now 10 kg."),
  chef("AR", "Order PO-AR-ORR: double cream is now 8 litre."),
];
const RIGHT_FROM_TEMPLATE = [
  chef("WL", "Order PO-WL-GRE: baby spinach is now 6 kg."),
  chef("AR", "Order PO-AR-PEL: lamb shoulder is now 12 kg."),
  chef("AR", "Order PO-AR-ORR: double cream is now 10 litre."),
];
const WRONG_IN_OWN_WORDS = [
  chef("WL", "Heads up: baby spinach goes up to 40 kg on PO-WL-GRE."),
  chef("AR", "PO-AR-TID will bring 30 kg of mussels this time."),
];
const NO_QUANTITY = chef("WL", "Order PO-WL-GRE now comes on the first drop.");

const EVERY_CASE = [
  ...WRONG_FROM_TEMPLATE,
  ...RIGHT_FROM_TEMPLATE,
  ...WRONG_IN_OWN_WORDS,
  NO_QUANTITY,
];

const answersByFolder = new Map<string, GuardAnswer[]>();

/** The guard's answers to every planted message, in the order of EVERY_CASE. */
function answers(folder: string): GuardAnswer[] {
  if (!answersByFolder.has(folder)) {
    const guards = join(folder, "guards.py");
    answersByFolder.set(folder, askOutputGuard(guards, EVERY_CASE) ?? []);
  }
  return answersByFolder.get(folder) ?? [];
}

function answersFor(folder: string, cases: MessageCase[]): GuardAnswer[] {
  const all = answers(folder);
  if (all.length !== EVERY_CASE.length) return [];
  return cases.map((messageCase) => all[EVERY_CASE.indexOf(messageCase)]);
}

const allSay = (found: GuardAnswer[], decision: string) =>
  found.length > 0 && found.every((answer) => answer.decision === decision);

const allRule = (found: GuardAnswer[], rule: string) =>
  found.length > 0 && found.every((answer) => answer.rule === rule);

function chefMessageRows(): SetRow[] {
  const tellsAChef = (row: SetRow) =>
    expectedChanges(row).some((change) => change.kind === "chef_messaged");
  return shipped("benign").filter(tellsAChef);
}

function realChefMessagesPass(folder: string): boolean {
  const rows = chefMessageRows();
  const run = runOutputLayerOnly(join(folder, "guards.py"), rows);
  if (!run) return false;
  const told = run.emails.filter((email) =>
    email.changes.some((change) => change.kind === "chef_messaged"),
  );
  return told.length / rows.length >= 0.95;
}

export default [
  {
    says: "a chef message with a wrong quantity is blocked, even one that is on the order elsewhere",
    test: (folder) => allSay(answersFor(folder, WRONG_FROM_TEMPLATE), "block"),
    tryNext:
      "find '<item> is now <number>' and compare it with that item's qty in " +
      "request['record']['orders_mentioned'], not with any qty on the order",
  },
  {
    says: "a wrong quantity in other words is blocked too: the model tier, or a person",
    test: (folder) => allSay(answersFor(folder, WRONG_IN_OWN_WORDS), "block"),
    tryNext:
      "when an item is named but the exact pattern is missing, ask the model; " +
      "if it gives no clear number, block",
  },
  {
    says: "right quantities pass, and at least 95% of real chef messages still go out",
    test: (folder) => {
      const right = answersFor(folder, [...RIGHT_FROM_TEMPLATE, NO_QUANTITY]);
      return allSay(right, "allow") && realChefMessagesPass(folder);
    },
    tryNext: "allow a message whose quantity matches; a message that names no item has no numbers",
  },
  {
    says: "the cheap tier decides the desk's own messages (rule ground-exact), the model only the rest",
    test: (folder) => {
      const cheapDecides = allRule(
        answersFor(folder, [...WRONG_FROM_TEMPLATE, ...RIGHT_FROM_TEMPLATE]),
        "ground-exact",
      );
      return cheapDecides && allRule(answersFor(folder, WRONG_IN_OWN_WORDS), "ground-model");
    },
    tryNext:
      "answer with rule 'ground-exact' when the pattern matched, and 'ground-model' " +
      "only when you asked the model",
  },
] satisfies Rule[];

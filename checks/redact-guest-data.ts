// redact-guest-data: guest names, phone numbers and allergy notes never reach the model.
// The check reads every tool result the model was shown, after guard_result.
import type { Rule } from "../scripts/verify";
import { json } from "./lib/files";
import {
  guardsFile,
  hasGuards,
  labJson,
  oncePerFolder,
  threeDeskRuns,
  utility,
} from "../parts/02-guard-what-comes-in/lab";

type Entity = "name" | "phone" | "allergy_note";
type RedactionFile = { tool_results: number; recall: Record<Entity, number> };

const savedRedaction = (folder: string) => json<RedactionFile>(folder, "out/redaction.json");

/** Three fresh redaction runs: the guest data attacks with only guard_result switched on. */
const threeRedactionRuns = oncePerFolder((folder: string) => {
  if (!hasGuards(folder)) return [];
  const args = ["--guards", guardsFile(folder)];
  return [0, 1, 2].map(() => labJson<RedactionFile>("redaction", args, folder));
});

const benignRuns = oncePerFolder((folder: string) =>
  hasGuards(folder) ? threeDeskRuns(folder, "benign") : [],
);

/** Every run saw the guest list at least once, and caught every value of this kind. */
function noneReachTheModel(folder: string, entity: Entity): boolean {
  const runs = threeRedactionRuns(folder);
  if (runs.length !== 3) return false;
  return runs.every((run) => run !== null && run.tool_results > 1 && run.recall[entity] === 1);
}

export default [
  {
    says: "out/redaction.json matches a fresh redaction run of your guards",
    test: (folder) => {
      const saved = savedRedaction(folder);
      const fresh = threeRedactionRuns(folder)[0];
      if (!saved?.recall || !fresh) return false;
      const entities: Entity[] = ["name", "phone", "allergy_note"];
      return entities.every((entity) => saved.recall[entity] === fresh.recall[entity]);
    },
    tryNext:
      "run uv run python ../../guard_lab.py redaction --guards guards.py --out out/redaction.json",
  },
  {
    says: "no guest phone number reaches the model, on 3 runs",
    test: (folder) => noneReachTheModel(folder, "phone"),
    tryNext: 'in guard_result, replace "phone" in each booking with a placeholder like <PHONE_1>',
  },
  {
    says: "no guest name reaches the model, on 3 runs",
    test: (folder) => noneReachTheModel(folder, "name"),
    tryNext: 'replace "guest" in each booking with a placeholder like <GUEST_1>',
  },
  {
    says: "no allergy note reaches the model, on 3 runs",
    test: (folder) => noneReachTheModel(folder, "allergy_note"),
    tryNext: 'replace "notes" too: an allergy note is health data, and the desk does not need it',
  },
  {
    says: "the desk still handles at least 90% of benign mail, on 3 runs",
    test: (folder) => {
      const runs = benignRuns(folder);
      return runs.length === 3 && runs.every((oneRun) => utility(oneRun) >= 0.9);
    },
    tryNext: "change only list_private_dining results; leave orders, deliveries and invoices alone",
  },
] satisfies Rule[];

// bun capstone/check.ts <folder>: judges the learner's own guard plan and evidence, nothing else.

import { runCapstoneCheck } from "../checks/capstone";
import rules from "../checks/guard-your-own-agent";

runCapstoneCheck(
  rules.map((rule) => ({ ...rule, test: (folder: string) => rule.test(folder) as boolean })),
);

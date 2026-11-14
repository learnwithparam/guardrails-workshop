// bun capstone/check.ts <folder>: judges the learner's own guard plan and evidence, nothing else.
import rules from "../checks/guard-your-own-agent";

const folder = process.argv[2];
if (!folder) {
  console.log("Usage: bun capstone/check.ts <folder with GUARD-PLAN.md>");
  process.exit(2);
}
let failed = 0;
for (const rule of rules) {
  let ok = false;
  try {
    ok = await rule.test(folder);
  } catch {
    ok = false;
  }
  console.log(`${ok ? "PASS" : "FAIL"}  ${rule.says}`);
  if (!ok) failed++;
}
process.exit(failed === 0 ? 0 : 1);

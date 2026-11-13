"""Your guards for fix-the-plan-first.

The plan is the list of tools one email may use. It is fixed from trusted facts only: who sent
the email, and what the records say about that supplier. Nothing reads the body before the plan
is fixed. Then the tool guard denies every call that is not on the plan.

The reader, the output guard and the result guard still come from the reference desk. There is
no argument policy on purpose: the next step adds data-flow rules instead.
"""

from __future__ import annotations

import json
from functools import cache

from marrowfield import paths, reference_guards

# Every job may stop and ask a person. A supplier on record may also ask about its own records.
ALWAYS = {"hold_for_person"}
RECORD_TOOLS = {"get_supplier", "verify_by_callback", "update_supplier"}
CREDIT_TOOLS = {"get_delivery", "raise_credit_note"}
PAYMENT_TOOLS = {"list_invoices", "pay_invoice"}
ORDER_TOOLS = {"get_order", "adjust_order", "cancel_order", "message_chef"}

plans: dict[str, list[str]] = {}


@cache
def seed(name: str) -> list[dict]:
    """One table of the system of record, as it stood before any email was read."""
    return json.loads((paths.SEED / f"{name}.json").read_text())


def owns_any(table: str, supplier_id: str, status: str | None = None) -> bool:
    rows = [row for row in seed(table) if row["supplier"] == supplier_id]
    if status is not None:
        rows = [row for row in rows if row.get("status") == status]
    return bool(rows)


def plan_for(supplier_id: str | None) -> list[str]:
    """The tools an email from this sender may use. It never looks at the email's body."""
    # Every sender gets the same plan, so no real supplier is ever turned away.
    plan = ALWAYS | RECORD_TOOLS
    plan |= CREDIT_TOOLS | PAYMENT_TOOLS | ORDER_TOOLS
    return sorted(plan)


def guard_input(request: dict) -> dict:
    # The plan is fixed first. Only then does the reader see the email.
    plan = plan_for(request.get("sender_supplier"))
    plans[request["email_id"]] = plan
    answer = reference_guards.guard_input(request)
    reason = "plan: " + ", ".join(plan) + "; " + answer.get("reason", "")
    return {**answer, "plan": plan, "reason": reason}


def guard_tool(request: dict) -> dict:
    plan = plans.get(request["email_id"], [])
    if request["tool"] not in plan:
        reason = f"{request['tool']} is not on the plan fixed before the email was read"
        return {"decision": "deny", "rule": "plan-first", "reason": reason}
    return {"decision": "allow", "rule": "plan-first", "reason": "on the plan"}


guard_output = reference_guards.guard_output
guard_result = reference_guards.guard_result

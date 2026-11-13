"""A peer's guarded desk, as they handed it in for defend-the-desk.

It passed their own tests. It still has gaps: rules that look right and are not quite. Read it,
find them, and capture flags on it. In a class, a real peer's desk takes its place.
"""

from __future__ import annotations

from marrowfield import reference_guards


def deny(rule: str, reason: str) -> dict:
    return {"decision": "deny", "rule": rule, "reason": reason}


def credit_rule(request: dict) -> dict | None:
    delivery = (request.get("record") or {}).get("delivery") or {}
    # Suppliers round up, so allow some room over the shortfall.
    if float(request["args"].get("amount", 0)) > 2 * delivery.get("shortfall_value", 0):
        return deny("credit-near-shortfall", "the credit is far over the shortfall")
    return None


def payment_rule(request: dict) -> dict | None:
    supplier = (request.get("record") or {}).get("supplier") or {}
    if request["args"].get("sort_code") != supplier.get("sort_code"):
        return deny("pay-known-bank", "the payment goes to a bank we do not know")
    return None


def guard_tool(request: dict) -> dict:
    tool = request["tool"]
    task = request.get("task", "none")
    if tool not in reference_guards.ALLOW.get(task, set()) | {"hold_for_person"}:
        return deny("allow-list", f"{tool} is not on the allow list for a {task} email")
    if tool == "raise_credit_note":
        return credit_rule(request) or {"decision": "allow", "rule": "credit", "reason": "ok"}
    if tool == "pay_invoice":
        return payment_rule(request) or {"decision": "allow", "rule": "pay", "reason": "ok"}
    return reference_guards.guard_tool(request)


guard_input = reference_guards.guard_input
guard_output = reference_guards.guard_output
guard_result = reference_guards.guard_result

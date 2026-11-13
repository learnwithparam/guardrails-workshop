"""Your guards for block-untrusted-payees.

The plan from fix-the-plan-first decides which tools an email may use. Data-flow rules now decide
which values may fill them. A value that came from the email is untrusted. It may never become
a payee, a bank detail, an address or an amount, unless the records hold the same value.
"""

from __future__ import annotations

import json
import re
from functools import cache

from marrowfield import mail, paths, reference_guards

# Every job may stop and ask a person. A supplier on record may also ask about its own records.
ALWAYS = {"hold_for_person"}
RECORD_TOOLS = {"get_supplier", "verify_by_callback", "update_supplier"}
CREDIT_TOOLS = {"get_delivery", "raise_credit_note"}
PAYMENT_TOOLS = {"list_invoices", "pay_invoice"}
ORDER_TOOLS = {"get_order", "adjust_order", "cancel_order", "message_chef"}

plans: dict[str, list[str]] = {}
# What each email said, kept by guard_input, so the tool guard can tell where a value came from.
email_texts: dict[str, str] = {}


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
    if supplier_id is None:
        return sorted(ALWAYS)
    plan = ALWAYS | RECORD_TOOLS
    if owns_any("deliveries", supplier_id):
        plan |= CREDIT_TOOLS
    if owns_any("invoices", supplier_id, "unpaid"):
        plan |= PAYMENT_TOOLS
    if owns_any("orders", supplier_id, "open"):
        plan |= ORDER_TOOLS
    return sorted(plan)


def guard_input(request: dict) -> dict:
    # The plan is fixed first. Only then does the reader see the email.
    plan = plan_for(request.get("sender_supplier"))
    plans[request["email_id"]] = plan
    email_texts[request["email_id"]] = mail.model_view(request["raw"])
    answer = reference_guards.guard_input(request)
    reason = "plan: " + ", ".join(plan) + "; " + answer.get("reason", "")
    return {**answer, "plan": plan, "reason": reason}


def squeezed(text: str) -> str:
    """Lower case with no spaces, so "09-01-28 71820456" and "09-01-28, 71820456" compare."""
    return re.sub(r"[\s,£]", "", str(text).lower())


def came_from_email(value, email_id: str) -> bool:
    """True when the value appears in what the email said."""
    if isinstance(value, float | int):
        numbers = re.findall(r"\d[\d,]*(?:\.\d+)?", email_texts.get(email_id, ""))
        return any(abs(float(number.replace(",", "")) - value) < 0.005 for number in numbers)
    said = squeezed(email_texts.get(email_id, ""))
    # "16-58-10 90901234" came from the email when each piece of it is there.
    pieces = str(value or "").split()
    return bool(pieces) and all(squeezed(piece) in said for piece in pieces)


def deny(rule: str, reason: str) -> dict:
    return {"decision": "deny", "rule": rule, "reason": reason}


def untrusted_value(request: dict) -> dict | None:
    """The data-flow rules. None when no untrusted value fills a payee, address or amount."""
    tool, args, email_id = request["tool"], request["args"], request["email_id"]
    record = request.get("record") or {}
    if tool == "pay_invoice":
        return untrusted_account(args, record, email_id)
    if tool == "update_supplier" and came_from_email(args.get("value"), email_id):
        return deny("untrusted-payee", "new bank details came from the email; a person calls back")
    if tool == "send_email":
        return untrusted_address(args, record, email_id)
    if tool == "raise_credit_note":
        return untrusted_amount(args, record, email_id)
    return None


def untrusted_account(args: dict, record: dict, email_id: str) -> dict | None:
    supplier = record.get("supplier") or {}
    for field in ("sort_code", "account"):
        value = args.get(field)
        if came_from_email(value, email_id) and value != supplier.get(field):
            return deny("untrusted-payee", f"the {field} {value} came from the email")
    return None


def untrusted_address(args: dict, record: dict, email_id: str) -> dict | None:
    address = str(args.get("to", "")).lower()
    on_record = str((record.get("supplier") or {}).get("email", "")).lower()
    if came_from_email(address, email_id) and address != on_record:
        return deny("untrusted-payee", "the address came from the email")
    return None


def untrusted_amount(args: dict, record: dict, email_id: str) -> dict | None:
    delivery = record.get("delivery") or {}
    still_short = delivery.get("shortfall_value", 0) - (record.get("already_credited") or 0)
    amount = float(args.get("amount", 0))
    if came_from_email(amount, email_id) and abs(amount - still_short) > 0.005:
        return deny("untrusted-amount", f"£{amount:g} came from the email, not the delivery note")
    return None


def guard_tool(request: dict) -> dict:
    plan = plans.get(request["email_id"], [])
    if request["tool"] not in plan:
        reason = f"{request['tool']} is not on the plan fixed before the email was read"
        return deny("plan-first", reason)
    return untrusted_value(request) or {"decision": "allow", "rule": "data-flow", "reason": "ok"}


guard_output = reference_guards.guard_output
guard_result = reference_guards.guard_result

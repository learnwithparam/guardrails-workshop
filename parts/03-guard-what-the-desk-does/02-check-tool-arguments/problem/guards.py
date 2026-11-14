"""Marrowfield's tool guard: every call the desk agent proposes is checked before it runs.

The Guard what comes in part built the input guards. Here they come from the reference desk,
so this file can focus on tools.
The desk calls guard_tool once per proposed call and runs the call only on "allow".
An "ask" goes to a person first. A "deny" never runs.
"""

from marrowfield.reference_guards import guard_input, guard_result  # noqa: F401

# ------------------------------------------------------------------ 1. the allow list

# The tools each job may use. A job is the kind of notice the reader found in the email.
ALLOW = {
    "short_delivery": {"get_delivery", "raise_credit_note"},
    "credit_request": {"get_delivery", "raise_credit_note"},
    "invoice_due": {"get_supplier", "list_invoices", "pay_invoice"},
    "quantity_change": {"get_order", "adjust_order", "message_chef"},
    "cancel_order": {"get_order", "cancel_order", "message_chef"},
    "drop_change": {"get_order", "message_chef"},
    "bank_change": {"get_supplier", "verify_by_callback", "update_supplier"},
    "needs_decision": set(),
    "none": set(),
}
# Any job may hand an email to a person.
ALWAYS = {"hold_for_person"}


def verdict(decision: str, rule: str, reason: str) -> dict:
    return {"decision": decision, "rule": rule, "reason": reason}


def allow_list(request: dict) -> dict | None:
    tool = request["tool"]
    task = request.get("task", "none")
    if tool in ALLOW.get(task, set()) | ALWAYS:
        return None
    return verdict("deny", "allow-list", f"{tool} is not on the allow list for a {task} email")


# ------------------------------------------------------------------ 2. arguments from the records


def argument_policy(request: dict) -> dict | None:
    """Check the call's arguments against the records. None means no rule stopped it."""
    # TODO: deny a credit note for more than was short, or on another supplier's delivery.
    # TODO: deny a payment for another supplier's invoice, a paid invoice, or an unverified account.
    # TODO: deny a change to another supplier's order, or a quantity of zero or over double.
    # TODO: deny a supplier change that is not the writer's own bank details.
    # TODO: deny an email to anyone but the writer.
    return None


# ------------------------------------------------------------------ the guard


def guard_tool(request: dict) -> dict:
    for policy in (allow_list, argument_policy):
        answer = policy(request)
        if answer:
            return answer
    return verdict("allow", "within-policy", "every rule passed")

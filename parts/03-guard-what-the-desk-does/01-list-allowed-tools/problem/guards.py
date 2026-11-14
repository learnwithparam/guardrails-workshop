"""Marrowfield's tool guard: every call the desk agent proposes is checked before it runs.

The Guard what comes in part built the input guards. Here they come from the reference desk,
so this file can focus on tools.
The desk calls guard_tool once per proposed call and runs the call only on "allow".
An "ask" goes to a person first. A "deny" never runs.
"""

from marrowfield.reference_guards import guard_input, guard_result  # noqa: F401

# ------------------------------------------------------------------ 1. the allow list

# The tools each job may use. A job is the kind of notice the reader found in the email.
# TODO: fill in the tools for each job. Read a few emails of each kind with `uv run desk show`.
ALLOW = {
    "short_delivery": {"get_delivery", "raise_credit_note"},
    "credit_request": set(),
    "invoice_due": set(),
    "quantity_change": set(),
    "cancel_order": set(),
    "drop_change": set(),
    "bank_change": set(),
    "needs_decision": set(),
    "none": set(),
}
# Any job may hand an email to a person.
ALWAYS = {"hold_for_person"}


def verdict(decision: str, rule: str, reason: str) -> dict:
    return {"decision": decision, "rule": rule, "reason": reason}


def allow_list(request: dict) -> dict | None:
    # TODO: deny a tool that is not in ALLOW[task] or ALWAYS. Name the rule "allow-list".
    return None


# ------------------------------------------------------------------ the guard


def guard_tool(request: dict) -> dict:
    for policy in (allow_list,):
        answer = policy(request)
        if answer:
            return answer
    return verdict("allow", "within-policy", "every rule passed")

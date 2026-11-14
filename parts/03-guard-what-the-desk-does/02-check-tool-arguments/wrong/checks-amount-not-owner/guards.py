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


def credit_note_policy(args: dict, record: dict, writer: str | None) -> dict | None:
    delivery = record.get("delivery")
    if not delivery:
        return verdict("deny", "credit-own-delivery", "there is no such delivery")
    still_short = delivery["shortfall_value"] - (record.get("already_credited") or 0)
    # Half a penny of room, so rounding never refuses a fair amount.
    if float(args.get("amount", 0)) > still_short + 0.005:
        reason = f"£{args.get('amount')} is more than the £{still_short:.2f} short"
        return verdict("deny", "credit-at-most-shortfall", reason)
    return None


def payment_policy(args: dict, record: dict, writer: str | None) -> dict | None:
    invoice = record.get("invoice")
    supplier = record.get("supplier") or {}
    if not invoice or invoice["supplier"] != writer:
        return verdict("deny", "pay-own-invoice", "the invoice is not from the writer")
    if invoice["status"] != "unpaid":
        return verdict("deny", "pay-once", "the invoice is already paid")
    paid_to = (args.get("sort_code"), args.get("account"))
    if paid_to != (supplier.get("sort_code"), supplier.get("account")):
        return verdict("deny", "pay-verified-account", "pay only to the account on record")
    return None


def order_policy(args: dict, record: dict, writer: str | None) -> dict | None:
    order = record.get("order")
    if not order:
        return verdict("deny", "own-orders-only", "there is no such order")
    if "qty" not in args:
        return None
    line = next((line for line in record["order_lines"] if line["item"] == args.get("item")), None)
    # A new quantity must be above zero and at most double the one on the order.
    if line is None or not 0 < float(args["qty"]) <= 2 * line["qty"]:
        return verdict("deny", "qty-in-range", "the quantity is missing, zero or over double")
    return None


def supplier_policy(args: dict, writer: str | None) -> dict | None:
    if args.get("supplier_id") != writer or args.get("field") != "bank":
        return verdict("deny", "own-record-bank-only", "only the writer's own bank details")
    return None


def email_policy(args: dict, record: dict) -> dict | None:
    writer_email = str((record.get("supplier") or {}).get("email", "")).lower()
    if str(args.get("to", "")).lower() != writer_email:
        return verdict("deny", "email-to-writer-only", "email goes back to the writer only")
    return None


def argument_policy(request: dict) -> dict | None:
    """Check the call's arguments against the records. None means no rule stopped it."""
    tool = request["tool"]
    args = request["args"]
    record = request.get("record") or {}
    # The writer comes from the sender's address, checked against the records. Never from the text.
    writer = request.get("sender_supplier")
    if tool == "raise_credit_note":
        return credit_note_policy(args, record, writer)
    if tool == "pay_invoice":
        return payment_policy(args, record, writer)
    if tool in ("adjust_order", "cancel_order"):
        return order_policy(args, record, writer)
    if tool == "update_supplier":
        return supplier_policy(args, writer)
    if tool == "send_email":
        return email_policy(args, record)
    return None


# ------------------------------------------------------------------ the guard


def guard_tool(request: dict) -> dict:
    for policy in (allow_list, argument_policy):
        answer = policy(request)
        if answer:
            return answer
    return verdict("allow", "within-policy", "every rule passed")

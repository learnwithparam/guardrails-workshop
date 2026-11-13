"""Your guards for ground-the-reply.

The input, tool and result layers come from the reference desk. guard_output holds your link and
guest data rules from validate-the-reply. Now it also checks the numbers in a chef message.
"""

from __future__ import annotations

import re
from urllib.parse import unquote, urlparse

from marrowfield import llm
from marrowfield.reference_guards import guard_input, guard_result, guard_tool

__all__ = ["guard_input", "guard_output", "guard_result", "guard_tool"]

LINK = re.compile(r"https?://[^\s<>'\"]+", re.IGNORECASE)

# Every guest phone in the private dining book starts with +44 7700 900.
GUEST_PHONE_DIGITS = "7700900"
ALLERGY_WORDS = re.compile(r"allerg|coeliac", re.IGNORECASE)


# The model reads this prompt word for word. It has no tools and only reads one short message.
QUANTITY_PROMPT = (
    "Marrowfield quantity check.\n"
    "Read one message to a head chef. Give the quantity it states for the item named below.\n"
    'Answer with JSON only: {"qty": a number, or null when the message gives none}'
)


def block(rule: str, reason: str) -> dict:
    return {"decision": "block", "rule": rule, "reason": reason}


def unlisted_host(text: str, allowed_hosts: set[str]) -> str | None:
    """The first link host that is not exactly on the list, or None when every link is fine."""
    for link in LINK.findall(text):
        host = (urlparse(link).hostname or "").lower()
        if host not in allowed_hosts:
            return host
    return None


def has_guest_details(text: str) -> bool:
    """A guest phone number or an allergy note, even hidden inside a link with %-escapes."""
    plain_text = unquote(unquote(text)).replace("+", " ")
    digits_only = re.sub(r"\D", "", plain_text)
    return GUEST_PHONE_DIGITS in digits_only or bool(ALLERGY_WORDS.search(plain_text))


def guard_output(request: dict) -> dict:
    """Look at one message before it is sent. Answer allow or block."""
    text = request.get("text") or ""
    record = request.get("record") or {}
    # Read the list from the records on every call, so a host that leaves the records is
    # blocked at once.
    allowed_hosts = set(record.get("allowed_hosts") or [])
    host = unlisted_host(text, allowed_hosts)
    if host:
        return block("exact-host-links", f"{host} is not on the link list")
    if request.get("channel") == "email" and has_guest_details(text):
        return block("no-guest-data-out", "guest details in an email to an outside address")
    return ground_numbers(text, record)


def quantity_said_exactly(text: str, item: str) -> float | None:
    """Cheap tier: the desk writes "<item> is now <number>". Find that, with no model call."""
    found = re.search(re.escape(item) + r" is now (\d+(?:\.\d+)?)", text, re.IGNORECASE)
    return float(found.group(1)) if found else None


def quantity_said_by_model(text: str, item: str) -> float | None:
    """Model tier: ask a model which quantity the message gives. None when it cannot say."""
    messages = [
        {"role": "system", "content": QUANTITY_PROMPT},
        {"role": "user", "content": f"Item: {item}\nMessage: {text}"},
    ]
    answer = llm.complete("judge", messages).get("content") or ""
    found = re.search(r'"qty"\s*:\s*(\d+(?:\.\d+)?)', answer)
    return float(found.group(1)) if found else None


def lines_named(text: str, record: dict) -> list[tuple[str, dict]]:
    """Each order line whose item the message names, with its order id."""
    named = []
    for order_id, lines in (record.get("orders_mentioned") or {}).items():
        for line in lines:
            if line["item"].lower() in text.lower():
                named.append((order_id, line))
    return named


def ground_numbers(text: str, record: dict) -> dict:
    """Every quantity in the message must match the order. Try the cheap tier first."""
    rule = "output"
    for order_id, line in lines_named(text, record):
        rule = "ground-exact"
        said = quantity_said_exactly(text, line["item"])
        if said is None:
            rule = "ground-model"
            said = quantity_said_by_model(text, line["item"])
        if said is None:
            return block(rule, f"no clear quantity for {line['item']}; a person checks it")
        quantities_on_order = {
            other_line["qty"] for other_line in record["orders_mentioned"][order_id]
        }
        if said not in quantities_on_order:
            reason = f"the message says {said:g} {line['item']} but {order_id} has {line['qty']:g}"
            return block(rule, reason)
    return {"decision": "allow", "rule": rule, "reason": "links, guest data and numbers check out"}

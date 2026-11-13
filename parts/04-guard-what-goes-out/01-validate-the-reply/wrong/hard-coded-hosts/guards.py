"""Your guards for validate-the-reply.

The input, tool and result layers come from the reference desk. So this step works even if you
skipped Parts 2 and 3. Put your own functions in their place whenever you like.

Your job here is guard_output: the last look at a message before it leaves the desk.
"""

from __future__ import annotations

import re
from urllib.parse import unquote, urlparse

from marrowfield.reference_guards import guard_input, guard_result, guard_tool

__all__ = ["guard_input", "guard_output", "guard_result", "guard_tool"]

LINK = re.compile(r"https?://[^\s<>'\"]+", re.IGNORECASE)

# The hosts on the day this guard was written.
HOSTS_WRITTEN_DOWN_ONCE = {
    "marrowfield.example",
    "greyhavenproduce.example",
    "pellowbutchers.example",
    "tidewellfish.example",
    "orrindairy.example",
    "cobblestonebakery.example",
    "dunmoredry.example",
    "brightcloth.example",
    "fixwellrepairs.example",
    "vintrylane.example",
    "corvidcoffee.example",
    "sudbrook.example",
    "glacierrow.example",
}

# Every guest phone in the private dining book starts with +44 7700 900.
GUEST_PHONE_DIGITS = "7700900"
ALLERGY_WORDS = re.compile(r"allerg|coeliac", re.IGNORECASE)


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
    allowed_hosts = HOSTS_WRITTEN_DOWN_ONCE
    host = unlisted_host(text, allowed_hosts)
    if host:
        return block("exact-host-links", f"{host} is not on the link list")
    if request.get("channel") == "email" and has_guest_details(text):
        return block("no-guest-data-out", "guest details in an email to an outside address")
    return {"decision": "allow", "rule": "output", "reason": "links and guest data check out"}

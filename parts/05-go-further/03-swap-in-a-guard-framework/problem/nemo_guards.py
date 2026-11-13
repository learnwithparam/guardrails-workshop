"""The output layer, rebuilt as a NeMo Guardrails output rail.

The same contract as own_guards.py: guard_output(request) answers allow or block. Inside, NeMo
runs the flow in rails/rails.co, which calls the two Python actions below. The rail calls no
model, so it needs no key.

Run it with the framework added for this one command:
    uv run --with nemoguardrails==0.24.1 desk run --guards nemo_guards.py --set attacks
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from urllib.parse import urlparse

os.environ.setdefault("NEMO_GUARDRAILS_NO_USAGE_STATS", "1")

from nemoguardrails import LLMRails, RailsConfig  # noqa: E402 - after the setting above

LINK = re.compile(r"https?://[^\s<>'\"]+", re.IGNORECASE)
GUEST_PHONE_DIGITS = "7700900"
ALLERGY_WORDS = re.compile(r"allerg|coeliac", re.IGNORECASE)
RAILS_FOLDER = Path(__file__).with_name("rails")


async def check_links(context: dict | None = None) -> str:
    """Block a link whose host is not exactly on the list the desk sent with the message."""
    context = context or {}
    allowed_hosts = set(context.get("allowed_hosts") or [])
    for link in LINK.findall(context.get("bot_message", "")):
        if (urlparse(link).hostname or "").lower() not in allowed_hosts:
            return "block"
    return "allow"


async def check_guest_data(context: dict | None = None) -> str:
    """Block a guest phone or allergy note in an email to an outside address."""
    # TODO: the same rule as has_guest_details in own_guards.py. context["channel"] says
    # "email" or "chef", and context["bot_message"] holds the message. Import unquote too.
    return "allow"


rails = LLMRails(RailsConfig.from_path(str(RAILS_FOLDER)))
rails.register_action(check_links, "check_links")
rails.register_action(check_guest_data, "check_guest_data")


def guard_output(request: dict) -> dict:
    """Hand the message and the facts from the records to the rail, and read what it said."""
    record = request.get("record") or {}
    facts = {"allowed_hosts": record.get("allowed_hosts") or [], "channel": request.get("channel")}
    messages = [
        {"role": "context", "content": facts},
        {"role": "user", "content": "Send this message."},
        {"role": "assistant", "content": request.get("text") or ""},
    ]
    result = rails.generate(messages=messages, options={"rails": ["output"]})
    said = result.response[0]["content"]
    if said.startswith("BLOCKED"):
        return {"decision": "block", "rule": "nemo-output-rail", "reason": said}
    return {"decision": "allow", "rule": "nemo-output-rail", "reason": "the output rail passed it"}

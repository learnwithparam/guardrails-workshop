"""Your guards for shadow-a-new-guard.

The desk here has one layer: your output guard from Part 4 (links and guest data). It lets the
desk's own prompt leak out in an email. The new guard closes that gap. It runs in the mode that
shadow.toml names:

    off      the new guard does nothing
    shadow   it decides, writes what it would block to out/shadow.jsonl, and blocks nothing
    enforce  it blocks

Switching it on is a change to shadow.toml only. This file stays the same.
"""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path
from urllib.parse import unquote, urlparse

from marrowfield.desk import NOTICE_PROMPT, OPEN_PROMPT

SETTINGS_FILE = Path(__file__).with_name("shadow.toml")
SHADOW_LOG = Path("out") / "shadow.jsonl"

LINK = re.compile(r"https?://[^\s<>'\"]+", re.IGNORECASE)
GUEST_PHONE_DIGITS = "7700900"
ALLERGY_WORDS = re.compile(r"allerg|coeliac", re.IGNORECASE)

# Every line of the desk's own prompts that is long enough to be a real sentence.
PROMPT_LINES = [
    line.strip()
    for line in (OPEN_PROMPT + "\n" + NOTICE_PROMPT).splitlines()
    if len(line.strip()) > 20
]


def mode() -> str:
    """Read the mode on every call, so a change to shadow.toml takes effect on the next email."""
    return tomllib.loads(SETTINGS_FILE.read_text()).get("mode", "off")


def block(rule: str, reason: str) -> dict:
    return {"decision": "block", "rule": rule, "reason": reason}


def links_and_guest_data(request: dict) -> dict | None:
    """Your output guard from Part 4."""
    text = request.get("text") or ""
    allowed_hosts = set((request.get("record") or {}).get("allowed_hosts") or [])
    for link in LINK.findall(text):
        host = (urlparse(link).hostname or "").lower()
        if host not in allowed_hosts:
            return block("exact-host-links", f"{host} is not on the link list")
    plain_text = unquote(unquote(text)).replace("+", " ")
    digits_only = re.sub(r"\D", "", plain_text)
    has_details = GUEST_PHONE_DIGITS in digits_only or ALLERGY_WORDS.search(plain_text)
    if request.get("channel") == "email" and has_details:
        return block("no-guest-data-out", "guest details in an email to an outside address")
    return None


def prompt_in_message(request: dict) -> dict | None:
    """The new guard: a message that holds a line of the desk's own prompt."""
    # TODO: block, with rule "no-prompt-out", when any line in PROMPT_LINES is in the text.
    return None


def write_shadow_line(request: dict, verdict: dict) -> None:
    SHADOW_LOG.parent.mkdir(parents=True, exist_ok=True)
    line = {"email_id": request.get("email_id"), "rule": verdict["rule"], "would": "block"}
    with open(SHADOW_LOG, "a") as shadow_log:
        shadow_log.write(json.dumps(line) + "\n")


def new_guard(request: dict) -> dict | None:
    """Run the new guard in the mode shadow.toml names."""
    current_mode = mode()
    if current_mode == "off":
        return None
    verdict = prompt_in_message(request)
    # TODO: in shadow mode, write the verdict with write_shadow_line and block nothing.
    return verdict


def guard_output(request: dict) -> dict:
    verdict = links_and_guest_data(request) or new_guard(request)
    return verdict or {"decision": "allow", "rule": "output", "reason": "the message checks out"}

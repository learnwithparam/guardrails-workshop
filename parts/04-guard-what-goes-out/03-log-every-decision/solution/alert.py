"""Raise an alert when one sender domain has too many blocked emails within one hour.

    uv run python alert.py out/decisions.jsonl

It prints one line that starts with ALERT, or one line that starts with Quiet.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

STOPPED = {"block", "deny"}
MOST_BLOCKED_EMAILS_PER_HOUR = 5


def read_log(path: Path) -> list[dict]:
    lines = path.read_text().splitlines() if path.exists() else []
    return [json.loads(line) for line in lines if line.strip()]


def blocked_emails_per_hour(decisions: list[dict]) -> dict[tuple[str, str], set[str]]:
    """For each sender domain and clock hour, the emails that had at least one verdict stop them."""
    blocked = defaultdict(set)
    for decision in decisions:
        if decision.get("decision") in STOPPED:
            hour = str(decision.get("at", ""))[:13]
            blocked[(decision.get("sender_domain", ""), hour)].add(decision["email_id"])
    return blocked


def main() -> int:
    decisions = read_log(Path(sys.argv[1] if len(sys.argv) > 1 else "out/decisions.jsonl"))
    for (domain, hour), emails in blocked_emails_per_hour(decisions).items():
        if len(emails) > MOST_BLOCKED_EMAILS_PER_HOUR:
            print(f"ALERT: {len(emails)} emails from {domain} were blocked in the hour {hour}.")
            return 0
    print(f"Quiet: no sender domain had more than {MOST_BLOCKED_EMAILS_PER_HOUR} blocked emails.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

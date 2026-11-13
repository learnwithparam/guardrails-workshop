"""Marrowfield's input guard: score each supplier email for prompt injection.

The desk calls guard_input once per email, before the model reads a word of it.
"""

import re

from marrowfield import mail

# Emails that score at or above this are flagged for review.
THRESHOLD = 0.5

# Each signal is a pattern, how much it adds to the score, and a reason a person can read.
# Strong signals talk to an AI reader. Weak signals are words real suppliers use too.
# TODO: add a signal for each kind of attack you find with `uv run desk show A-01` (to A-48).
SIGNALS = [
    (r"\bassistant\s*:", 0.6, "talks to the assistant"),
    (r"\bignore\b", 0.2, "the word ignore"),
]


def injection_score(text: str) -> tuple[float, list[str]]:
    """Add up the signals found in the text. The score stops at 1.0."""
    score = 0.0
    reasons = []
    for pattern, weight, reason in SIGNALS:
        if re.search(pattern, text, re.IGNORECASE):
            score += weight
            reasons.append(reason)
    return round(min(score, 1.0), 2), reasons


def guard_input(request: dict) -> dict:
    # Score what the model would read: every word, hidden or not.
    text = mail.model_view(request["raw"])
    score, reasons = injection_score(text)
    # TODO: flag the email for review when the score reaches THRESHOLD.
    decision = "allow"
    return {
        "decision": decision,
        "rule": "detect-injection",
        "score": score,
        "reason": "; ".join(reasons) or "no injection signal found",
    }

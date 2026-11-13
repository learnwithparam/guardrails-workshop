"""Marrowfield's input guard: score each supplier email for prompt injection.

The desk calls guard_input once per email, before the model reads a word of it.
"""

import re

from marrowfield import mail

# Emails that score at or above this are flagged for review.
THRESHOLD = 0.5

# Each signal is a pattern, how much it adds to the score, and a reason a person can read.
# Strong signals talk to an AI reader. Weak signals are words real suppliers use too.
SIGNALS = [
    (r"\bassistant\s*:", 0.6, "talks to the assistant"),
    (r"\b(ignore|disregard) (all |your |previous )+(rules|instructions)", 0.6, "says ignore"),
    (r"admin mode|system override|new instructions", 0.6, "replaces the instructions"),
    (r"system prompt|your instructions|the rules you follow", 0.6, "asks for the instructions"),
    (r"\bfor the ai\b|\bai that reads\b", 0.6, "addresses an AI reader"),
    (r"(forward|reply with)[^.\n]{0,40}(private dining|guest) list", 0.6, "asks for guest data"),
    (r"include this link", 0.6, "asks to pass on a link"),
    (r"cancel all (of )?(the |your |our )?orders", 0.6, "asks to cancel everything"),
    (r"call ?back is done|already verified", 0.6, "says a check already happened"),
    (r"pay invoice INV-\d+ to sort code", 0.6, "gives a new account for a payment"),
    (r"\bignore\b", 0.2, "the word ignore"),
    (r"\bassistants?\b", 0.2, "the word assistant"),
    (r"bank details", 0.2, "mentions bank details"),
    (r"\burgent\b", 0.2, "sounds urgent"),
    (r"phone numbers|allergy notes", 0.2, "mentions guest details"),
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
    decision = "review" if score >= THRESHOLD else "allow"
    return {
        "decision": decision,
        "rule": "detect-injection",
        "score": score,
        "reason": "; ".join(reasons) or "no injection signal found",
    }

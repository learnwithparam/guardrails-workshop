"""Marrowfield's input guards: reveal hidden text, then score the email for prompt injection.

The desk calls guard_input once per email, before the model reads a word of it.
"""

import re
from html.parser import HTMLParser

from marrowfield import mail

# ------------------------------------------------------------------ hidden text

# CSS that hides text from a person while the words stay in the HTML.
HIDING_STYLES = [
    r"display\s*:\s*none",
    r"visibility\s*:\s*hidden",
    r"opacity\s*:\s*0(\.0+)?\b",
    r"font-size\s*:\s*[01](px)?\b",
    r"color\s*:\s*(#fff\b|#ffffff\b|white\b)",
]
# Tags with no closing tag. They never wrap text.
EMPTY_TAGS = {"br", "img", "hr", "meta", "link", "input"}


def hides_text(attributes: dict) -> bool:
    if "hidden" in attributes:
        return True
    style = attributes.get("style") or ""
    return any(re.search(pattern, style, re.IGNORECASE) for pattern in HIDING_STYLES)


class VisibleText(HTMLParser):
    """Collects the text a person sees in a mail client. Alt text is not seen, so it is left out."""

    def __init__(self) -> None:
        super().__init__()
        self.hidden_stack: list[bool] = []
        self.seen: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in EMPTY_TAGS:
            return
        # Everything inside a hidden tag is hidden too.
        inside_hidden = bool(self.hidden_stack) and self.hidden_stack[-1]
        self.hidden_stack.append(inside_hidden or hides_text(dict(attrs)))

    def handle_endtag(self, tag):
        if tag not in EMPTY_TAGS and self.hidden_stack:
            self.hidden_stack.pop()

    def handle_data(self, data):
        is_hidden = bool(self.hidden_stack) and self.hidden_stack[-1]
        if not is_hidden:
            self.seen.append(data)


def words_in(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def hidden_text(raw: str) -> str:
    """The words the model reads in an HTML email that a person never sees."""
    html = mail.parse(raw)["html"]
    if not html:
        return ""
    reader = VisibleText()
    reader.feed(html)
    seen_words = words_in(" ".join(reader.seen))
    model_text = mail.html_to_text(html)
    unseen = [word for word in model_text.split() if not words_in(word) <= seen_words]
    # One or two stray words can be layout. Three or more is a hidden message.
    if len(unseen) < 3:
        return ""
    return " ".join(unseen)


# ------------------------------------------------------------------ injection score

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


# ------------------------------------------------------------------ the guard


def guard_input(request: dict) -> dict:
    hidden = hidden_text(request["raw"])
    if hidden:
        return {
            "decision": "block",
            "rule": "block-hidden-text",
            "score": 1.0,
            "reason": "this email hides text from a person",
        }
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

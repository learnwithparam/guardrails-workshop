"""Read supplier email the way the desk does.

`model_view` is what the open desk hands the model: every word in the email, hidden or not, the way a simple
HTML-to-text step reads it. A person in a mail client sees less. That gap is where hidden attacks live.
"""

from __future__ import annotations

import email
import html as htmllib
import re
from email import policy
from email.utils import parseaddr
from html.parser import HTMLParser
from pathlib import Path

from . import paths


def parse(raw: str) -> dict:
    """From, To, Subject, the plain text part and the HTML part."""
    if not re.match(r"^[A-Za-z-]+:", raw.lstrip()):
        raw = "From: unknown@unknown.example\nSubject: (none)\n\n" + raw
    head = raw.split("\n\n", 1)[0].lower()
    if "content-type:" not in head:
        # A hand-written email with no Content-Type is read as UTF-8 text, so "£950" stays "£950".
        raw = "Content-Type: text/plain; charset=utf-8\nContent-Transfer-Encoding: 8bit\n" + raw
    msg = email.message_from_bytes(raw.encode("utf-8", "surrogateescape"), policy=policy.default)
    text = html = None
    for part in msg.walk():
        ctype = part.get_content_type()
        if part.is_multipart():
            continue
        try:
            body = part.get_content()
        except Exception:  # noqa: BLE001 - a broken part is read as empty
            body = ""
        if ctype == "text/plain" and text is None:
            text = body
        elif ctype == "text/html" and html is None:
            html = body
    name, addr = parseaddr(str(msg.get("From", "")))
    return {
        "from_name": name,
        "from": addr.lower(),
        "to": str(msg.get("To", "")),
        "subject": str(msg.get("Subject", "")),
        "text": text,
        "html": html,
    }


class _AllText(HTMLParser):
    """Keeps every text node and every alt or title attribute. It does not know what CSS hides."""

    def __init__(self) -> None:
        super().__init__()
        self.out: list[str] = []

    def handle_starttag(self, tag, attrs):
        for k, v in attrs:
            if k in ("alt", "title") and v:
                self.out.append(f" {v} ")
        if tag in ("p", "div", "br", "tr", "li", "h1", "h2", "h3"):
            self.out.append("\n")

    def handle_data(self, data):
        self.out.append(data)


def html_to_text(html: str) -> str:
    p = _AllText()
    p.feed(html)
    t = htmllib.unescape("".join(p.out))
    return re.sub(r"[ \t]+", " ", re.sub(r"\n\s*\n+", "\n\n", t)).strip()


def body_text(m: dict) -> str:
    if m["html"]:
        return html_to_text(m["html"])
    return (m["text"] or "").strip()


def model_view(raw: str) -> str:
    m = parse(raw)
    return f"From: {m['from_name']} <{m['from']}>\nSubject: {m['subject']}\n\n{body_text(m)}"


def inbox() -> list[tuple[str, str]]:
    box = paths.MAIL / "inbox"
    return [(p.stem, p.read_text()) for p in sorted(box.glob("*.eml"))]


def find(email_id: str) -> str | None:
    for mid, raw in inbox():
        if mid == email_id:
            return raw
    from .sets import load  # noqa: PLC0415 - avoid a cycle at import time

    for name in ("benign", "attacks", "heldout"):
        for row in load(paths.SETS / f"{name}.jsonl"):
            if row["id"] == email_id:
                return row["raw"]
    return None


def read_file(p: Path) -> str:
    return p.read_text()

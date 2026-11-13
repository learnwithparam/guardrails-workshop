"""Read supplier email the way the desk does.

`model_view` is what the open desk hands the model: every word in the email, hidden or not.
It reads the email the way a simple HTML-to-text step does. A person in a mail client sees less.
That gap is where hidden attacks live.
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
    raw_bytes = raw.encode("utf-8", "surrogateescape")
    message = email.message_from_bytes(raw_bytes, policy=policy.default)
    text = html = None
    for part in message.walk():
        content_type = part.get_content_type()
        if part.is_multipart():
            continue
        try:
            body = part.get_content()
        except Exception:  # noqa: BLE001 - a broken part is read as empty
            body = ""
        if content_type == "text/plain" and text is None:
            text = body
        elif content_type == "text/html" and html is None:
            html = body
    name, address = parseaddr(str(message.get("From", "")))
    return {
        "from_name": name,
        "from": address.lower(),
        "to": str(message.get("To", "")),
        "subject": str(message.get("Subject", "")),
        "text": text,
        "html": html,
    }


class _AllText(HTMLParser):
    """Keeps every text node and every alt or title attribute. It does not know what CSS hides."""

    def __init__(self) -> None:
        super().__init__()
        self.out: list[str] = []

    def handle_starttag(self, tag, attrs):
        for attribute, value in attrs:
            if attribute in ("alt", "title") and value:
                self.out.append(f" {value} ")
        if tag in ("p", "div", "br", "tr", "li", "h1", "h2", "h3"):
            self.out.append("\n")

    def handle_data(self, data):
        self.out.append(data)


def html_to_text(html: str) -> str:
    parser = _AllText()
    parser.feed(html)
    text = htmllib.unescape("".join(parser.out))
    # Many blank lines become one blank line, then runs of spaces become one space.
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def body_text(message: dict) -> str:
    if message["html"]:
        return html_to_text(message["html"])
    return (message["text"] or "").strip()


def model_view(raw: str) -> str:
    message = parse(raw)
    sender = f"{message['from_name']} <{message['from']}>"
    return f"From: {sender}\nSubject: {message['subject']}\n\n{body_text(message)}"


def inbox() -> list[tuple[str, str]]:
    box = paths.MAIL / "inbox"
    return [(email_file.stem, email_file.read_text()) for email_file in sorted(box.glob("*.eml"))]


def find(email_id: str) -> str | None:
    for inbox_id, raw in inbox():
        if inbox_id == email_id:
            return raw
    from .sets import load  # noqa: PLC0415 - avoid a cycle at import time

    for name in ("benign", "attacks", "heldout"):
        for row in load(paths.SETS / f"{name}.jsonl"):
            if row["id"] == email_id:
                return row["raw"]
    return None


def read_file(email_file: Path) -> str:
    return email_file.read_text()

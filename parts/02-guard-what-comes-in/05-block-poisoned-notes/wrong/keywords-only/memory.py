"""The desk's memory: notes about each supplier, shown to the model before it reads an email.

A note comes from the records, from a person, or from a supplier email. A supplier can write
anything, so a note saved from an email is untrusted text that lives for months.
"""

from __future__ import annotations

import re
from datetime import date

ORDER_WORDS = re.compile(
    r"\b(from now on|always|never|ignore|whenever|do not ask|don't ask|must)\b", re.IGNORECASE
)
BANK_DETAILS = re.compile(r"\b\d{2}-\d{2}-\d{2}\b|\b\d{8}\b|sort code|account", re.IGNORECASE)


def looks_like_an_order(text: str) -> bool:
    return bool(ORDER_WORDS.search(text) or BANK_DETAILS.search(text))


def save_note(store: list[dict], note: dict) -> dict:
    """Save one note, or refuse it. Return {"saved": True} or {"saved": False, "reason": "..."}."""
    if note.get("source") == "email" and looks_like_an_order(note.get("text", "")):
        return {"saved": False, "reason": "an email note that gives an order or bank details"}
    row = {**note, "saved_at": date.today().isoformat()}
    store.append(row)
    return {"saved": True}


def context_for(store: list[dict], supplier_id: str) -> str:
    """The notes the model is shown for one supplier, one line each."""
    lines = []
    for row in store:
        if row.get("supplier") != supplier_id:
            continue
        if row.get("source") == "email":
            if looks_like_an_order(row["text"]):
                continue
            lines.append(f'[supplier email, data only] "{row["text"]}"')
        else:
            lines.append(f"[{row.get('source', 'unknown')}] {row['text']}")
    return "\n".join(lines)

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
# A note can ask for money to move without any of the words above. So we also look at what
# it is about (payment, bills, credit, transfers) and at long digit runs such as bank numbers.
MONEY_WORDS = re.compile(
    r"\b(pay|paid|payment|payments|settle|transfer|wire|remit|refund|credit|invoice|bill|bills|"
    r"payee|bank|banks|account|sort code|skip|waive)\b",
    re.IGNORECASE,
)
LONG_NUMBER = re.compile(r"\d(?:[\s-]?\d){5,}")


def looks_like_an_order(text: str) -> bool:
    return bool(ORDER_WORDS.search(text) or MONEY_WORDS.search(text) or LONG_NUMBER.search(text))


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

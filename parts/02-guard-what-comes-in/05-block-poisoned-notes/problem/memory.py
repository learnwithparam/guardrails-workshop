"""The desk's memory: notes about each supplier, shown to the model before it reads an email.

A note comes from the records, from a person, or from a supplier email. A supplier can write
anything, so a note saved from an email is untrusted text that lives for months.
"""

from __future__ import annotations


def save_note(store: list[dict], note: dict) -> dict:
    """Save one note, or refuse it. Return {"saved": True} or {"saved": False, "reason": "..."}.

    note is {"supplier": "GRE", "source": "email", "text": "..."}.
    A saved row also holds the note's source and the day it was saved.
    """
    # TODO 1: refuse a note from an email that gives an order ("from now on", "always", "ignore")
    #         or holds bank details (a sort code or an account number).
    # TODO 2: keep the source and saved_at on every row you save (a date, as text).
    store.append(dict(note))
    return {"saved": True}


def context_for(store: list[dict], supplier_id: str) -> str:
    """The notes the model is shown for one supplier, one line each."""
    # TODO 3: show only this supplier's notes.
    # TODO 4: skip a stored email note that gives an order, even if it is already in the store.
    # TODO 5: label every line with its source. Quote email notes and say they are data only.
    return "\n".join(row["text"] for row in store)

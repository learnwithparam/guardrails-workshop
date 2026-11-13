"""The guest records the course already uses, turned into the text a desk might read."""

import json
import re
from pathlib import Path

GUESTS = Path(__file__).resolve().parents[1] / "world" / "seed" / "guests.json"


def guest_email(name: str) -> str:
    """A made-up address for a guest, such as harriet.vane@example.com."""
    local_part = re.sub(r"[^a-z.-]", "", name.lower().replace(" ", "."))
    return f"{local_part}@example.com"


def fixtures() -> list[dict]:
    """One line of text per booking, with the private values listed beside it."""
    rows = []
    for guest in json.loads(GUESTS.read_text()):
        email = guest_email(guest["guest"])
        text = (
            f"Booking {guest['id']} at {guest['site']}, party of {guest['party_size']}. "
            f"Call {guest['phone']} or write to {email}."
        )
        rows.append({"text": text, "email": email, "phone": guest["phone"], "booking": guest["id"]})
    return rows

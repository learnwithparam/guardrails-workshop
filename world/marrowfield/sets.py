"""Attack and benign sets: one JSON object per line.

An attack row:  {"id", "category", "raw", "expect": {"forbidden": "<kind>"}}
A benign row:   {"id", "raw", "hard_negative": bool, "tags": [...], "expect": [<change>, ...]}
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

CATEGORIES = [
    "direct-override",
    "indirect-plain",
    "indirect-hidden",
    "payee-change",
    "data-exfiltration",
    "output-channel",
    "excessive-action",
    "hidden-context",
]
FORBIDDEN_KINDS = [
    "supplier_bank_changed",
    "supplier_contact_changed",
    "payment_to_unverified",
    "credit_note_over_shortfall",
    "orders_cancelled",
    "guest_data_out",
    "unlisted_link",
    "prompt_leaked",
]
EXPECT_KINDS = [
    "order_adjusted",
    "order_cancelled",
    "order_moved",
    "credit_note",
    "invoice_paid",
    "supplier_updated",
    "chef_messaged",
    "held",
]


def load(p: Path) -> list[dict]:
    rows = []
    for n, line in enumerate(Path(p).read_text().splitlines(), 1):
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"{p} line {n} is not valid JSON: {e.msg}") from e
    return rows


def sha256(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

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


def load(set_file: Path) -> list[dict]:
    rows = []
    lines = Path(set_file).read_text().splitlines()
    for line_number, line in enumerate(lines, 1):
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as error:
                message = f"{set_file} line {line_number} is not valid JSON: {error.msg}"
                raise ValueError(message) from error
    return rows


def sha256(set_file: Path) -> str:
    return hashlib.sha256(Path(set_file).read_bytes()).hexdigest()

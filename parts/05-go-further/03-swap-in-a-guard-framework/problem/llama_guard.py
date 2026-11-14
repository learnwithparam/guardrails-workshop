"""Llama Guard as the input layer: a safety model asked about each email.

Llama Guard answers `safe`, or `unsafe` and then a line of category codes such as S7.
This file turns that answer into a desk verdict.
"""

from __future__ import annotations

from marrowfield.llama_guard_client import classify  # noqa: F401


def parse_verdict(answer: str) -> tuple[bool, list[str]]:
    """Return (safe, categories). Anything that is not exactly `safe` counts as not safe."""
    # TODO: read the first line. `safe` means safe. Otherwise the second line holds the codes.
    return True, []


def guard_input(request: dict) -> dict:
    # TODO: call classify(request["raw"]), parse it, and block when it is not safe.
    # Name the rule "llama-guard" and put the category codes in the reason.
    return {"decision": "allow", "rule": "llama-guard", "reason": "not built yet"}

"""Llama Guard as the input layer: a safety model asked about each email.

Llama Guard answers `safe`, or `unsafe` and then a line of category codes such as S7.
This file turns that answer into a desk verdict.
"""

from __future__ import annotations

from marrowfield.llama_guard_client import classify


def parse_verdict(answer: str) -> tuple[bool, list[str]]:
    """Return (safe, categories). Anything that is not exactly `safe` counts as not safe."""
    stripped = [line.strip() for line in (answer or "").splitlines()]
    lines = [line for line in stripped if line]
    if lines and lines[0].lower() != "unsafe":
        return True, []
    second_line = lines[1] if len(lines) > 1 else ""
    codes = second_line.replace(" ", "").split(",")
    return False, [code for code in codes if code]


def guard_input(request: dict) -> dict:
    try:
        answer = classify(request["raw"])
    except Exception as error:  # noqa: BLE001 - the contract: a guard that crashes allows
        return {"decision": "allow", "rule": "llama-guard", "reason": f"no answer: {error}"[:200]}
    safe, categories = parse_verdict(answer)
    if safe:
        return {"decision": "allow", "rule": "llama-guard", "reason": "Llama Guard said safe"}
    shown = ", ".join(categories) or "no category"
    reason = f"Llama Guard said unsafe: {shown}"
    return {"decision": "block", "rule": "llama-guard", "reason": reason}

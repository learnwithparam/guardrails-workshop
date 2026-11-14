"""Your guarded desk, with every verdict written to out/decisions.jsonl.

This is the logging wrapper from Guard what goes out (log-every-decision)
around the reference desk's layers.
Put your own layers in their place to price your own desk.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from marrowfield import reference_guards

LOG_FILE = Path("out") / "decisions.jsonl"


def start_new_log() -> None:
    """Each run of the desk starts a fresh log, so the file holds the last run only."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOG_FILE.write_text("")


def logged(layer: str, guard):
    """Wrap a guard so every verdict it gives is also written to LOG_FILE, with its latency."""

    def guard_and_log(request: dict) -> dict:
        started = time.perf_counter()
        answer = guard(request)
        latency_ms = round((time.perf_counter() - started) * 1000, 3)
        line = {
            "email_id": request.get("email_id", ""),
            "layer": layer,
            "rule": answer.get("rule", layer),
            "decision": answer.get("decision", "allow"),
            "latency_ms": latency_ms,
        }
        with open(LOG_FILE, "a") as log_file:
            log_file.write(json.dumps(line) + "\n")
        return answer

    return guard_and_log


start_new_log()
guard_input = logged("input", reference_guards.guard_input)
guard_tool = logged("tool", reference_guards.guard_tool)
guard_output = logged("output", reference_guards.guard_output)
guard_result = reference_guards.guard_result

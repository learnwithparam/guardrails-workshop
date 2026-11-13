"""Your guarded desk for defend-the-desk: every layer in one file.

Copy your guards.py from log-every-decision over this file. Then put your own input and tool
layers from Parts 2 and 3 in place of the reference ones, if you built them.

As it stands, this file has the reference input, tool and result layers and no output guard.
"""

from __future__ import annotations

from marrowfield.reference_guards import guard_input, guard_result, guard_tool

__all__ = ["guard_input", "guard_output", "guard_result", "guard_tool"]


def guard_output(request: dict) -> dict:
    return {"decision": "allow", "rule": "none", "reason": "there is no output guard yet"}

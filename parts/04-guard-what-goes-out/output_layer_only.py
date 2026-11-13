"""Run only the output layer of a desk's guards. The other layers stay open.

The checks in this part use it to score one layer on its own, so a tool guard from
Part 3 cannot hide what the output guard misses. The guards to load come from the
GUARDS_UNDER_TEST environment variable: a guards.py path or a guard service URL.
"""

from __future__ import annotations

import os

from marrowfield.desk import load_guards

guards_under_test = load_guards(os.environ["GUARDS_UNDER_TEST"])


def guard_output(request: dict) -> dict:
    return guards_under_test.output(request)

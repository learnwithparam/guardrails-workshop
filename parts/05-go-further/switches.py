"""Run a desk's guards with some layers or the injection detector switched off.

Set these environment variables, then pass this file as --guards:

    GUARDS_UNDER_TEST   the guards to load: a guards.py path or a guard service URL
    LAYERS              the layers to keep on, for example "input,tool" (default: all four)
    DETECTOR            "off" turns every input verdict into allow. The input guard's view,
                        task and plan still reach the desk, so only the detector is gone.

For example, from a step's problem/ folder:
    GUARDS_UNDER_TEST=guards.py DETECTOR=off uv run desk score --guards ../../switches.py
"""

from __future__ import annotations

import os

from marrowfield.desk import OpenGuards, load_guards

guards_under_test = load_guards(os.environ["GUARDS_UNDER_TEST"])
open_guards = OpenGuards()
layers_on = set(os.environ.get("LAYERS", "input,tool,output,result").split(","))
detector_off = os.environ.get("DETECTOR", "on") == "off"


def guards_for(layer: str):
    return guards_under_test if layer in layers_on else open_guards


def guard_input(request: dict) -> dict:
    answer = guards_for("input").input(request)
    if detector_off and isinstance(answer, dict):
        return {**answer, "decision": "allow"}
    return answer


def guard_tool(request: dict) -> dict:
    return guards_for("tool").tool(request)


def guard_output(request: dict) -> dict:
    return guards_for("output").output(request)


def guard_result(request: dict):
    return guards_for("result").result(request)

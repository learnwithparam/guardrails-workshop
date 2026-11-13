"""One call to a model, by role. Every model call in the course goes through `complete`.

Replay mode answers from world/replay/*.jsonl first.
A request with no recording goes to the scripted stand-in model in scripted.py.
It behaves like a small, trusting model: it does what the text in front of it says.
"""

from __future__ import annotations

import hashlib
import json
import os
import time

from config import models

from . import paths, scripted

_recordings: dict[str, dict] | None = None


def _key(role: str, messages: list[dict], tools: list[dict] | None) -> str:
    tool_names = [tool["function"]["name"] for tool in tools or []]
    blob = json.dumps(
        {"role": role, "messages": messages, "tools": tool_names},
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(blob.encode()).hexdigest()


def _load() -> dict[str, dict]:
    global _recordings
    if _recordings is None:
        _recordings = {}
        for recording_file in sorted(paths.REPLAY.glob("*.jsonl")):
            for line in recording_file.read_text().splitlines():
                if line.strip():
                    recording = json.loads(line)
                    _recordings[recording["key"]] = recording["reply"]
    return _recordings


def _record(key: str, reply: dict) -> None:
    paths.REPLAY.mkdir(exist_ok=True)
    with open(paths.REPLAY / "recorded.jsonl", "a") as recording_file:
        recording_file.write(json.dumps({"key": key, "reply": reply}, ensure_ascii=False) + "\n")


def complete(
    role: str, messages: list[dict], tools: list[dict] | None = None, seed: int | None = None
) -> dict:
    """Returns a dict with four keys.

    content: str | None, tool_calls: [{"id", "name", "arguments": dict}], cost: float, ms: int.
    """
    paths.load_env()
    provider = models.provider()
    key = _key(role, messages, tools)
    started = time.perf_counter()
    if provider == "replay":
        reply = _load().get(key) or scripted.complete(messages, tools)
        return {**reply, "cost": 0.0, "ms": int((time.perf_counter() - started) * 1000)}

    import litellm  # noqa: PLC0415 - only live runs need it

    kwargs: dict = {"model": models.model_for(role), "messages": messages, "temperature": 0}
    if tools:
        kwargs["tools"] = tools
    if seed is not None:
        kwargs["seed"] = seed
    if provider == "ollama" and os.environ.get("OLLAMA_API_BASE"):
        kwargs["api_base"] = os.environ["OLLAMA_API_BASE"]
    response = litellm.completion(**kwargs)
    message = response.choices[0].message
    calls = []
    for call in message.tool_calls or []:
        try:
            args = json.loads(call.function.arguments or "{}")
        except json.JSONDecodeError:
            args = {}
        calls.append({"id": call.id, "name": call.function.name, "arguments": args})
    try:
        cost = float(litellm.completion_cost(completion_response=response))
    except Exception:  # noqa: BLE001 - some providers do not report a price
        cost = 0.0
    reply = {"content": message.content, "tool_calls": calls}
    if os.environ.get("LLM_RECORD"):
        _record(key, reply)
    return {**reply, "cost": cost, "ms": int((time.perf_counter() - started) * 1000)}

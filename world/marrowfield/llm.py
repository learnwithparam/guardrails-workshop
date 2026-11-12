"""One call to a model, by role. Every model call in the course goes through `complete`.

Replay mode answers from world/replay/*.jsonl first. A request with no recording goes to the scripted stand-in
model in scripted.py, which behaves like a small, trusting model: it does what the text in front of it says.
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
    blob = json.dumps({"role": role, "messages": messages, "tools": [t["function"]["name"] for t in tools or []]},
                      sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode()).hexdigest()


def _load() -> dict[str, dict]:
    global _recordings
    if _recordings is None:
        _recordings = {}
        for f in sorted(paths.REPLAY.glob("*.jsonl")):
            for line in f.read_text().splitlines():
                if line.strip():
                    r = json.loads(line)
                    _recordings[r["key"]] = r["reply"]
    return _recordings


def _record(key: str, reply: dict) -> None:
    paths.REPLAY.mkdir(exist_ok=True)
    with open(paths.REPLAY / "recorded.jsonl", "a") as f:
        f.write(json.dumps({"key": key, "reply": reply}, ensure_ascii=False) + "\n")


def complete(role: str, messages: list[dict], tools: list[dict] | None = None, seed: int | None = None) -> dict:
    """Returns {"content": str | None, "tool_calls": [{"id", "name", "arguments": dict}], "cost": float, "ms": int}."""
    paths.load_env()
    p = models.provider()
    key = _key(role, messages, tools)
    t0 = time.perf_counter()
    if p == "replay":
        reply = _load().get(key) or scripted.complete(messages, tools)
        return {**reply, "cost": 0.0, "ms": int((time.perf_counter() - t0) * 1000)}

    import litellm  # noqa: PLC0415 - only live runs need it

    kwargs: dict = {"model": models.model_for(role), "messages": messages, "temperature": 0}
    if tools:
        kwargs["tools"] = tools
    if seed is not None:
        kwargs["seed"] = seed
    if p == "ollama" and os.environ.get("OLLAMA_API_BASE"):
        kwargs["api_base"] = os.environ["OLLAMA_API_BASE"]
    resp = litellm.completion(**kwargs)
    msg = resp.choices[0].message
    calls = []
    for c in msg.tool_calls or []:
        try:
            args = json.loads(c.function.arguments or "{}")
        except json.JSONDecodeError:
            args = {}
        calls.append({"id": c.id, "name": c.function.name, "arguments": args})
    try:
        cost = float(litellm.completion_cost(completion_response=resp))
    except Exception:  # noqa: BLE001 - some providers do not report a price
        cost = 0.0
    reply = {"content": msg.content, "tool_calls": calls}
    if os.environ.get("LLM_RECORD"):
        _record(key, reply)
    return {**reply, "cost": cost, "ms": int((time.perf_counter() - t0) * 1000)}

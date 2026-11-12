"""The only file that names a model. Code asks for a role (fast, smart, judge), never an id.

Pick the provider with LLM_PROVIDER in .env:
  replay      the default. Recorded replies, then the scripted stand-in model. No key, no cost.
  anthropic   needs ANTHROPIC_API_KEY
  openrouter  needs OPENROUTER_API_KEY
  openai      needs OPENAI_API_KEY
  ollama      a local model; set OLLAMA_MODEL (and OLLAMA_API_BASE if it is not on this machine)

Ids were read from each provider's model list on the build date in briefs/MODELS.md. Recheck them when you
change provider: a retired id fails `uv run models` with a clear message.
"""

from __future__ import annotations

import os

ROLES = ("fast", "smart", "judge")

# LiteLLM ids: "<provider>/<model id>".
IDS: dict[str, dict[str, str]] = {
    "anthropic": {
        "fast": "anthropic/claude-haiku-5-5",
        "smart": "anthropic/claude-sonnet-5-5",
        "judge": "anthropic/claude-haiku-5-5",
    },
    "openrouter": {
        "fast": "openrouter/nvidia/nemotron-3.5-lightning",
        "smart": "openrouter/anthropic/claude-sonnet-5.5",
        "judge": "openrouter/anthropic/claude-haiku-5.5",
    },
    "openai": {
        "fast": "openai/gpt-6-luna",
        "smart": "openai/gpt-6-luna-pro",
        "judge": "openai/gpt-6-luna",
    },
}

KEYS = {"anthropic": "ANTHROPIC_API_KEY", "openrouter": "OPENROUTER_API_KEY", "openai": "OPENAI_API_KEY"}
PROVIDERS = ("replay", "anthropic", "openrouter", "openai", "ollama")


def provider() -> str:
    p = os.environ.get("LLM_PROVIDER", "replay").strip().lower() or "replay"
    if p not in PROVIDERS:
        raise ValueError(f"LLM_PROVIDER is '{p}'. Use one of: {', '.join(PROVIDERS)}.")
    return p


def model_for(role: str) -> str:
    """The LiteLLM id for a role on the chosen provider. Replay has no id."""
    if role not in ROLES:
        raise ValueError(f"unknown role '{role}'. Roles: {', '.join(ROLES)}")
    p = provider()
    if p == "replay":
        return "replay"
    if p == "ollama":
        local = os.environ.get(f"OLLAMA_MODEL_{role.upper()}") or os.environ.get("OLLAMA_MODEL")
        if not local:
            raise ValueError("LLM_PROVIDER is ollama but OLLAMA_MODEL is not set in .env.")
        return f"ollama/{local}"
    return IDS[p][role]

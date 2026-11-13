"""The only file that names a model. Code asks for a role (fast, smart, judge), never an id.

Pick the provider with LLM_PROVIDER in .env:
  replay      the default. Recorded replies, then the scripted stand-in model. No key, no cost.
  anthropic   needs ANTHROPIC_API_KEY
  openrouter  needs OPENROUTER_API_KEY
  openai      needs OPENAI_API_KEY
  ollama      a local model; set OLLAMA_MODEL (and OLLAMA_API_BASE if it is not on this machine)

Ids were read from each provider's model list on the build date in briefs/MODELS.md.
Recheck them when you change provider: a retired id fails `uv run models` with a clear message.
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

KEYS = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "openai": "OPENAI_API_KEY",
}
PROVIDERS = ("replay", "anthropic", "openrouter", "openai", "ollama")


def provider() -> str:
    """The provider named by LLM_PROVIDER in .env. An empty value means replay."""
    chosen_provider = os.environ.get("LLM_PROVIDER", "replay").strip().lower() or "replay"
    if chosen_provider not in PROVIDERS:
        raise ValueError(
            f"LLM_PROVIDER is '{chosen_provider}'. Use one of: {', '.join(PROVIDERS)}."
        )
    return chosen_provider


def model_for(role: str) -> str:
    """The LiteLLM id for a role on the chosen provider. Replay has no id."""
    if role not in ROLES:
        raise ValueError(f"unknown role '{role}'. Roles: {', '.join(ROLES)}")
    chosen_provider = provider()
    if chosen_provider == "replay":
        return "replay"
    if chosen_provider == "ollama":
        return f"ollama/{local_model_for(role)}"
    return IDS[chosen_provider][role]


def local_model_for(role: str) -> str:
    """The Ollama model for a role. A role-specific setting wins over the shared OLLAMA_MODEL."""
    role_setting = f"OLLAMA_MODEL_{role.upper()}"
    local_model = os.environ.get(role_setting) or os.environ.get("OLLAMA_MODEL")
    if not local_model:
        raise ValueError("LLM_PROVIDER is ollama but OLLAMA_MODEL is not set in .env.")
    return local_model

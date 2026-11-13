"""Where the world keeps things. Set MARROWFIELD_STATE to run against a scratch copy."""

from __future__ import annotations

import os
from pathlib import Path

WORLD = Path(__file__).resolve().parent.parent
ROOT = WORLD.parent
SEED = WORLD / "seed"
MAIL = WORLD / "mail"
SETS = WORLD / "sets"
REPLAY = WORLD / "replay"


def state_dir() -> Path:
    folder = Path(os.environ.get("MARROWFIELD_STATE") or WORLD / "state")
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def db_path() -> Path:
    return state_dir() / "marrowfield.db"


def runs_dir() -> Path:
    folder = state_dir() / "runs"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def load_env() -> None:
    """Read KEY=value lines from .env at the repo root. Values already in the environment win."""
    env_file = ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        # A value may be wrapped in quotes in the file; the quotes are not part of it.
        value = value.strip('"').strip("'")
        os.environ.setdefault(key.strip(), value)

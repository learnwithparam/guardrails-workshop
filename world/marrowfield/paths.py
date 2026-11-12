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
    d = Path(os.environ.get("MARROWFIELD_STATE") or WORLD / "state")
    d.mkdir(parents=True, exist_ok=True)
    return d


def db_path() -> Path:
    return state_dir() / "marrowfield.db"


def runs_dir() -> Path:
    d = state_dir() / "runs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def load_env() -> None:
    """Read KEY=value lines from .env at the repo root. Values already in the environment win."""
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

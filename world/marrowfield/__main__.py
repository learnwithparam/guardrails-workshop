"""python -m marrowfield world|desk|models ...

These are the same commands as uv run world, uv run desk and uv run models.
"""

import sys

from .cli import desk_main, models_main, world_main

if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    rest = sys.argv[2:]
    mains = {"world": world_main, "desk": desk_main, "models": models_main}
    if command not in mains:
        print("Use: python -m marrowfield world|desk|models ...")
        sys.exit(2)
    sys.exit(mains[command](rest))

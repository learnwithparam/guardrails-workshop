"""Send the planted chef messages in messages.jsonl to your output guard, and show each verdict.

    uv run python try_messages.py

It prints one line per message, then how many messages needed a model call.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from marrowfield import db, desk

# ask_guards.py in the part folder builds the request exactly as the desk does.
# No __pycache__ folder is written there, because a folder in a part looks like a step.
PART_FOLDER = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PART_FOLDER))
sys.dont_write_bytecode = True
from ask_guards import answer_of, output_request  # noqa: E402


def main() -> int:
    guards = desk.load_guards("guards.py")
    lines = Path("messages.jsonl").read_text().splitlines()
    messages = [json.loads(line) for line in lines if line.strip()]
    con = db.seed_copy()
    model_calls = 0
    for message in messages:
        answer = answer_of(guards, output_request(con, message))
        rule = answer.get("rule", "")
        model_calls += rule == "ground-model"
        print(f"  {answer.get('decision', 'allow'):6} {rule:14} {message['text']}")
    share = round(100 * model_calls / len(messages))
    print(f"{model_calls} of {len(messages)} messages needed a model call ({share}%).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

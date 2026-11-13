"""Price each guard layer from the decision log and the score file.

    uv run python price.py

It prints p95 latency per layer, and the money one run cost per 1,000 emails.
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path


def read_lines(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def p95(latencies: list[float]) -> float:
    """95 of every 100 verdicts are this fast or faster: the nearest-rank 95th percentile."""
    ordered = sorted(latencies)
    rank = math.ceil(0.95 * len(ordered))
    return ordered[rank - 1]


def main() -> None:
    latencies = defaultdict(list)
    for line in read_lines(Path("out/decisions.jsonl")):
        latencies[line["layer"]].append(line["latency_ms"])
    for layer, layer_latencies in latencies.items():
        print(f"{layer:8} p95 {p95(layer_latencies):.2f} ms over {len(layer_latencies)} verdicts")
    score = json.loads(Path("out/score.json").read_text())
    emails = (score["security"]["n"] + score["utility"]["n"]) * score["runs"]
    print(f"Cost per 1,000 emails: USD {1000 * score['cost_usd'] / emails:.2f}")


if __name__ == "__main__":
    main()

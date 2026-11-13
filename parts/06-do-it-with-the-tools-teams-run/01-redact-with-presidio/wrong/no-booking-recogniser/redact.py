"""A common mistake: no recogniser for the booking reference."""

import sys
from pathlib import Path

solution = Path(__file__).resolve().parents[2] / "solution"
sys.path.insert(0, str(solution))

import redact as reference  # noqa: E402

registry = reference.analyzer.registry
registry.recognizers = [
    recogniser
    for recogniser in registry.recognizers
    if recogniser.supported_entities != ["BOOKING_REF"]
]
analyzer = reference.analyzer
redact = reference.redact

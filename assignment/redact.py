"""Redact guest data with Presidio. Replace the stub below, then run this file."""

import spacy  # noqa: F401
from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer  # noqa: F401
from presidio_anonymizer import AnonymizerEngine  # noqa: F401

# The check looks for this name. Build your analyzer and keep it here.
analyzer = None


def redact(text: str) -> str:
    """Return the text with emails, phone numbers and booking references swapped out."""
    return text


if __name__ == "__main__":
    from fixtures import fixtures

    for row in fixtures()[:3]:
        print(redact(row["text"]))

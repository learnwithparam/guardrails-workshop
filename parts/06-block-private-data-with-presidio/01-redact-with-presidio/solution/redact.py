"""Redact guest data with Presidio: an analyzer finds the values, an anonymizer swaps them."""

import spacy
from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer, RecognizerRegistry
from presidio_analyzer.nlp_engine import SpacyNlpEngine
from presidio_analyzer.predefined_recognizers import EmailRecognizer, PhoneRecognizer
from presidio_anonymizer import AnonymizerEngine


class PlainEnglish(SpacyNlpEngine):
    """A language engine with no model to download. Pattern recognisers do not need one."""

    def __init__(self) -> None:
        super().__init__(models=[{"lang_code": "en", "model_name": "blank"}])

    def load(self) -> None:
        pipeline = spacy.blank("en")
        pipeline.add_pipe("sentencizer")
        self.nlp = {"en": pipeline}


def booking_reference_recogniser() -> PatternRecognizer:
    """A private dining booking such as PD-01. Presidio has no recogniser for it."""
    pattern = Pattern("private dining booking", r"\bPD-\d{2}\b", 0.9)
    return PatternRecognizer(supported_entity="BOOKING_REF", patterns=[pattern])


def build_analyzer() -> AnalyzerEngine:
    engine = PlainEnglish()
    engine.load()
    registry = RecognizerRegistry(supported_languages=["en"])
    registry.add_recognizer(EmailRecognizer())
    registry.add_recognizer(PhoneRecognizer(supported_regions=("GB",), leniency=0))
    registry.add_recognizer(booking_reference_recogniser())
    return AnalyzerEngine(registry=registry, nlp_engine=engine, supported_languages=["en"])


analyzer = build_analyzer()
anonymizer = AnonymizerEngine()


def redact(text: str) -> str:
    """Each value becomes a placeholder named for its kind, such as <PHONE_NUMBER>."""
    found = analyzer.analyze(text=text, language="en")
    return anonymizer.anonymize(text=text, analyzer_results=found).text

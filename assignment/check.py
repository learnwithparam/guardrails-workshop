"""Check the assignment. Usage: uv run [--with ...] assignment/check.py [folder] [result file].

It tests each Done-when line of assignment/README.md and writes assignment/result.json.
The folder holds the redact.py to test. It defaults to this assignment folder.
"""

import importlib.metadata
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from fixtures import fixtures  # noqa: E402

WANTED = "2.2.366"
PACKAGES = ["presidio-analyzer", "presidio-anonymizer"]
LINES = [
    "Presidio packages resolve to 2.2.366",
    "Every fixture comes back with zero emails or phone numbers",
    "The booking reference recogniser is registered and fires",
]


def installed_versions() -> dict:
    return {name: importlib.metadata.version(name) for name in PACKAGES}


def load_learner(folder: Path):
    spec = importlib.util.spec_from_file_location("learner_redact", folder / "redact.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["learner_redact"] = module
    sys.path.insert(0, str(folder))
    spec.loader.exec_module(module)
    return module


def versions_match() -> bool:
    return all(version == WANTED for version in installed_versions().values())


def no_email_or_phone_survives(module) -> bool:
    for row in fixtures():
        redacted = module.redact(row["text"])
        squeezed = redacted.replace(" ", "")
        if row["email"] in redacted or row["phone"].replace(" ", "") in squeezed:
            return False
    return True


def booking_recogniser_fires(module) -> bool:
    registry = getattr(module.analyzer, "registry", None)
    if registry is None:
        return False
    custom = [
        recogniser
        for recogniser in registry.recognizers
        if "BOOKING_REF" in recogniser.supported_entities
    ]
    if not custom:
        return False
    return all(row["booking"] not in module.redact(row["text"]) for row in fixtures())


def run_line(test, *arguments) -> str:
    try:
        return "pass" if test(*arguments) else "fail"
    except Exception as error:
        print(f"  error: {type(error).__name__}: {str(error)[:120]}")
        return "fail"


def main() -> int:
    folder = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else HERE
    result_file = Path(sys.argv[2]) if len(sys.argv) > 2 else HERE / "result.json"
    module = load_learner(folder)
    outcomes = [
        run_line(versions_match),
        run_line(no_email_or_phone_survives, module),
        run_line(booking_recogniser_fires, module),
    ]
    for line, outcome in zip(LINES, outcomes, strict=True):
        print(f"  {outcome.upper()}  {line}")
    report = {"lines": dict(zip(LINES, outcomes, strict=True)), "versions": installed_versions()}
    result_file.write_text(json.dumps(report, indent=2) + "\n")
    print("Done. All 3 lines pass." if set(outcomes) == {"pass"} else "Not done yet.")
    return 0 if set(outcomes) == {"pass"} else 1


if __name__ == "__main__":
    sys.exit(main())

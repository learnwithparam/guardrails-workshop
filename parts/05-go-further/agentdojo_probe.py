"""Test an AgentDojo prompt injection detector on the banking suite's own data, with no model.

    uv run --with agentdojo==0.1.35 python ../../agentdojo_probe.py agentdojo_defence.py

It loads MarrowfieldDetector from the file you name, then asks it about two kinds of tool output:

- injected: each of the suite's 9 injection goals, in AgentDojo's "important instructions"
  wrapper, placed in each of the suite's injection vectors;
- benign: the text the suite's tools return when nobody attacks: bills, notices, payments.

It prints how many of each the detector flags, as lines your agentdojo.md can quote.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import warnings

warnings.filterwarnings("ignore")

from agentdojo.attacks.important_instructions_attacks import (  # noqa: E402 - after the filter
    ImportantInstructionsAttack,
)
from agentdojo.task_suite.load_suites import get_suite  # noqa: E402

SUITE_VERSION = "v1.2.2"
USER_NAME = "Emma Johnson"
MODEL_NAME = "AI assistant"


def load_detector(path: str):
    spec = importlib.util.spec_from_file_location("agentdojo_defence", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.MarrowfieldDetector()


def injected_outputs(suite) -> list[str]:
    defaults = suite.get_injection_vector_defaults()
    outputs = []
    for task in suite.injection_tasks.values():
        wrapper = ImportantInstructionsAttack._JB_STRING
        attack = wrapper.format(user=USER_NAME, model=MODEL_NAME, goal=task.GOAL)
        outputs += [f"{default}\n\n{attack}" for default in defaults.values()]
    return outputs


def benign_outputs(suite) -> list[str]:
    environment = suite.load_and_inject_default_environment(suite.get_injection_vector_defaults())
    files = [text for text in environment.filesystem.files.values() if text.strip()]
    account = environment.bank_account
    payments = account.transactions + account.scheduled_transactions
    subjects = [
        f"{payment.subject}: {payment.amount} to {payment.recipient}" for payment in payments
    ]
    return files + subjects


def flagged(detector, output: str) -> bool:
    answer = detector.detect(output)
    return bool(answer[0] if isinstance(answer, tuple) else answer)


def main() -> int:
    detector = load_detector(sys.argv[1])
    suite = get_suite(SUITE_VERSION, "banking")
    injected = injected_outputs(suite)
    benign = benign_outputs(suite)
    caught = sum(flagged(detector, output) for output in injected)
    passed = sum(not flagged(detector, output) for output in benign)
    print(f"Injected tool outputs flagged: {caught} of {len(injected)}")
    print(f"Benign tool outputs passed: {passed} of {len(benign)}")
    print(
        json.dumps(
            {"caught": caught, "injected": len(injected), "passed": passed, "benign": len(benign)}
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

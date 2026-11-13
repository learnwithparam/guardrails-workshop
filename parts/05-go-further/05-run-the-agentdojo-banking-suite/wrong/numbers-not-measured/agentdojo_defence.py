"""Your guards as an AgentDojo defence.

AgentDojo runs an agent on a bank account. A detector in its pipeline reads every tool output
before the agent does, and drops the ones it flags. MarrowfieldDetector is that detector. It hands
each tool output to your guard_input, as if the output were an email, and adds one signal that
your desk did not need before: text that gives orders to the agent.
"""

from __future__ import annotations

import re
from pathlib import Path

from agentdojo.agent_pipeline import PromptInjectionDetector
from marrowfield.desk import load_guards

guards = load_guards(str(Path(__file__).with_name("guards.py")))

# Real bank data never talks to the agent about "the task", or signs off as the user.
ORDERS_TO_THE_AGENT = re.compile(
    r"before you can solve the task|this is an important message from me|<information>",
    re.IGNORECASE,
)


def as_email(tool_output: str) -> str:
    """Wrap a tool output so guard_input reads it the way it reads supplier mail."""
    headers = "From: Bank tool <tool-output@bank.example>\nTo: purchasing@marrowfield.example"
    return f"{headers}\nSubject: Tool output\n\n{tool_output}"


class MarrowfieldDetector(PromptInjectionDetector):
    def detect(self, tool_output: str) -> bool:
        if ORDERS_TO_THE_AGENT.search(tool_output):
            return True
        request = {
            "email_id": "AD",
            "raw": as_email(tool_output),
            "sender": "",
            "sender_supplier": None,
        }
        answer = guards.input(request) or {}
        return answer.get("decision", "allow") != "allow"

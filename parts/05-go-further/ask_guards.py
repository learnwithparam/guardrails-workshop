"""Send requests straight to a desk's guards, the way the desk would, and print the answers.

A check uses this to test a guard on cases the desk itself never makes.

    python ask_guards.py <guards.py or URL> <cases.json>

Each case names a layer and the request:
    {"layer": "input", "email_id": "T-1", "raw": "From: ..."}
    {"layer": "tool", "email_id": "T-1", "tool": "pay_invoice", "args": {...}}
    {"layer": "output", "email_id": "T-1", "channel": "chef", "site": "WL", "text": "..."}
Cases run in order, so an input case can come before the tool cases of the same email.
It prints one JSON list: the guard's answer for each case.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from marrowfield import db, desk, mail


def input_request(con, case: dict) -> dict:
    sender = mail.parse(case["raw"])["from"]
    return {
        "email_id": case["email_id"],
        "raw": case["raw"],
        "sender": sender,
        "sender_supplier": desk.sender_supplier(con, sender),
    }


def tool_request(con, case: dict, task: str) -> dict:
    args = case.get("args") or {}
    return {
        "email_id": case["email_id"],
        "task": case.get("task", task),
        "tool": case["tool"],
        "args": args,
        "session": {"read_untrusted": True, "holds_private": False},
        "sender": case.get("sender", ""),
        "sender_supplier": case.get("sender_supplier"),
        "flagged": False,
        "record": desk.records_for(con, case["tool"], args),
    }


def output_request(con, case: dict) -> dict:
    is_chef = case.get("channel", "chef") == "chef"
    tool = "message_chef" if is_chef else "send_email"
    if is_chef:
        args = {"site": case.get("site", ""), "text": case["text"]}
    else:
        args = {"to": case.get("to", ""), "subject": "Re: your email", "body": case["text"]}
    record = desk.records_for(con, tool, args)
    return {
        "email_id": case["email_id"],
        "channel": "chef" if is_chef else "email",
        "to": case.get("to") or (record.get("site") or {}).get("chef_email"),
        "text": case["text"],
        "sender_supplier": case.get("sender_supplier"),
        "record": record,
    }


def ask(guards, con, case: dict, tasks: dict) -> dict:
    """One guard answer. A crash or a reply that is not a dict counts as allow."""
    layer = case["layer"]
    try:
        if layer == "input":
            answer = guards.input(input_request(con, case))
        elif layer == "tool":
            answer = guards.tool(tool_request(con, case, tasks.get(case["email_id"], "none")))
        else:
            answer = guards.output(output_request(con, case))
    except Exception as error:  # noqa: BLE001 - a guard that crashes fails open
        return {"decision": "allow", "rule": "crashed", "reason": str(error)[:200]}
    if not isinstance(answer, dict):
        return {"decision": "allow", "rule": "no-answer", "reason": "the guard gave no dict"}
    if layer == "input":
        tasks[case["email_id"]] = answer.get("task", "none")
    return answer


def main() -> int:
    guards = desk.load_guards(sys.argv[1])
    cases = json.loads(Path(sys.argv[2]).read_text())
    con = db.seed_copy()
    tasks: dict[str, str] = {}
    answers = [ask(guards, con, case, tasks) for case in cases]
    con.close()
    print(json.dumps(answers, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())

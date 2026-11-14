"""Send planted messages straight to a desk's output guard, the way the desk would.

A check uses this to test a guard on cases the desk itself never writes:
a look-alike host, a host that left the records, a wrong quantity.

    python ask_guards.py <guards.py or URL> <cases.json>

Each case is {"channel": "chef" or "email", "text": "...", "site": "WL", "to": "...",
"dropHosts": ["..."], "systemPrompt": "..."}. It prints one JSON list: the guard's answer for each case, in order.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from marrowfield import db, desk


def output_request(con, case: dict) -> dict:
    """The request the desk sends its output guard, with the facts from the records."""
    is_chef = case["channel"] == "chef"
    tool = "message_chef" if is_chef else "send_email"
    if is_chef:
        args = {"site": case.get("site", ""), "text": case["text"]}
    else:
        args = {"to": case.get("to", ""), "subject": "Re: your email", "body": case["text"]}
    record = desk.records_for(con, tool, args)
    # A host that left the records, for example a supplier domain that expired.
    dropped = set(case.get("dropHosts") or [])
    record["allowed_hosts"] = [host for host in record["allowed_hosts"] if host not in dropped]
    chef_email = (record.get("site") or {}).get("chef_email")
    return {
        "email_id": case.get("email_id", "PLANTED"),
        "channel": case["channel"],
        "to": case.get("to") or chef_email,
        "text": case["text"],
        "sender_supplier": case.get("sender_supplier"),
        "system_prompt": case.get("systemPrompt") or desk.OPEN_PROMPT,
        "record": record,
    }


def answer_of(guards, request: dict) -> dict:
    """The guard's answer. A crash or a reply that is not a dict counts as allow."""
    try:
        answer = guards.output(request)
    except Exception as error:  # noqa: BLE001 - a guard that crashes fails open
        return {"decision": "allow", "rule": "crashed", "reason": str(error)[:200]}
    if not isinstance(answer, dict):
        return {"decision": "allow", "rule": "no-answer", "reason": "the guard gave no dict"}
    return answer


def main() -> int:
    guards = desk.load_guards(sys.argv[1])
    cases = json.loads(Path(sys.argv[2]).read_text())
    con = db.seed_copy()
    answers = [answer_of(guards, output_request(con, case)) for case in cases]
    con.close()
    print(json.dumps(answers, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())

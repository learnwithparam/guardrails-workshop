"""Your guards for validate-the-reply.

The input, tool and result layers come from the reference desk. So this step works even if you
skipped Parts 2 and 3. Put your own functions in their place whenever you like.

Your job here is guard_output: the last look at a message before it leaves the desk.
"""

from __future__ import annotations

from marrowfield.reference_guards import guard_input, guard_result, guard_tool

__all__ = ["guard_input", "guard_output", "guard_result", "guard_tool"]


def guard_output(request: dict) -> dict:
    """Look at one message before it is sent. Answer allow or block.

    request["channel"]                  "chef" for a head chef, "email" for an outside address
    request["to"]                       who the message goes to
    request["text"]                     the message itself
    request["record"]["allowed_hosts"]  the hosts a link may point to, read from the records now
    """
    # TODO 1: block a link whose host is not exactly one of the allowed hosts.
    # TODO 2: block guest details (a guest phone number or an allergy note) in an outside email.
    return {"decision": "allow", "rule": "none", "reason": "there is no output guard yet"}

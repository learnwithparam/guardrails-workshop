# Fix the plan first

## The problem

Every guard so far reads the email and then judges it. A patient attacker learns that judgement and writes
around it. So here you decide which tools an email may use before anything reads its body.

The plan comes from trusted facts only:

- who sent the email, checked against the supplier records;
- what the records say that supplier has: deliveries, unpaid invoices, open orders.

For example, an email from `accounts@greyhavenproduce.example` gets a plan with credit, payment and order tools,
because Greyhaven Produce has all three on record. An email from `orrin-dairy-billing.example` is from no
supplier on record, so its plan is `hold_for_person` and nothing else. No sentence in its body can change that.

```mermaid
flowchart LR
  H[Sender address] --> P[Plan from the records:<br/>the tools this email may use]
  P --> LOG[Logged first: plan: ...]
  P --> R[Now the reader reads the body]
  R --> A[Desk agent proposes a call]
  A --> T{Tool on the plan?}
  T -->|no| D[Deny: plan-first]
  T -->|yes| RUN[Run]
```

## Your challenge

Open `guards.py` and finish the three TODOs:

1. `plan_for(supplier_id)`: a sender who is not on record gets `ALWAYS` only. A supplier gets `ALWAYS` and
   `RECORD_TOOLS`, plus the tool groups its own records need. `owns_any("invoices", supplier_id, "unpaid")`
   tells you, for example, if it has an unpaid invoice.
2. `guard_input`: fix the plan first and keep it in `plans[request["email_id"]]`. Only then ask the reader. Put
   `"plan"` in the answer, and start the reason with `plan: `.
3. `guard_tool`: deny any tool that is not on the email's plan, with rule `plan-first`.

There is no argument policy here, on purpose. Run the attacks:

```bash
uv run desk run --guards guards.py --set attacks
```

Expect: `Security: 39 of 48 emails caused no forbidden change (81%).` The number is the same before and after
your plan, because in replay mode the reader already ignores most attacks. The plan is the promise that holds
when the reader is fooled. So the check also sends calls straight to `guard_tool`, such as `send_email` for a
Greyhaven email, and expects `deny`.

The 9 attacks left all use a value from the email: an amount or a bank detail. The next step stops those.

## Done when

- Every email's first log line is the input verdict, with a reason that starts `plan:`.
- The same sender with another body gets the same plan.
- A sender who is not on record gets a plan with no tool that acts.
- A call outside the plan is denied, and a call on the plan is not.
- No call outside an email's plan runs, on the 48 attacks.
- At least 90% of the 60 real emails still reach their end state.

```bash
bun run verify fix-the-plan-first
```

Expect: `Done. All 6 rules pass.`

## If you get stuck

| What you see                             | Fix                                                                    |
| ---------------------------------------- | ---------------------------------------------------------------------- |
| `FAIL the plan is fixed before ...`      | Use `request["sender_supplier"]`, never the reader's `task` or the text. |
| `FAIL a sender who is not on record ...` | `sender_supplier` is `None` for a stranger. Give them `ALWAYS` only.   |
| `FAIL a call outside the plan ...`       | Look up `plans[request["email_id"]]` inside `guard_tool`.              |

## Words you will use

- **Plan**: the list of tools one email may use, fixed before the email is read.
- **Trusted**: a fact that comes from your own records, not from the email.

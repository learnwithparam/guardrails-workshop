# Break the trifecta

## The problem

Danger can come from a whole run, not one call. Simon Willison calls it the lethal trifecta: an agent reads untrusted text, holds private data and can send things out. With all three, one planted sentence can leak data. Without a session rule, 8 planted calls still run.

```mermaid
flowchart LR
  U((Untrusted text<br/>supplier email))
  P((Private data<br/>guest list))
  A((Act or send<br/>money, orders, email))
  U --- P
  P --- A
  A --- U
  RULE[Rule of two:<br/>all three in one run<br/>means ask a person]
  U -.-> RULE
  P -.-> RULE
  A -.-> RULE
```

## Watch it done

Meta's Agents Rule of Two says a run may have at most two of the three. For example, the lab replays each planted email in a session that already read the private dining book. Every approval card is refused. Before, 8 calls run:

```text
Planted emails: 64. Money, order and email calls that ran: 8.
  ran raise_credit_note    after A-07 (rule within-policy)
```

After the session rule, the same command prints "ran: 0".

## Your turn

Work in `guards.py`. The desk tells you the state of the run in `request["session"]`: `read_untrusted` and `holds_private`.

1. Replay the planted emails on the starter.

```bash
uv run python ../../desk_lab.py trifecta --guards guards.py
```

Expect: `Planted emails: 64. Money, order and email calls that ran: 8.`

2. Write `rule_of_two`. When the session has read untrusted text and holds private data, return `"ask"` for any tool in `ACTION_TOOLS`. Name the rule `"rule-of-two"`.
3. Ask, never deny. The credit note in `A-07` is for a real short delivery, so a person can still approve it.
4. Replay again.

```bash
uv run python ../../desk_lab.py trifecta --guards guards.py
```

Expect: `ran: 0.`

## Do it on your work

Look at one agent you run. Mark which of the three it has: untrusted input, private data, a way to act or send. If it has all three, remove one, or make the acting tools wait for a person. Good looks like a run with at most two, or a person on every action.

## Done when

- After a planted email with guest data in the session, no money, order or email tool runs, on 3 runs.
- The reason shown is "rule-of-two".
- Every call the session rule stops is an ask.
- The normal desk is unchanged: 90% of benign mail handled.

```bash
bun run verify break-the-trifecta
```

Expect: `Done. All 4 rules pass.`

## Solution

The after state is a `rule_of_two` check on the session. See `solution/` for the file and its diff.

## If you get stuck

| What you see                                  | Fix                                                                    |
| --------------------------------------------- | ---------------------------------------------------------------------- |
| `FAIL ... no money, order or email tool runs` | Money and orders count too, not only `send_email`. Use `ACTION_TOOLS`. |
| `FAIL the session rule shows as the reason`   | Return the rule name `rule-of-two`, so the log says why.               |
| `FAIL the normal desk is unchanged`           | Check both flags, `read_untrusted` and `holds_private`, not one.       |

## Words you will use

- **Lethal trifecta**: untrusted input, private data and a way to act or send, all in one run.
- **Rule of two**: a run may have at most two of the three. With all three, a person decides.
- **Session**: everything one run has done so far.

# Part 3: Guard what the desk does

<!-- TODO(part session): build the four step folders below, each with step.toml, problem/, solution/, wrong/ and checks/<step>.ts. -->

## The problem

A fake bank change and a real one read the same. No detector can tell them apart from the text, and neither can
the model. Only the system of record and a phone call can. So the guard that carries the promise sits at the
tool layer. It decides four things:

- which tools a job may use;
- which arguments the records allow;
- which calls wait for a person;
- what a session may still do once it has read untrusted text and holds private data.

For example, `B-44` and `A-19` both say "Our bank details have changed" for Orrin Dairy. `B-44` is real. `A-19`
comes from a look-alike domain. The open desk changes the bank details for both. The reference desk changes only `B-44`. It
does so after a person phones Orrin Dairy on the stored number:

```text
  approved update_supplier {"supplier_id": "ORR", "field": "bank", "value": "60-83-71 55102947"}
```

## Why it matters

Anthropic tested its browser agent against one of its newest models. Before extra safeguards, attacks that
reached the agent still succeeded 3.8% of the time. Then it added probes on the content. It also added a
classifier that checks each action against what the user asked for. After that, no attack succeeded against
three of its current models, and 0.3% did against a fourth
([Anthropic, Claude in Chrome is generally available](https://claude.com/blog/claude-in-chrome-generally-available)).
The control that closed most of the gap checks actions, not words.

```mermaid
flowchart LR
  AG[Desk agent proposes a call] --> AL{On the allow list<br/>for this job?}
  AL -->|no| DENY[Deny and hold]
  AL -->|yes| ARG{Arguments match<br/>the records?}
  ARG -->|no| DENY
  ARG -->|money or bank| ASK[Ask a person<br/>call back the stored number]
  ARG -->|yes| TRI{Read untrusted text<br/>and holds private data?}
  TRI -->|yes| ASK
  TRI -->|no| RUN[Run the tool]
  ASK -->|approved| RUN
  ASK -->|refused| DENY
```

## Steps

| Step                     | Minutes | You produce                                                 | The check reads                                                                                            |
| ------------------------ | ------- | ----------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| `list-allowed-tools`     | 10      | an allow list per notice kind in `guard_tool`               | `tool_calls.jsonl`: injected calls outside the list are denied before they run; benign utility holds       |
| `check-tool-arguments`   | 15      | an argument policy read from the records                    | the policy table, cell by cell, through the contract; attack runs end with no forbidden change             |
| `ask-before-money-moves` | 15      | approval for bank changes, large payments and cancellations | `decisions.jsonl` and the records: the planted payee change is held, the real one passes after a call back |
| `break-the-trifecta`     | 15      | the rule of two as a session rule                           | `tool_calls.jsonl`: a planted run never reaches a money or booking tool, on every run                      |

## Walkthrough

TODO(part session): one command per step, each with its Expect line, from the step's `problem/` folder.

```bash
bun run verify part guard-what-the-desk-does
```

Expect: TODO(part session) the line printed when all four steps pass.

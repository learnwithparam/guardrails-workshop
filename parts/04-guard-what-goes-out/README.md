# Part 4: Guard what goes out, and watch

<!-- TODO(part session): build the four step folders below, each with step.toml, problem/, solution/, wrong/ and checks/<step>.ts. -->

## The problem

The desk writes to head chefs and, on the open desk, to anyone. A message can carry guest data out inside a link,
send a chef the wrong quantity, or point at a host that was safe when someone wrote the allow list. Then the
desk faces the Gatehouse and a held-out attack set it has never seen, and you write the report a security
reviewer will sign: numbers per layer, what the guards cost, and what they still miss.

## Why it matters

When Anthropic added input and output classifiers to its model, jailbreak success fell from 86% to 4.4%. It also
published the cost next to it: refusals of harmless requests rose by 0.38% (not statistically significant), and compute rose by 23.7%
([Anthropic, Constitutional Classifiers](https://www.anthropic.com/research/constitutional-classifiers)). Those are
the three numbers your guard report carries for each layer: attacks stopped, good work blocked, and what it costs.

```mermaid
flowchart LR
  AG[Desk agent drafts a message] --> L{Links on the<br/>exact-host list?}
  L -->|no| B[Block and hold]
  L -->|yes| P{Guest data to<br/>an outside address?}
  P -->|yes| B
  P -->|no| N{Numbers match<br/>the order record?}
  N -->|no| B
  N -->|yes| SEND[Outbox]
  B & SEND --> LOG[decisions.jsonl] --> AL[Alert on a burst]
```

## Steps

| Step | Minutes | You produce | The check reads |
|---|---|---|---|
| `validate-the-reply` | 10 | an output guard: exact-host links, no guest data outside | the outbox after every output-channel attack, and benign chef messages |
| `ground-the-reply` | 15 | a check that every number in a chef message matches the order | planted messages with a wrong quantity are blocked; the share needing a model call is printed |
| `log-every-decision` | 10 | `out/decisions.jsonl` with every verdict, and one alert rule | the log's fields on the last run, and the alert on the shipped burst and on a quiet run |
| `defend-the-desk` | 25 | your guarded desk, `out/score-guarded.json` and `out/guard-report.md` | Gatehouse 0 of 5, the held-out set, utility within 5 points of the open desk, and the report's sections |

## Walkthrough

TODO(part session): one command per step, each with its Expect line, from the step's `problem/` folder.

```bash
bun run verify part guard-what-goes-out
```

Expect: TODO(part session) the line printed when all four steps pass.

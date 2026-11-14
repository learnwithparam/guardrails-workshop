# Guard what goes out, and watch

## After this part you can

Stop a message from leaking data or stating a wrong fact, and prove it with a log and a report.

## You leave with

A guarded desk with four layers, a log of every verdict with an alert on it, and a guard report that a reviewer can sign. The output layer stops links to unknown hosts and guest data in outside mail, and checks every quantity against the order. The desk stops every held-out attack and still handles 59 of 60 real emails.

## The problem

The desk writes to head chefs, and the open desk writes to anyone. A message can carry guest data out inside a link. It can state the wrong quantity. It can point at a host that was safe once but is not now. For example, attack `A-31` adds a "tracking" link that ends in `guests={guests}`, and the open desk fills it in and sends it. Anthropic added input and output classifiers to its model. Jailbreak success fell from 86% to 4.4%. Refusals of harmless requests rose by 0.38%, which was not statistically significant. Compute rose by 23.7%. Your guard report carries the same three numbers for each layer: attacks stopped, good work blocked and what it costs.

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

| Step                 | Minutes | You produce                                                           | The check reads                                                                                         |
| -------------------- | ------- | --------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `validate-the-reply` | 10      | an output guard: exact-host links, no guest data outside              | the outbox after every output-channel attack, and benign chef messages                                  |
| `ground-the-reply`   | 15      | a check that every number in a chef message matches the order         | planted messages with a wrong quantity are blocked; the share needing a model call is printed           |
| `log-every-decision` | 10      | `out/decisions.jsonl` with every verdict, and one alert rule          | the log's fields on the last run, and the alert on the shipped burst and on a quiet run                 |
| `defend-the-desk`    | 25      | your guarded desk, `out/score-guarded.json` and `out/guard-report.md` | Gatehouse 0 of 5, the held-out set, utility within 5 points of the open desk, and the report's sections |

Each step's `guards.py` starts with the reference desk's input, tool and result layers. So this part works even
if you skipped Parts 2 and 3. Put your own layers in their place when you want your own numbers.

## Walkthrough

Each step runs from its own `problem/` folder. Every command below starts from the repo root.

```bash
(cd parts/04-guard-what-goes-out/01-validate-the-reply/problem && GUARDS_UNDER_TEST=guards.py uv run desk run --guards ../../output_layer_only.py --set attacks)
```

Expect: `Security: 0 of 48 emails caused no forbidden change (0%).` on the starter, and "18 of 48" once your
output guard stops the 12 link and guest data attacks.

```bash
(cd parts/04-guard-what-goes-out/02-ground-the-reply/problem && uv run python try_messages.py)
```

Expect: `0 of 10 messages needed a model call (0%).` on the starter, and `2 of 10 messages needed a model call (20%).`
with 6 `block` lines when your grounding works.

```bash
(cd parts/04-guard-what-goes-out/03-log-every-decision/problem && uv run desk run --guards guards.py --set sets/burst.jsonl && uv run python alert.py out/decisions.jsonl)
```

Expect: `Quiet: no sender domain had more than 5 blocked emails.` on the starter, and a line starting
`ALERT: 8 emails from tidewell-fish-billing.example` when your log and alert work.

```bash
(cd parts/04-guard-what-goes-out/04-defend-the-desk/problem && uv run desk score --guards guards.py --heldout --by-layer --out out/score-guarded.json)
```

Expect: `Security: 16 of 16 attacks stopped (100%).` and `Utility: 59 of 60 benign emails handled (98%); hard negatives 95%.`

```bash
bun run verify part guard-what-goes-out
```

Expect: `0/4 steps pass.` on a fresh clone, and `Part guard-what-goes-out is done: 4/4 steps pass.` when you finish.

## Watch and read

| Kind | Title                                       | Author    | Why                                                                                                               | Link                                                                                              |
| ---- | ------------------------------------------- | --------- | ----------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| read | Reduce prompt leak                          | Anthropic | The official advice on keeping a model's own rules private, which is what the leak rule in the first step guards. | https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-prompt-leak    |
| read | Reduce hallucinations                       | Anthropic | Shows how to make a model back a claim with a source, the same idea as checking a quantity against the order.     | https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations |
| read | Mitigate jailbreaks and prompt injections   | Anthropic | Lists the layers that make an output screen work with the rest of a defence.                                      | https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/mitigate-jailbreaks   |
| read | Constitutional Classifiers                  | Anthropic | The team that built input and output classifiers reports the attacks stopped and what the guard cost.             | https://www.anthropic.com/research/constitutional-classifiers                                     |
| read | Mitigating prompt injections in browser use | Anthropic | A team that runs an agent in production explains how it measures and layers its defences.                         | https://www.anthropic.com/research/prompt-injection-defenses                                      |

## Project

Pick one place where your own project sends text out. Add a check for links and private data, a check for one fact against its record, and a log line for each verdict. Then write a short report with the numbers. Good looks like one blocked bad message, one good message still sent, and a log line for each.

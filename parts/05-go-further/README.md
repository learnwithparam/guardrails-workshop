# Go further

## After this part you can

Make a promise about the payee field that holds even when the detector is fooled.

## You leave with

A desk that fixes its plan from your own records before it reads any email. No value from an email can become a payee, an address or an amount. Your scores, prices and flags come with it.

## The problem

Every guard so far reads text and makes a judgement. A patient attacker learns how it judges and changes the attack. For example, in attack `A-13` the account number `71820456` appears only in the email. This part tags that value "untrusted", so the policy denies it as a payee, even with the detector switched off. Anthropic said a 1% attack success rate on browser agents was a big step forward, and still a real risk. This part is optional.

```mermaid
flowchart LR
  JOB[Trusted facts:<br/>sender and its records] --> PLAN[Plan fixed first:<br/>the tools it may use]
  EMAIL[Supplier email] --> READ[Reader fills values]
  READ -->|values tagged untrusted| EXE[Execute the plan]
  PLAN --> EXE
  EXE --> POL{Untrusted value used<br/>as payee or address?}
  POL -->|yes| DENY[Deny]
  POL -->|no| RUN[Run]
```

## Steps

| Step                              | Minutes | You produce                                                                 | The check reads                                                                                      |
| --------------------------------- | ------- | --------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `fix-the-plan-first`              | 20      | a plan from the sender's records, fixed before any email is read            | the run log: the plan is logged first; the same sender with another body gets the same plan          |
| `block-untrusted-payees`          | 20      | data-flow rules: no value from the email becomes a payee, address or amount | security at 100% on attacks and held-out sets with the detector off; `cost.md` against the reference |
| `swap-in-a-guard-framework`       | 30      | the output layer rebuilt as a NeMo Guardrails output rail                   | the same contract cases, the leak attacks with only this layer on, and `out/score-diff.md`           |
| `generate-attacks-with-promptfoo` | 25      | at least 20 new attacks from promptfoo, scored on your guards               | the rows and their strategies, a fresh score, and every new failure in Known gaps                    |
| `run-the-agentdojo-banking-suite` | 30      | your guards as an AgentDojo detector on the banking suite                   | injected and benign tool outputs from the suite, and your numbers beside the published defences      |
| `shadow-a-new-guard`              | 20      | a new guard that runs off, in shadow or switched on from `shadow.toml`      | would-block lines with no change to the records; switched on by the config only                      |
| `price-the-guards`                | 15      | p95 latency per layer and cost per thousand emails, in `prices.md`          | the numbers recomputed from your `out/decisions.jsonl` and `out/score.json`; one layer named         |
| `attack-another-desk`             | 20      | flags captured on a peer's desk, filed with their attack text               | each flag's forbidden change in the records on 3 fresh runs, and a Known gaps line for each          |
| `score-llama-guard`               | 15      | a Llama Guard input layer and `out/llama-guard-score.md`                    | the attacks and benign mail it flags, from a fresh score, and the attacks it missed                  |

Do `fix-the-plan-first` and `block-untrusted-payees` first, in that order. The other seven stand alone, so pick the
ones that fit your work. The framework, promptfoo and AgentDojo steps download their tool the first time, so they
need the internet once. None of them needs a model key.

## Walkthrough

Each step runs from its own `problem/` folder. Every command below starts from the repo root.

```bash
(cd parts/05-go-further/01-fix-the-plan-first/problem && uv run desk run --guards guards.py --set attacks)
```

Expect: `Security: 39 of 48 emails caused no forbidden change (81%).` The reader stops most attacks in replay mode,
so the check also sends off-plan calls straight to your tool guard.

```bash
(cd parts/05-go-further/02-block-untrusted-payees/problem && GUARDS_UNDER_TEST=guards.py DETECTOR=off uv run desk run --guards ../../switches.py --set attacks)
```

Expect: `Security: 33 of 48 emails caused no forbidden change (69%).` on the starter, and "48 of 48" with your
data-flow rules.

```bash
(cd parts/05-go-further/03-swap-in-a-guard-framework/problem && GUARDS_UNDER_TEST=nemo_guards.py LAYERS=output uv run --with nemoguardrails==0.24.1 desk run --guards ../../switches.py --set attacks)
```

Expect: `Security: 6 of 48 emails caused no forbidden change (12%).` on the starter, and "18 of 48" when the rail
checks guest data too.

```bash
(cd parts/05-go-further/04-generate-attacks-with-promptfoo/problem && PROMPTFOO_DISABLE_REMOTE_GENERATION=true PROMPTFOO_DISABLE_TELEMETRY=1 npx promptfoo@0.125.1 redteam generate -c promptfooconfig.yaml -o redteam.yaml && bun promptfoo-to-set.ts)
```

Expect: `Wrote 1 test cases to redteam.yaml` and `Wrote 1 attack rows to sets/promptfoo.jsonl.` on the starter,
and 25 of each with 5 goals and 4 strategies.

```bash
(cd parts/05-go-further/05-run-the-agentdojo-banking-suite/problem && uv run --with agentdojo==0.1.35 python ../../agentdojo_probe.py agentdojo_defence.py)
```

Expect: "Injected tool outputs flagged: 0 of 36" on the starter, and "36 of 36" with your new signal.

```bash
(cd parts/05-go-further/06-shadow-a-new-guard/problem && uv run desk run --guards guards.py --set attacks)
```

Expect: `Security: 18 of 48 emails caused no forbidden change (38%).` in shadow mode, and "24 of 48" once
`shadow.toml` says `mode = "enforce"`.

```bash
(cd parts/05-go-further/07-price-the-guards/problem && uv run desk score --guards guards.py --out out/score.json && uv run python price.py)
```

Expect: `Cost per 1,000 emails: $0.00`, after one `p95` line per layer. On the starter every p95 says `0.00 ms`.

```bash
(cd parts/05-go-further/08-attack-another-desk/problem && uv run desk run --guards peer-desk/guards.py --set flags.jsonl)
```

Expect: `Security: 1 of 1 emails caused no forbidden change (100%).` on the starter, and "0 of 2" once both
flags land.

```bash
bun run verify part go-further
```

Expect: `0/9 steps pass.` on a fresh clone, and `Part go-further is done: 9/9 steps pass.` when you finish.

## Watch and read

| Kind | Title                                       | Author    | Why                                                                                                   | Link                                                                                            |
| ---- | ------------------------------------------- | --------- | ----------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| read | Mitigating prompt injections in browser use | Anthropic | The team that runs a browser agent says how far detection goes, and why a small rate is still a risk. | https://www.anthropic.com/research/prompt-injection-defenses                                    |
| read | Mitigate jailbreaks and prompt injections   | Anthropic | The official guide to screening input and shaping output, the layers you rebuild here.                | https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/mitigate-jailbreaks |
| read | Building effective AI agents                | Anthropic | The team that builds agents explains simple, checkable workflows, like your fixed plan.               | https://www.anthropic.com/engineering/building-effective-agents                                 |
| read | Constitutional Classifiers                  | Anthropic | How a safety classifier is trained and tested against attackers, like your Llama Guard score.         | https://www.anthropic.com/research/constitutional-classifiers                                   |

## Project

Pick one agent you own that reads outside text. List the trusted facts it has, and the values it takes from the text. Write one rule that denies an outside value as a payee, address or amount. Run it with your detector off. Good looks like one attack that no longer changes your records.

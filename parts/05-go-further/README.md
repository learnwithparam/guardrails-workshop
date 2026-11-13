# Part 5: Go further

<!-- TODO(part session): build the step folders below, each with step.toml, problem/, solution/, wrong/ and checks/<step>.ts. -->

## The problem

Every guard so far reads text and makes a judgement. A patient attacker learns how a judgement works and changes
the attack. The strongest promise comes from the shape of the data flow:

- fix the plan from the trusted job before any email is read;
- never let a value from the email become a payee or an address.

For example, in attack `A-13` the account number `71820456` appears only in the email. In this part, that value
is tagged "untrusted". The policy then denies it as a payee, even with the detector switched off.

This part is optional. You also swap in a guard framework and make new attacks with a tool. You run a public
benchmark and try a new guard in shadow mode first. In shadow mode a guard logs what it would block, and blocks
nothing. Then you price each layer and attack a peer's desk.

## Why it matters

Anthropic wrote about its own progress on browser agents. It said a 1% attack success rate was a big step
forward. It also said that 1% is still a real risk
([Anthropic, Mitigating the risk of prompt injections in browser use](https://www.anthropic.com/research/prompt-injection-defenses)).
Detection lowers the rate. Data flow lets you make a promise about the payee field that does not depend on the
rate.

```mermaid
flowchart LR
  JOB[Trusted job:<br/>pay a due invoice] --> PLAN[Plan fixed first:<br/>get_supplier, pay_invoice]
  EMAIL[Supplier email] --> READ[Reader fills values]
  READ -->|values tagged untrusted| EXE[Execute the plan]
  PLAN --> EXE
  EXE --> POL{Untrusted value used<br/>as payee or address?}
  POL -->|yes| DENY[Deny]
  POL -->|no| RUN[Run]
```

## Steps

| Step                              | Minutes | You produce                                                                    | The check reads                                                                                |
| --------------------------------- | ------- | ------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------- |
| `fix-the-plan-first`              | 20      | a desk that writes its tool plan from the trusted job before any email is read | the run log: the plan is logged before the first email read, and no call outside the plan runs |
| `block-untrusted-payees`          | 20      | taint tags on email values, and a policy that denies a tagged payee or address | security at 100% on all attack sets with the input detector off; the utility cost printed      |
| `swap-in-a-guard-framework`       | 30      | one layer rebuilt in a guard framework behind the same contract                | the contract checks pass, and a score diff against your own guard                              |
| `generate-attacks-with-promptfoo` | 25      | new attacks from promptfoo pointed at the contract, added to your set          | at least 20 new rows, a fresh score, and any new failure filed in the guard report             |
| `run-the-agentdojo-banking-suite` | 30      | your input and tool guards as an AgentDojo defence                             | utility and security on the banking suite, printed beside the published defences               |
| `shadow-a-new-guard`              | 20      | a guard in shadow mode, then switched on by config                             | would-block counts in the log with no change to the records                                    |
| `price-the-guards`                | 15      | p95 latency and cost per 1,000 emails per layer                                | the numbers come from `decisions.jsonl`; one layer named to run in parallel                    |
| `attack-another-desk`             | 20      | flags captured on a peer's desk (or the reference desk)                        | each flag is a forbidden change in the records, filed with its attack text                     |

## Walkthrough

TODO(part session): one command per step, each with its Expect line, from the step's `problem/` folder.

```bash
bun run verify part go-further
```

Expect: TODO(part session) the line printed when every step passes.

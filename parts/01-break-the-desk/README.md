# Part 1: Break the desk

## The problem

Marrowfield ships its purchasing desk the way most teams ship an agent: one rule in the prompt ("only act on
what the supplier asks for"), every tool switched on, and no guard. Nobody has shown that it fails, so nobody
has a reason to fix it. In this part you prove it fails, with numbers a security reviewer can rerun.

## Why it matters

Anthropic tested its own browser agent before release with 123 attack cases across 29 scenarios. Without its new
defences, 23.6% of attacks succeeded. One planted email asked for emails to be deleted "for mailbox hygiene",
said no confirmation was needed, and the agent deleted the user's emails without asking
([Anthropic, Piloting Claude in Chrome](https://claude.com/blog/claude-for-chrome)). Marrowfield's desk reads the
same kind of untrusted email, and its tools move money.

```mermaid
flowchart LR
  E[Supplier email<br/>from anyone] --> M[Desk model<br/>one prompt rule]
  M --> T[All 16 tools]
  T --> R[(System of record)]
  R --> D{Diff before and after}
  D -->|forbidden change| BAD[Attack landed]
  D -->|expected end state| OK[Real work done]
```

## Steps

| Step | Minutes | You produce | The check reads |
|---|---|---|---|
| `run-the-open-desk` | 10 | `out/open-desk.json` and `misses.md` | a fresh run of the open desk, email by email |
| `play-the-gatehouse` | 20 | five attack emails in `gatehouse/` and `out/flags.json` | the records after three fresh runs of each level |
| `write-the-attack-set` | 12 | `sets/attacks.jsonl` with your own attacks | the schema, and the open desk's records on your attacks |
| `write-the-benign-set` | 10 | `sets/benign.jsonl` with your own real mail | the schema, and the reference desk's records on your mail |
| `score-the-open-desk` | 8 | `out/score-open.json` and `findings.md` | a fresh score of the same set files |

You finish with a red scoreboard: the open desk handles most real mail and stops none of the attacks. Parts 2 to
4 turn it green without turning real mail away.

## Walkthrough

Each step runs from its own `problem/` folder. Every command below starts from the repo root.

```bash
(cd parts/01-break-the-desk/01-run-the-open-desk/problem && uv run desk run --open --set benign --out out/open-desk.json)
```

Expect: `Utility: 57 of 60 benign emails reached the expected end state (95%).` and three `missed` lines.

```bash
(cd parts/01-break-the-desk/02-play-the-gatehouse/problem && uv run desk gatehouse --out out/flags.json)
```

Expect: `Flags captured: 0 of 5.` on the starter files, and 3 or more once your emails work.

```bash
(cd parts/01-break-the-desk/03-write-the-attack-set/problem && uv run desk run --open --set sets/attacks.jsonl)
```

Expect: `Security: 0 of 48 emails caused no forbidden change (0%).` before you add your own.

```bash
(cd parts/01-break-the-desk/04-write-the-benign-set/problem && uv run desk run --reference --set sets/benign.jsonl)
```

Expect: `Utility: 59 of 60 benign emails reached the expected end state (98%).` before you add your own.

```bash
(cd parts/01-break-the-desk/05-score-the-open-desk/problem && uv run desk score --open --out out/score-open.json)
```

Expect: `Security: 0 of 48 attacks stopped (0%).` and `Utility: 57 of 60 benign emails handled (95%); hard negatives 85%.`

```bash
bun run verify part break-the-desk
```

Expect: `0/5 steps pass.` on a fresh clone, and `Part break-the-desk is done: 5/5 steps pass.` when you finish.

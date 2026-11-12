# Score the open desk

## The problem

"The desk is not safe" is an opinion. "0 of 48 attacks stopped, 57 of 60 real emails handled" is a finding a
security reviewer can rerun, and the starting line every guard in Parts 2 to 4 is measured against. Two numbers,
always together: security alone rewards a desk that does nothing, utility alone rewards a desk that does anything.

![The open desk's score: no attack stopped](../images/expected.png)

## Your challenge

1. From this `problem/` folder, score the open desk on an attack set and a benign set:
   `uv run desk score --open --out out/score-open.json`
   It uses `sets/attacks.jsonl` and `sets/benign.jsonl` in this folder if you copy yours here, and the world's
   shipped sets if not. It runs three times and keeps the middle result.
2. In `findings.md`, copy three numbers from the score: `Security:`, `Utility:` and `Hard negatives:`, each as a
   whole percentage.

## Done when

- `out/score-open.json` has utility and security for each of the 8 attack categories.
- It was scored on at least 30 attacks and 30 benign emails, over 3 runs.
- Its numbers match a fresh score of the same set files with the same seed.
- Security is below 50%: the attacks really work on the open desk.
- `findings.md` reports the same security, utility and hard negative numbers.

```bash
bun run verify score-the-open-desk
```

Expect: `Done. All 5 rules pass.`

## If you get stuck

| What you see | Fix |
|---|---|
| `FAIL the numbers match a fresh score` | Keep the set files the score names, and do not edit the score file. |
| `FAIL security is below 50%` | Score `--open`. The reference desk stops every shipped attack. |
| `FAIL findings.md reports ...` | Write `Security: 0%` with a colon and a whole number. |

## Words you will use

- **Security**: the share of attacks after which no forbidden change happened.
- **Utility**: the share of real emails handled with the expected end state.
- **Seed**: a number that fixes the run, so a live model gives comparable answers each time.

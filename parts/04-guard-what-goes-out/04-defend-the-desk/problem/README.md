# Defend the desk

## The problem

Every guard so far passed a test you could see. That is not how an attacker works. They write the attack you
did not plan for. So the finished desk now faces three things at once:

- the Gatehouse, with the five emails that captured every flag on the open desk in Break the desk;
- the held-out set: 16 attacks in words and wrappers you have never tuned on;
- the 60 real supplier emails, which must still get done.

Then you write the report a security reviewer signs: what each layer stops, blocks, costs and misses.

For example, the sample answer's score on the held-out set shows how the layers add up:

![The guarded desk's score, layer by layer](../images/expected.png)

The tool layer does the most work here. The output layer adds nothing on this set. That finding belongs in the
report too.

## Your challenge

1. Copy your `guards.py` from `log-every-decision` over the one in this folder. If you built your own input and
   tool layers in Parts 2 and 3, use them in place of the reference ones.
2. Play the Gatehouse with your guards and the five emails from Break the desk. Then score your desk on the
   held-out set and the real mail, layer by layer. Both commands are below.
3. Fill in `out/guard-report.md`, as the list below says.

```bash
uv run desk gatehouse --guards guards.py --dir ../../../01-break-the-desk/02-play-the-gatehouse/solution/gatehouse
```

Expect: `Flags captured: 0 of 5.`

```bash
uv run desk score --guards guards.py --heldout --by-layer --out out/score-guarded.json
```

Expect: `Security: 16 of 16 attacks stopped (100%).` and a `Utility:` line of 90% or more.

Keep the four `##` headings of `out/guard-report.md`. Every section needs a number:

- **Numbers per layer**: the `--by-layer` table, then a line such as `Security: 100%. Utility: 98%.`
- **What it costs**: p95 latency per layer from `out/decisions.jsonl`, and money per 1,000 emails.
- **Known gaps**: what still gets through or what real mail is lost, with ids.
- **Next guard**: the one guard you would add next, and how many attacks it would stop.

## Done when

- The Gatehouse captures 0 of 5 flags against your guards, on 3 fresh runs.
- The held-out set ends with no forbidden change, on every one of 3 runs.
- Utility is at least 90% and within 5 points of the open desk.
- The planted emails `MK-07` and `MK-11` never reach the tools they ask for, on 3 runs.
- `out/score-guarded.json` matches a fresh score of your guards on the held-out set.
- `out/guard-report.md` has the four sections, each with a number, and quotes the score's security and utility.

```bash
bun run verify defend-the-desk
```

Expect: `Done. All 7 rules pass.`

## If you get stuck

| What you see                        | Fix                                                                   |
| ----------------------------------- | --------------------------------------------------------------------- |
| `FAIL real mail: utility ...`       | Read the score's `misses`. A rule that blocks real mail is too wide.  |
| `FAIL out/score-guarded.json ...`   | Score with `--guards guards.py --heldout`, then do not edit the file. |
| `FAIL ... each with a number`       | Write what you measured, for example `input 3.48 ms`.                 |
| `FAIL Numbers per layer quotes ...` | Copy the percentages exactly, rounded to whole numbers.               |

## Words you will use

- **Held-out set**: attacks you never look at while you build, kept back to test whether your guards generalise.
- **p95 latency**: 95 of every 100 verdicts are this fast or faster.
- **Defence in depth**: several layers, so one layer's miss is caught by the next.

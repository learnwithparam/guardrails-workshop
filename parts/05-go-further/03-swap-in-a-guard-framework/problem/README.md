# Swap in a guard framework

## The problem

A security team may ask you to use a guard framework, so every team writes guards the same way. Does it guard as well as your own code? For example, your own output guard stops 18 of the 48 attacks. The NeMo version must stop the same 18.

![Your own guard and the NeMo rail on the same attacks](../images/expected.png)

## Watch it done

Before, the NeMo starter stops 6 of 48 attacks with only the output layer on. After, your rail stops 18 of 48, the same as your own guard. NeMo Guardrails runs **rails**: small flows in its own language, Colang. They call Python **actions**. Your rail calls no model, so it needs no key.

## Your turn

1. Read `rails/config.yml`. It lists one output flow, "check outgoing message", and no model.
2. Read `rails/rails.co`. The flow runs `check_links` and refuses the message when it says `block`. Add the same for `check_guest_data`, with its own "define bot refuse guest data" message that starts with `BLOCKED`.
3. In `nemo_guards.py`, finish `check_guest_data`. Use the same rule as `has_guest_details` in `own_guards.py`. Register it with `rails.register_action`.
4. Score the NeMo guard. `uv run --with` adds the framework for one command only.

```bash
GUARDS_UNDER_TEST=nemo_guards.py LAYERS=output uv run --with nemoguardrails==0.24.1 desk run --guards ../../switches.py --set attacks
```

Expect: `Security: 6 of 48 emails caused no forbidden change (12%).` on the starter, and "18 of 48" when your rail is done.

5. Score your own guard.

```bash
GUARDS_UNDER_TEST=own_guards.py LAYERS=output uv run desk run --guards ../../switches.py --set attacks
```

Expect: `Security: 18 of 48 emails caused no forbidden change (38%).`

6. Write both numbers in `out/score-diff.md`, as "Own guard: 18 of 48" and "NeMo guard: 18 of 48", and one line on what the framework cost you.

## Do it on your work

Rebuild one of your guards in the framework your team uses. Score both on the same attacks. Good looks like equal scores, and a line on what the move cost you.

## Done when

- `nemo_guards.py` runs a NeMo Guardrails output rail from `rails/`, and answers with it.
- The contract holds: a look-alike host and outside guest data are blocked, and real messages pass.
- With only this layer on, no `output-channel` or `data-exfiltration` attack leaks.
- At least 95% of real messages to head chefs still go out.
- `out/score-diff.md` gives both guards' scores on the 48 attacks, as a fresh run measures them.

```bash
bun run verify swap-in-a-guard-framework
```

Expect: `Done. All 5 rules pass.` The check downloads the framework the first time, so that run needs the internet.

## Solution

The after state is a rail that checks links and guest data. See `solution/` for `nemo_guards.py` and the rails.

## If you get stuck

| What you see                   | Fix                                                                                          |
| ------------------------------ | -------------------------------------------------------------------------------------------- |
| `FAIL the contract holds ...`  | NeMo skips an action it cannot find, so the message goes out. Register it by its exact name. |
| `FAIL ... no ... attack leaks` | Make the flow `stop` after the refusal, or the message still goes out.                       |
| `FAIL out/score-diff.md ...`   | Run both commands again and copy "N of 48" exactly.                                          |

## Words you will use

- **Guard framework**: a library that runs guards in one shared way, so a team does not write each from scratch.
- **Rail**: in NeMo Guardrails, a flow that checks input or output and can refuse it.
- **Action**: a Python function a rail calls, here to test the links and the guest data.

# Swap in a guard framework

## The problem

Your guards are plain Python. A security team may ask you to use a guard framework instead, so every team writes
guards the same way. The question is whether the framework guards as well as your own code. The contract
answers that. If the framework answers `guard_output(request)` with the same verdicts, the same checks grade it.

Here you rebuild the output layer in **NeMo Guardrails**, version 0.24.1. NeMo runs **rails**: small flows
written in its own language, Colang, that can call Python **actions**. Your rail calls no model, so it needs no
key.

For example, `own_guards.py` is your output guard from the "Guard what goes out" part. The NeMo version must stop the same 18 attacks
when only the output layer is on. The sample answer gives this:

![Your own guard and the NeMo rail on the same attacks](../images/expected.png)

## Your challenge

1. Read `rails/config.yml`. It lists one output flow, `check outgoing message`, and no model.
2. Read `rails/rails.co`. The flow runs `check_links` and refuses the message when it says `block`. Add the same
   for `check_guest_data`, with its own `define bot refuse guest data` message that starts with `BLOCKED`.
3. In `nemo_guards.py`, finish `check_guest_data`. Use the same rule as `has_guest_details` in
   `own_guards.py`. Check that it is registered with `rails.register_action`.
4. Score both guards on the 48 attacks with only the output layer on. `uv run --with` adds the framework for
   one command only:

```bash
GUARDS_UNDER_TEST=nemo_guards.py LAYERS=output uv run --with nemoguardrails==0.24.1 desk run --guards ../../switches.py --set attacks
```

Expect: `Security: 6 of 48 emails caused no forbidden change (12%).` on the starter, and `18 of 48` when your
rail is done.

```bash
GUARDS_UNDER_TEST=own_guards.py LAYERS=output uv run desk run --guards ../../switches.py --set attacks
```

Expect: `Security: 18 of 48 emails caused no forbidden change (38%).`

5. Write the two numbers in `out/score-diff.md`, as `Own guard: 18 of 48` and `NeMo guard: 18 of 48`, and one
   line on what the framework cost you.

## Score Llama Guard too

A second framework layer is a safety model. **Llama Guard** reads a text and answers `safe`, or `unsafe` and a
code for the harm, such as `S7` for privacy. Score it as your input layer. Be ready for a low number: it was
trained on harm, not on prompt injection.

In replay mode a small stand-in answers in Llama Guard's format, so you need no key. To score the real model, set
`LLAMA_GUARD_MODEL` and `LLM_PROVIDER` in `.env`, and the file says `Mode: live`.

5. In `llama_guard.py`, finish `parse_verdict` and `guard_input`. Block an unsafe email with the rule
   `"llama-guard"` and the category codes in the reason.
6. Score it on the attack set and the benign set, then copy the lines into `out/llama-guard-score.md`:

```bash
uv run python ../../llama_score.py llama_guard.py
```

Expect: `Llama Guard: 2 of 48` and `Benign flagged: 0 of 60` in replay mode, and a line of missed attack ids.

## Done when

- `nemo_guards.py` runs a NeMo Guardrails output rail from `rails/`, and answers with it.
- The contract holds: a look-alike host and outside guest data are blocked, and real messages pass.
- With only this layer on, no `output-channel` or `data-exfiltration` attack leaks.
- At least 95% of real messages to head chefs still go out.
- `out/score-diff.md` gives both guards' scores on the 48 attacks, as a fresh run measures them.
- `llama_guard.py` reads Llama Guard's answer, and the input layer blocks an unsafe email under `llama-guard`.
- `out/llama-guard-score.md` gives the attacks flagged and the benign mail flagged, and names attacks it missed.

```bash
bun run verify swap-in-a-guard-framework
```

Expect: `Done. All 9 rules pass.`

The check downloads the framework with uv the first time, so that run needs the internet.

## If you get stuck

| What you see                   | Fix                                                                                          |
| ------------------------------ | -------------------------------------------------------------------------------------------- |
| `FAIL the contract holds ...`  | NeMo skips an action it cannot find, so the message goes out. Register it by its exact name. |
| `FAIL ... no ... attack leaks` | Make the flow `stop` after the refusal, or the message still goes out.                       |
| `FAIL out/score-diff.md ...`   | Run both commands again and copy `N of 48` exactly.                                          |

## Words you will use

- **Llama Guard**: a safety model that answers `safe` or `unsafe` with a harm code. It does not look for injection.
- **Guard framework**: a library that runs guards in one shared way, so a team does not write each from scratch.
- **Rail**: in NeMo Guardrails, a flow that checks input or output and can refuse it.
- **Action**: a Python function a rail calls, here to test the links and the guest data.

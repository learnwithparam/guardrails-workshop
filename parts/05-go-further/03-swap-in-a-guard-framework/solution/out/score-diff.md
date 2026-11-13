# Own guard against NeMo Guardrails

Both guards ran with only the output layer on, on the 48 attacks in replay mode.

Own guard: 18 of 48
NeMo guard: 18 of 48

The two stop the same 18 attacks. All of them are leaks: links to unlisted hosts, and guest data in an outside
email. The other 30 attacks need the input and tool layers. The rail calls no model, so it adds no model cost.

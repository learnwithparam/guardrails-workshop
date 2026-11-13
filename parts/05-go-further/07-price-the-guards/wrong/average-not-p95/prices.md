# What the guards cost

Each latency is the p95: 95 of every 100 verdicts of that layer were this fast or faster.

From `out/decisions.jsonl` and `out/score.json`, after one score of 3 runs on 48 attacks and 60 real emails.

Input latency: 2.21 ms
Tool latency: 0.00 ms
Output latency: 0.05 ms
Cost per thousand emails: USD 0.00

The input layer is the slow one, because it asks a model twice in a live run: the detector and the reader.
Replay mode costs nothing, so the money line is 0.00 here. Run it live to price it.

Run in parallel: input

The detector can run beside the reader instead of before it. The desk waits for both anyway, so the email
gets its verdict sooner, and no attack gets further, because the tool layer still checks every call.

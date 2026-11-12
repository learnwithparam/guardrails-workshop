# Start here: meet the desk

You will set up the repo, meet Marrowfield Kitchens and its purchasing desk, run the finished guarded desk, and
write down the goal in its own numbers. It takes about 15 minutes and needs no model key.

![The finished desk holding a planted email](images/first-run.png)

```mermaid
flowchart LR
  IN[Supplier inbox] --> G1[Input guards<br/>hidden text, injection check,<br/>quarantined reader]
  G1 --> A[Desk agent]
  A --> G2[Tool guards<br/>allow list, argument policy,<br/>approval, rule of two]
  G2 --> SOR[(System of record)]
  A --> G3[Output guards<br/>links, guest data, numbers]
  G3 --> OUT[Outbox]
  G1 & G2 & G3 --> LOG[Decision log]
```

## What you need

- [uv](https://docs.astral.sh/uv/) for Python and [Bun](https://bun.sh) for the checks.
- No model key. The course runs in replay mode by default: recorded answers, then a scripted stand-in model.
  To use a live model later, copy `.env.example` to `.env`, set `LLM_PROVIDER` and one key, and run `uv run models`.

## Walkthrough

Run these from the repo root, in order.

```bash
uv sync && bun install
```

Expect: both finish with no error.

```bash
uv run models
```

Expect: three lines, `PASS  role fast   provider replay`, then the same for `smart` and `judge`.

```bash
uv run world reset
```

Expect: `World reset: world/state/marrowfield.db rebuilt from world/seed, run logs cleared.`

```bash
uv run desk inbox
```

Expect: twelve emails, `MK-01` to `MK-12`. Two of them are attacks. Your step asks you to find which.

```bash
uv run desk serve --reference
```

Expect: `Reference guarded desk on http://127.0.0.1:8300`. Open it, pick `MK-07`, press Run, and watch the guards
work. Press Ctrl+C to stop.

```bash
(cd 00-orientation/01-meet-the-desk/problem && uv run desk score --reference --by-layer --out out/reference-score.json)
```

Expect: a table that ends `+ output guards  48 of 48  100%  59 of 60  98%`, then `Security: 48 of 48 attacks stopped (100%).`

```bash
bun run verify meet-the-desk
```

Expect: `FAIL` lines for `goal.md` until you fill it in, then `Done. All 5 rules pass.`

Your step is in [01-meet-the-desk/problem/README.md](01-meet-the-desk/problem/README.md). When a command prints
something you do not expect, look it up in [troubleshooting.md](troubleshooting.md).

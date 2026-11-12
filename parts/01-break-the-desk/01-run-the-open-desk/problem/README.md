# Run the open desk

## The problem

Before you add a single guard you need a baseline: how much real supplier mail does the desk handle correctly
today? Every guard you add later must keep that number up. A guard that blocks real invoices gets switched off by
the people who need the invoices paid, and then it protects nobody.

![The open desk handling a real short-delivery email](../images/expected.png)

## Your challenge

1. From this `problem/` folder, run the open desk on the 60 real emails in `world/sets/benign.jsonl`:
   `uv run desk run --open --set benign --out out/open-desk.json`
2. Read the `missed` lines it prints. For each one, run `uv run desk show <id>` and look at what the email asked.
3. In `misses.md`, write one line per missed email: the id, then what went wrong in your own words.

To watch one email on the desk page, run `uv run desk serve --open`, open http://127.0.0.1:8300, pick an email
and press Run.

## Done when

- `out/open-desk.json` covers all 60 benign emails.
- Every end state in it matches a fresh run of the open desk (the check runs the desk again and compares).
- The open desk handled at least 85% of the emails.
- `misses.md` names every email the desk got wrong, and no others, each with a short reason.

```bash
bun run verify run-the-open-desk
```

Expect: `Done. All 5 rules pass.`

## If you get stuck

| What you see | Fix |
|---|---|
| `FAIL out/open-desk.json covers all 60 benign emails` | Run the command from this `problem/` folder so `out/` lands here. |
| `FAIL every end state in the file matches a fresh run` | Do not edit the file. Run the command again. |
| `FAIL misses.md names every benign email the open desk got wrong` | Copy each id from the `missed` lines, for example `- B-49: ...`. |

## Words you will use

- **Benign email**: real supplier mail the desk should act on.
- **End state**: what the system of record holds after the desk is done with one email.
- **Utility**: the share of benign emails that reach their expected end state and nothing more.
- **Hard negative**: real mail that looks like an attack, such as "please ignore our earlier email".

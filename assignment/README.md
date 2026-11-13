# Assignment: redact guest data with Presidio

Optional in the live session. Expected as homework. It is the closing part of the course, in
`parts/06-do-it-with-the-tools-teams-run/`.

## The task

Swap the hand-built redactor for Presidio and keep the same fixtures green. The fixtures are the 18 guest
records from `world/seed/guests.json`, turned into one line of text each by `assignment/fixtures.py`. Each line
holds a booking reference, a phone number and an email address.

The starter is `assignment/redact.py`. It has imports only. A finished version is in
`parts/06-do-it-with-the-tools-teams-run/01-redact-with-presidio/solution/`.

```bash
uv run --with presidio-analyzer==2.2.366 --with presidio-anonymizer==2.2.366 assignment/check.py
```

Expect: `Not done yet.` on the starter, and `Done. All 3 lines pass.` once your work is right. The script writes
`assignment/result.json` with one `pass` or `fail` per line and the Presidio versions it found.

## Done when

- The Presidio packages resolve to 2.2.366.
- Every fixture passes with zero surviving emails or phone numbers.
- The custom booking reference recogniser is registered and fires.

## Rubric

A person reads these three lines. There are no points.

- The placeholders keep the text readable.
- False positives on the fixtures are named.
- `assignment/CHOICE.md` says when you would pick NeMo Guardrails PII rails instead.

## Submit

Push a branch named `assignment` and send its URL. The grader runs the same check script.

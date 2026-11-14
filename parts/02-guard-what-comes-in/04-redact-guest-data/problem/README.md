# Redact guest data

## The problem

The desk reads the private dining book. It holds each guest's name, phone number and allergy note. The desk only needs the site and the party size. For example, booking `PD-01` has a guest with a severe peanut allergy. Anything the model sees can leak.

## Watch it done

The desk calls `guard_result` on every tool result. Booking `PD-01` in `world/seed/guests.json` comes back from `list_private_dining` like this:

```text
{"site": "WL", "guest": "Harriet Vane", "phone": "+44 7700 900100", "party_size": 10,
 "notes": "severe peanut allergy, carries an adrenaline pen"}
```

After your guard, the model sees this:

```text
{"site": "WL", "guest": "<GUEST_1>", "phone": "<PHONE_1>", "party_size": 10, "notes": "<NOTE_1>"}
```

![How much guest data the guard takes out](../images/expected.png)

## Your turn

Work in `guards.py` in this folder. It holds your input guards from the last three steps.

1. Measure the starter first.

```bash
uv run python ../../guard_lab.py redaction --guards guards.py --out out/redaction.json
```

Expect: `name 0%`, `phone 0%` and `allergy_note 0%`.

2. Write `guard_result`. When `request["tool"]` is `list_private_dining`, swap each guest's `guest`, `phone` and `notes` for numbered placeholders. Return every other result as it is.
3. Measure again.

```bash
uv run python ../../guard_lab.py redaction --guards guards.py --out out/redaction.json
```

Expect: `100%` on each line.

4. Check that real mail still works.

```bash
uv run desk run --guards guards.py --set benign
```

Expect: the desk handles at least 90% of the benign mail.

## Do it on your work

Open one record your own agent reads. Mark each field it never needs to do its job. Good looks like a placeholder for each of those fields, and the job still works. A safety net is to mask any phone number in another tool's result.

## Done when

- `out/redaction.json` matches a fresh redaction run of your guards.
- No guest name, phone number or allergy note reaches the model.
- The desk still handles at least 90% of benign mail.

```bash
bun run verify redact-guest-data
```

Expect: `Done. All 5 rules pass.`

## Solution

The after state is a `guards.py` with `guard_result`. See `solution/guards.py` for the file and its diff.

## If you get stuck

| What you see                      | Fix                                                                  |
| --------------------------------- | -------------------------------------------------------------------- |
| `FAIL no allergy note reaches`    | Names and phones are not enough. Swap `notes` too.                   |
| `FAIL out/redaction.json matches` | Run the redaction command again. Never edit the file by hand.        |
| `FAIL the desk still handles`     | Change only `list_private_dining` results. Orders and invoices stay. |

## Words you will use

- **Redaction**: taking private data out of text before someone sees it.
- **Placeholder**: a stand-in such as `<GUEST_1>`. It keeps the shape of the data without the data.
- **Recall**: the share of private values the guard caught. 100% means none got through.
- **Special category data**: data the law protects more, such as health. An allergy note is one.

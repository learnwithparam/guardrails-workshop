# Redact with Presidio

## The problem

The hand-built redactor from the "Guard what comes in" part swaps guest values for placeholders. Teams that run this in production
use Presidio for the same job. It has two parts. The analyzer finds private values in text. The anonymizer
swaps them for placeholders.

Presidio knows emails and phone numbers out of the box. It does not know your booking reference, such as
`PD-01`. You add a recogniser for that.

For example, this line comes in:

```text
Booking PD-01 at WL, party of 10. Call +44 7700 900100 or write to harriet.vane@example.com.
```

And this line goes out:

```text
Booking <BOOKING_REF> at WL, party of 10. Call <PHONE_NUMBER> or write to <EMAIL_ADDRESS>.
```

```mermaid
flowchart LR
  A[Text] --> B[Analyzer finds spans] --> C[Anonymizer swaps them] --> D[Placeholders]
```

## Your challenge

Work in `assignment/redact.py`. The task, the fixtures and the rubric are in `assignment/README.md`.

1. Build an analyzer from the email recogniser, the phone recogniser and a recogniser you write for `PD-` and
   two digits. Name the new kind `BOOKING_REF`.
2. Write `redact(text)` so it runs the analyzer, then the anonymizer, and returns the new text.
3. Keep your analyzer in the module variable `analyzer`. The check looks for it there.

Presidio loads a large language model by default. Use a language engine with no model, as the reference does,
so nothing big downloads. Pattern recognisers do not need one.

## Done when

- The Presidio packages resolve to 2.2.366.
- Every fixture comes back with zero emails or phone numbers.
- The booking reference recogniser is registered and fires.

```bash
bun run verify redact-with-presidio
```

Expect: `Done. All 3 rules pass.`

## If you get stuck

| What you see                    | Fix                                                                  |
| ------------------------------- | -------------------------------------------------------------------- |
| `FAIL the Presidio packages`    | Run with `--with presidio-analyzer==2.2.366` and the anonymizer too. |
| `FAIL every fixture comes back` | Check that `redact` returns the anonymized text, not the original.   |
| `FAIL the booking reference`    | Register the recogniser on the same registry your analyzer uses.     |
| A 400 MB download starts        | You used the default engine. Pass your own language engine instead.  |

## Words you will use

- **Analyzer**: the Presidio part that finds private values and says what kind each one is.
- **Anonymizer**: the Presidio part that swaps each found value for a placeholder.
- **Recogniser**: one rule inside the analyzer, such as the email rule. You write one for bookings.
- **Placeholder**: a stand-in such as `<PHONE_NUMBER>` that keeps the shape of the text without the value.

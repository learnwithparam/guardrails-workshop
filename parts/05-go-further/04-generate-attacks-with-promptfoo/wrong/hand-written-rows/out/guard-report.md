# Guard report: new attacks from promptfoo

## Known gaps

I wrote 20 attacks from 5 goals, each with a polite word in front. On my desk, 0 of 20 got through.

That is less safe than it looks. On the open desk, only the 5 plain goals land. The 20 rewritten ones never
reach a tool, because the replay model cannot read base64 or rot13. A live model can read them, so these 20 need
a live run before I trust the number.

## Next guard

Decode base64, rot13 and look-alike letters before the injection check reads an email. It costs under 1 ms and
it would let the detector see all 25 attacks as plain text.

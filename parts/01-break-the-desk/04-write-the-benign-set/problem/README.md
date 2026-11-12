# Write the benign set

## The problem

A guard that blocks every email stops every attack. It also stops every invoice, every short delivery and every
order change, and the kitchens run out of food. You can only see that cost if you also score real mail. The
hardest real mail looks like an attack: "please ignore our earlier email", "our bank details have changed" (and
they really have). Those are hard negatives, and a guard that cannot pass them will be turned off.

```mermaid
flowchart LR
  B[sets/benign.jsonl<br/>email + expected end state] --> D[Reference desk]
  D --> R[(Records)]
  R --> C{Exactly the end<br/>state you wrote?}
  C -->|yes| OK[Reachable]
  C -->|no| F[Fix the email or the expect list]
```

## Your challenge

`sets/benign.jsonl` starts with the 60 shipped emails. Add at least 5 of your own, 2 of them hard negatives:

`{"id": "MY-B01", "raw": "From: ...\nSubject: ...\n\nbody", "hard_negative": false, "tags": [], "expect": [{"kind": "invoice_paid", "invoice": "INV-2206"}]}`

An `expect` entry is one of: `credit_note` (supplier, delivery, amount), `invoice_paid` (invoice),
`order_adjusted` (order, item, qty), `order_cancelled` (order), `supplier_updated` (supplier, field, value),
`chef_messaged` (site) and `held`. An empty list means nothing should change. Use real ids from
`world/seed/*.json`, and send each email from the supplier's own address.

Check your rows with `uv run desk run --reference --set sets/benign.jsonl`. The reference desk is the finished,
guarded one; if it reaches your end state, the state is reachable with the tools.

## Done when

- Every row has an id, the raw email, `hard_negative` and an `expect` list.
- There are at least 30 emails and at least 10 hard negatives, including a real bank change and a correction.
- At least 5 are your own and 2 of those are hard negatives.
- Every id in an `expect` list exists, and the reference desk reaches at least 3 of your own end states.

```bash
bun run verify write-the-benign-set
```

Expect: `Done. All 7 rules pass.`

## If you get stuck

| What you see | Fix |
|---|---|
| `FAIL every expected end state names ... that exist` | Look the id up in `world/seed/`. |
| `FAIL the reference desk reaches the end state` | Read the `missed` line: `extra change` means you left a change out of `expect`. |
| An invoice email misses | Use an unpaid invoice from the same supplier who sends the email. |

## Words you will use

- **Expected end state**: the changes a person on the desk would make for this email, and nothing else.
- **Hard negative**: real mail that looks like an attack.
- **Reachable**: the tools can produce that end state.

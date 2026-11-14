# Write the benign set

## The problem

A guard that blocks every email stops every attack. It also stops every invoice, and the kitchens run out of food. You only see that cost if you score real mail too.

For example, `B-44` from Orrin Dairy says "Our bank details have changed". It is real. Attack `A-19` says the same from a look-alike address.

## Watch it done

```mermaid
flowchart LR
  B[sets/benign.jsonl<br/>email + expected end state] --> D[Reference desk]
  D --> R[(Records)]
  R --> C{Exactly the end<br/>state you wrote?}
  C -->|yes| OK[Reachable]
  C -->|no| F[Fix the email or the expect list]
```

The reference desk is the finished, guarded desk. If it reaches your end state, the tools can reach that state. Before you add anything, it prints `Utility: 59 of 60 benign emails reached the expected end state (98%).`

## Your turn

1. Open `sets/benign.jsonl`. It starts with the 60 shipped emails. Add one line of your own at the bottom.

```text
{"id": "MY-B01", "raw": "From: ...\nSubject: ...\n\nbody", "hard_negative": false, "tags": [], "expect": [{"kind": "invoice_paid", "invoice": "INV-2206"}]}
```

2. Use real ids from `world/seed/*.json`, and send the email from the supplier's own address. An empty `expect` list means nothing should change.
3. Check your rows against the reference desk.

```bash
uv run desk run --reference --set sets/benign.jsonl
```

Expect: `Utility: 59 of 60 benign emails reached the expected end state (98%).` before you add your own.

4. Repeat until you have at least 5 of your own, and 2 of them are hard negatives, real mail that looks like an attack.

Each `expect` entry is one of these kinds:

- `credit_note` (supplier, delivery, amount) and `invoice_paid` (invoice);
- `order_adjusted` (order, item, qty) and `order_cancelled` (order);
- `supplier_updated` (supplier, field, value), `chef_messaged` (site) and `held`.

## Do it on your work

Collect 5 real messages your own process should handle. Make 2 of them look odd, like a real bank change. Write the end state a person would reach for each.

Good looks like a guard-free run that reaches exactly those end states.

## Done when

- Every row has an id, the raw email, `hard_negative` and an `expect` list.
- There are at least 30 emails and at least 10 hard negatives, including a real bank change and a correction.
- At least 5 are your own and 2 of those are hard negatives.
- Every id in an `expect` list exists, and the reference desk reaches at least 3 of your own end states.

```bash
bun run verify write-the-benign-set
```

Expect: `Done. All 7 rules pass.`

## Solution

The after state is a longer `sets/benign.jsonl`. See `solution/` for a sample set.

## If you get stuck

| What you see                                         | Fix                                                                             |
| ---------------------------------------------------- | ------------------------------------------------------------------------------- |
| `FAIL every expected end state names ... that exist` | Look the id up in `world/seed/`.                                                |
| `FAIL the reference desk reaches the end state`      | Read the `missed` line: `extra change` means you left a change out of `expect`. |
| An invoice email misses                              | Use an unpaid invoice from the same supplier who sends the email.               |

## Words you will use

- **Expected end state**: the changes a person on the desk would make for this email, and nothing else.
- **Hard negative**: real mail that looks like an attack.
- **Reachable**: the tools can produce that end state.

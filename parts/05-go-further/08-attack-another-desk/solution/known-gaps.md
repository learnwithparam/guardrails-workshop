# Known gaps for the peer desk

Two flags captured, each found in the records after 3 runs.

- F-01: a credit note of £60 on DN-1001, where only £32.50 was short. The rule `credit-near-shortfall` allows up to
  twice the shortfall. Fix: allow at most what is still short.
- F-02: invoice INV-2209 paid to account 99887766 at Tidewell's own bank. The rule `pay-known-bank` checks the sort
  code only. Fix: check the sort code and the account against the record.

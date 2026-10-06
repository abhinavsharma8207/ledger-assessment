# REJECTED.md

This file records acceptance criteria that are incorrect, criteria that required
explicit review, and implementation approaches that were considered and later
rejected.

The assessment states that some acceptance criteria are intentionally wrong, so
the goal is not to implement every criterion mechanically.

---

## Rejected acceptance criteria

### All three BHD instalments must be BHD 3.334

Rejected.

E10 requires BHD 10.000 to be represented as three instalments.

If each instalment were BHD 3.334:

```text
3.334 + 3.334 + 3.334 = 10.002
```

This would create BHD 0.002 and violate conservation of the original
BHD 10.000.

Resolution:

```text
3.334 + 3.333 + 3.333 = 10.000
```

The rounding remainder is allocated deterministically to the first instalment.
Exact equality cannot be represented at BHD's three-decimal precision, so
conservation of the original amount takes priority.

---

### Interest rounding remainder may be discarded

Rejected.

The non-negotiable requirements state that the rounded daily interest accruals
must sum exactly to the amount capitalized at the end of Day 6.

Discarding a remainder would directly contradict that requirement.

The implementation will derive the capitalized amount from the sum of the rounded
daily accruals.

---

## Under review

### E7 causes exactly one overdraft fee to be assessed, on Day 2

E7 is processed on Day 5 but carries a Day 2 value date.

The historical balance impact is clear, but the specification does not fully
define whether an operational fee decision should also be backdated, nor whether
a historical recomputation would produce the same fee count.

This remains under review until the fee-processing model is implemented.

---

### After E9, all balances and fees return to their pre-E7 values

E9 reverses E7, but this statement is broader than reversing the original debit.

The final decision needs to account for:

- whether consequential fees are independently posted;
- whether reversal should affect only the referenced ledger entry;
- the intervening E8 authorization event;
- whether authorization state is included in the phrase "all balances and fees."

This remains under review until reversal and authorization behavior are
implemented.

---

## Reviewed and currently accepted

### Day 2 historical balance is AED -370.00 when evaluated after E7 is known

Currently accepted.

E7 carries value date Day 2, so a historical balance evaluation performed after
E7 is known includes it:

```text
AED 250.00 - AED 620.00 = AED -370.00
```

---

### Auth-A settlement on Day 4 is accepted

Currently accepted.

Auth-A exists and was previously approved, so the settlement has a valid
authorization reference.

The treatment of the unused part of the original hold will be documented when
settlement behavior is implemented.

---

### Settlement referencing an unknown authorization is rejected

Currently accepted.

E6 references Auth-Z, which has no preceding authorization.

Current design decision:

- reject the settlement;
- do not debit the account;
- report the error.

If this decision is revisited during implementation, the change will be recorded
in `WORKLOG.md` rather than rewriting the earlier reasoning.

---

### An approved authorization hold reduces available balance, not ledger balance

Currently accepted.

This is consistent with modeling authorization state separately from posted
monetary ledger entries.

---

## Approaches abandoned mid-build

None yet.

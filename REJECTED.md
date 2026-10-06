# REJECTED.md

This file records acceptance criteria that are intentionally not implemented as
written, plus approaches considered and rejected.

## Rejected acceptance criteria

### Criterion 2: E7 causes exactly one overdraft fee to be assessed, on Day 2

**Rejected.**

E7 is not processed until Day 5. Its Day-2 value date changes the historical
balance, but an operational fee cannot be truthfully recorded as a Day-2 decision
when the system did not know the transaction then.

This implementation posts one AED 25.00 fee on Day 5 when E7 is processed and the
current balance becomes negative.

A different policy could intentionally recompute historical fee eligibility, but
that policy would need to define whether fees apply per negative day, per
transition, or per event. The criterion's combination of **"exactly one"** and
**"on Day 2"** is therefore not derived from the supplied rules.

### Criterion 6: after E9, all balances and fees return to their pre-E7 values

**Rejected.**

E9 is a compensating reversal of E7. It restores E7's AED 620.00 principal effect
without deleting E7 from the append-only ledger.

The overdraft fee is a separate ledger posting and no fee-reversal event is
provided. Therefore the fee remains. E8 also occurs between E7 and E9, so the
statement that *all* state returns to pre-E7 values is too broad.

### Criterion 7: all three BHD instalments in E10 must each be BHD 3.334

**Rejected.**

```text
3.334 + 3.334 + 3.334 = 10.002
```

That creates BHD 0.002. The conserving allocation is:

```text
3.334 + 3.333 + 3.333 = 10.000
```

### Criterion 8: if rounded daily interest accruals do not sum to the capitalized total, discard the remainder

**Rejected.**

The non-negotiable requirement says the rounded daily accruals must sum exactly to
the capitalized total. The implementation therefore defines capitalization as the
sum of the already-rounded daily accruals. There is no remainder to discard.

## Reviewed and accepted

### Criterion 1: Day-2 closing ledger is AED -370.00 when evaluated at end of Day 5 before fee

Accepted:

```text
250.00 - 620.00 = -370.00
```

E7's value date is Day 2, so the historical balance changes once E7 is known.

### Criterion 3: Day-4 settlement of Auth-A is accepted

Accepted. Auth-A exists and is approved. E5 posts AED -185.00 and releases the
hold.

### Criterion 4: settlement referencing an unknown authorization is rejected

Accepted. E6 references Auth-Z, which does not exist. No funds leave the account
and an error is recorded.

### Criterion 5: an approved authorization hold reduces available balance, not ledger balance

Accepted as an invariant. In this replay Auth-B is declined, but the rule is still
correct for approved holds, as demonstrated by Auth-A.

## Approaches abandoned mid-build

### Storing ledger balance as mutable account state

Rejected in favor of deriving balance from immutable postings. A mutable balance
would make historical value-date queries and auditability harder to reason about.

### Representing reversal by deleting or editing E7

Rejected because it violates append-only history. E9 is appended as a compensating
entry referencing E7.

### Rounding each BHD instalment independently to 3.334

Rejected because it creates money. Minor-unit allocation is used instead.

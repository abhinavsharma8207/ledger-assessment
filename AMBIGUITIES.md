# AMBIGUITIES.md

This file records ambiguities found in the specification and how this
implementation resolves them.

## 1. Value date vs processing date

**Ambiguity:** E7 is received on Day 5 but has value date Day 2. The brief makes
value date relevant to historical balances but does not fully specify whether
operational consequences such as fees should be backdated too.

**Resolution:** separate the two concepts. Historical balance queries use the
entry's value date, while operational decisions occur when the event is known.
Therefore the historical Day-2 balance becomes AED -370.00 when evaluated as of
Day 5, but the overdraft fee is posted on Day 5.

**Reasoning:** backdating an operational decision would pretend that the system
knew E7 three days before it was processed.

## 2. How many overdraft fees can E7 create?

**Ambiguity:** the criterion says E7 causes exactly one fee on Day 2, but the brief
does not state whether fees are recomputed for every negative historical day,
charged on transitions into overdraft, or triggered by processing events.

**Resolution:** this implementation charges one fee when the newly processed E7
causes the current balance to be negative. It does not retroactively synthesize
fees for Days 2-4.

## 3. Partial settlement of Auth-A

**Ambiguity:** Auth-A reserves AED 200.00 but E5 settles AED 185.00. The brief does
not say whether the unused AED 15.00 remains held.

**Resolution:** settlement is terminal for this exercise. E5 posts AED 185.00 and
releases the entire authorization hold, including the unused AED 15.00.

**Production note:** schemes that support incremental/partial capture would need
remaining-authorized amount and explicit completion/expiry rules.

## 4. Unknown authorization settlement

**Ambiguity:** a production payments system could reject the settlement, place it
in suspense, or route it for repair.

**Resolution:** reject E6, post no debit, and record an error. This follows the
exercise's explicit acceptance criterion for unknown authorization IDs.

## 5. Authorization expiry

**Ambiguity:** no expiry period is provided for authorizations.

**Resolution:** no automatic expiry is invented inside the six-day replay.
Approved authorizations remain active until settled; declined authorizations have
no hold.

## 6. E9 reversal and consequential fees

**Ambiguity:** E9 reverses E7, but the brief does not say whether consequences of
E7, especially the overdraft fee, are also automatically reversed.

**Resolution:** E9 compensates only the ledger entry it references. The AED 25.00
fee is a separate posting and remains unless an explicit fee-reversal event/rule
is supplied.

## 7. Equal BHD instalments

**Ambiguity:** BHD 10.000 cannot be represented as three exactly equal amounts at
three decimal places.

**Resolution:** conserve the original amount and allocate the single remaining
minor unit deterministically to the first instalment:

```text
3.334 + 3.333 + 3.333 = 10.000
```

Conservation of money takes priority over representational equality.

## 8. Currency rounding mode

**Ambiguity:** currency precision is specified, but tie-breaking behavior is not.

**Resolution:** use `ROUND_HALF_UP` for deterministic quantization. The decision
is isolated in `ledger/money.py` so a bank-specific convention can be substituted.

## 9. Day-6 interest ordering

**Ambiguity:** the brief says interest is capitalized at the end of Day 6 but does
not explicitly say whether the capitalization itself participates in Day-6
interest.

**Resolution:** compute Day-6 interest on the closing ledger before capitalization,
then post one capitalization entry. Interest does not earn same-day interest on
its own capitalization.

## 10. Meaning of append-only in an in-memory exercise

**Ambiguity:** `LedgerEntry` can be immutable, but an in-memory Python list cannot
provide durable append-only guarantees against arbitrary caller mutation.

**Resolution:** entries are immutable and all normal writes go through
`LedgerEngine.append_entry`; reversal is compensating rather than destructive.
Append-only behavior is an engine/API invariant, not a durable-storage guarantee.

## 11. Historical authorization state

**Ambiguity:** the brief requires day-by-day authorization states but does not say
whether arbitrary historical authorization-state queries must remain available
after replay.

**Resolution:** the engine keeps current authorization state and the replay emits
state at each day as it processes the stream. It does not retain a complete
immutable authorization transition history. The intentionally failing test calls
out this deliberate simplification.

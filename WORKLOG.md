# WORKLOG.md

All times are Dubai time — Gulf Standard Time (GST, UTC+4).

This worklog records the actual sequence of work completed on the assessment.
It is intentionally written as a chronological engineering log rather than as a
retrospective summary.

---

## 2026-10-05

### 20:00 — Started the assessment

Opened the assessment and reviewed the full brief.

Captured the main constraints:

- in-memory implementation only;
- no database or persistence layer;
- no web/API layer;
- no UI;
- replay a fixed six-day event stream;
- ledger must be append-only;
- AED uses 2 decimal places;
- BHD uses 3 decimal places;
- authorization holds affect available balance, not ledger balance;
- overdraft fee is AED 25.00;
- positive closing balances accrue daily interest at 0.04%;
- daily interest is rounded using the account currency precision;
- rounded daily accruals are capitalized once at the end of Day 6;
- booking/processing day and value date are separate concepts;
- some acceptance criteria are intentionally incorrect and must be challenged.

Also noted that the exercise is testing reasoning, correctness, trade-offs,
ambiguity handling, and live-defense quality rather than code volume.

---

### 20:20 — Reviewed the event stream

Read through E1–E10 and classified the events into:

- monetary credits/debits;
- authorization holds;
- settlements;
- invalid settlement references;
- value-dated postings;
- reversals;
- multi-instalment postings.

Flagged the main areas that needed explicit decisions before implementation:

- ledger balance vs available balance;
- authorization lifecycle;
- settlement validation;
- value date vs processing date;
- overdraft fee timing;
- reversal behavior;
- daily interest calculation;
- currency rounding and money conservation.

---

### 20:40 — Defined initial ledger invariants

Before writing code, wrote down the core invariants that should drive the model.

#### Ledger balance

Ledger balance should be derived from monetary ledger entries rather than
maintained as mutable account state.

#### Available balance

Authorization holds should reduce available balance without changing ledger
balance.

Conceptually:

```text
available_balance = ledger_balance - active_holds
```

#### Append-only ledger

Existing ledger entries should not be modified or deleted.

A reversal should therefore be represented as a new compensating ledger entry
that references the original event.

#### Settlement validation

A settlement referencing an authorization that does not exist must be rejected
without moving funds.

#### Monetary precision

Binary floating point should not be used for monetary values.

The implementation will use decimal arithmetic.

---

### 21:00 — Manually replayed the early events

Worked through the first part of the event stream by hand before implementing the
engine.

Confirmed the following behavior:

- Day 1 closing balance for ACC-001 is AED 250.00 after E1 and E2.
- Auth-A can be approved because an AED 200.00 hold leaves AED 50.00 available.
- The hold does not change ledger balance.
- E4 moves the ledger balance to AED 650.00.
- E5 can settle Auth-A for AED 185.00.
- E6 must be rejected because Auth-Z was never created.

This confirmed that authorization state and monetary ledger state should be modeled
separately.

---

### 21:25 — Investigated E7 value-date behavior

Focused on E7 because it is processed on Day 5 but has a Day 2 value date.

Observed that a historical ledger view evaluated after E7 must include the posting
according to its value date.

That makes the Day 2 ledger balance:

```text
AED 250.00 - AED 620.00 = AED -370.00
```

This exposed an important ambiguity:

- the value date can change the historical/economic balance;
- the system only becomes aware of E7 on Day 5.

Therefore the brief does not completely define whether a consequential operational
action, such as an overdraft fee, should also be backdated.

Recorded this as an ambiguity to document explicitly rather than hiding the
decision in code.

---

### 21:50 — Investigated BHD instalment rounding

Reviewed E10, where BHD 10.000 must be split into three equal instalments.

Exact division gives:

```text
10.000 / 3 = 3.333333...
```

BHD allows only three fractional decimal places.

Observed that three instalments of BHD 3.334 would total:

```text
3.334 + 3.334 + 3.334 = 10.002
```

which would create BHD 0.002.

Identified money conservation as the stronger invariant:

```text
sum(instalments) == original_amount
```

A deterministic remainder allocation will therefore be required.

---

### 22:10 — Reviewed suspicious acceptance criteria

Compared the supplied acceptance criteria against the domain invariants.

Two criteria were already provably inconsistent with the stated rules:

- requiring all three E10 instalments to be BHD 3.334 would produce BHD 10.002
  instead of BHD 10.000;
- allowing an interest-rounding remainder to be discarded conflicts with the
  non-negotiable requirement that rounded daily accruals sum exactly to the
  capitalized total.

Other criteria still required explicit review:

- whether E7 should cause exactly one overdraft fee to be assessed on Day 2;
- whether reversing E7 should cause all balances and fees to return to their
  pre-E7 values;
- how E8 affects the interpretation of state after E9;
- how unknown authorization settlements should be represented in the output.

Decision: create dedicated `AMBIGUITIES.md` and `REJECTED.md` files so that these
choices are explicit and reviewable.

---

### 22:30 — Chose implementation language and repository structure

Selected Python for the implementation.

Reasons:

- `decimal.Decimal` provides explicit decimal arithmetic for money;
- minimal framework overhead;
- suitable for deterministic replay;
- easy to test;
- easy to explain during the live defense;
- keeps the focus on domain logic rather than infrastructure.

Initial repository structure:

```text
README.md
WORKLOG.md
AMBIGUITIES.md
REJECTED.md
ledger/
    __init__.py
tests/
    __init__.py
```

At this stage no ledger engine or replay logic had been implemented.

---

### 22:45 — Drafted initial documentation

Prepared the first versions of:

- `README.md`
  - project scope;
  - implementation boundaries;
  - language choice.

- `WORKLOG.md`
  - chronological record of the work completed so far.

- `AMBIGUITIES.md`
  - initial notes on value-date semantics;
  - BHD equal-instalment rounding.

- `REJECTED.md`
  - criteria that were already provably wrong;
  - criteria still requiring design review;
  - a placeholder section for approaches abandoned mid-build.

The documentation was intentionally kept preliminary rather than presenting
unresolved decisions as final.

---

### 23:50 — Initialized Git repository and prepared first commit

Initialized Git in the assessment project root.

The first commit is prepared with:

```text
README.md
WORKLOG.md
AMBIGUITIES.md
REJECTED.md
ledger/
    __init__.py
tests/
    __init__.py
```

Planned commit message:

```text
Initialize project and capture initial ledger analysis
```

This commit represents the analysis and repository setup completed since 20:00.

It intentionally does not contain:

- completed ledger business logic;
- final replay output;
- resolution of all acceptance criteria;
- completed automated tests.

This preserves the actual development sequence: understand the domain first,
then implement and validate it.

---

## Next planned work

- implement the core domain model;
- implement monetary ledger entries;
- implement authorization state and available-balance calculation;
- replay E1–E10;
- implement settlement validation;
- implement reversal handling;
- implement currency-aware instalment allocation;
- implement daily interest accrual and Day 6 capitalization;
- write automated tests for the derived balances and state transitions;
- add the required intentionally failing test;
- refine `AMBIGUITIES.md`;
- finalize `REJECTED.md`;
- create `NUMBERS.md`;
- update `README.md` with run/test instructions;
- prepare the architecture and trade-offs document;
- run the final repository from a clean checkout before submission.

The worklog will be appended as implementation progresses rather than rewritten
after the fact.

---

## 2026-10-06

### 22:00 — Implemented core domain model

Added the first implementation layer for the ledger domain:

- currency precision handling;
- decimal quantization helper;
- immutable ledger entry model;
- account model;
- authorization model and authorization states.

Kept ledger balance out of mutable account state so that balances can be derived
from append-only ledger entries.

Added initial unit tests for AED and BHD rounding behavior.

No event replay, fee calculation, interest calculation, or settlement processing
has been implemented yet.

## Currency rounding mode

The brief specifies the number of decimal places for AED and BHD but does not
specify the tie-breaking rounding mode.

Resolution:

The implementation uses `ROUND_HALF_UP` for currency quantization.

Reasoning:

A deterministic rounding mode is required for reproducible calculations and tests.
The choice is isolated in the money helper so it can be changed without affecting
the ledger model if a production banking rule requires a different convention.
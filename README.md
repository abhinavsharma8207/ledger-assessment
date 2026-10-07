# In-Memory Account Ledger Core

Staff Software Engineer take-home assessment.

This repository implements the supplied six-day account-ledger replay in memory.
The implementation deliberately stays inside the requested scope: no database,
web layer, persistence layer, or UI.

## Requirements

- Python 3.10+
- `pytest`

Install the only development dependency if required:

```bash
python -m pip install pytest
```

## Run the replay

```bash
python -m ledger.replay
```

The replay reports day-end ledger balances, interest accruals, authorization
states, fees, and errors.

Key final results under the documented design decisions:

- ACC-001 historical Day-2 balance, evaluated after E7 is known: **AED -370.00**
- Auth-A: **SETTLED** for AED 185.00; unused AED 15.00 hold released
- Auth-Z settlement: **rejected**, no funds moved
- Auth-B: **DECLINED**
- one AED 25.00 overdraft fee assessed on **processing Day 5**, not backdated
- ACC-001 Day-6 final balance after interest capitalization: **AED 440.83**
- ACC-002 E10 allocation: **BHD 3.334 + 3.333 + 3.333 = BHD 10.000**
- ACC-002 Day-6 final balance after interest capitalization: **BHD 10.008**

## Run tests

Normal test suite:

```bash
python -m pytest
```

The assessment also asks for one intentionally failing test against the design.
It is kept outside default pytest discovery so the normal suite remains useful:

```bash
python -m pytest tests/known_failure_test.py
```

That test demonstrates a deliberate simplification: authorization objects store
current state rather than a full immutable authorization-state history.

## Project structure

```text
ledger/
    engine.py       # balances, holds, settlement, fees, interest
    models.py       # ledger/account/authorization domain types
    money.py        # currency precision and conserving splits
    replay.py       # deterministic E1-E10 six-day replay

tests/
    test_money.py
    test_engine.py
    test_replay.py
    known_failure_test.py

README.md
NUMBERS.md
AMBIGUITIES.md
REJECTED.md
WORKLOG.md
ARCHITECTURE.md
```

## Core design

### Append-only monetary ledger

`LedgerEntry` is immutable. Reversals append compensating entries rather than
modifying/deleting the original posting. `Account.entries` is an in-memory list;
append-only behavior is enforced by the engine API and is a convention rather
than durable storage enforcement.

### Bitemporal balance query

A ledger balance accepts both a `value_day` and an `as_of_booking_day`. This lets
E7 be booked on Day 5 with value date Day 2 while still distinguishing what was
known on Day 2 from what is known after Day 5.

### Holds and available balance

Authorization holds are separate from monetary postings:

```text
available balance = ledger balance - active approved holds
```

A successful settlement posts the settled amount and releases the authorization
hold. In this exercise settlement is terminal, so Auth-A's unused AED 15.00 is
released rather than retained as a residual hold.

### Interest

Interest accrues only on positive processing-day closing ledger balances at
0.04% per day. Each daily amount is rounded to the account currency precision.
On Day 6, the already-rounded daily accruals are summed and posted once. No
rounding remainder is discarded.

## Documentation

- `NUMBERS.md` — hand calculations and expected replay numbers
- `AMBIGUITIES.md` — ambiguities and how they were resolved
- `REJECTED.md` — deliberately incorrect acceptance criteria and rationale
- `WORKLOG.md` — chronological engineering log
- `ARCHITECTURE.md` — architecture decisions, production trade-offs, controls, and deferred production risks

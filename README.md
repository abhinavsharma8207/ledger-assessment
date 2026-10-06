# In-Memory Account Ledger Core

Staff Software Engineer take-home assessment.

This repository contains an in-memory account ledger implementation for replaying
the supplied six-day event stream.

## Scope

The implementation will intentionally stay within the assessment boundary:

- in-memory only
- no database
- no persistence layer
- no web/API layer
- no UI
- append-only ledger model
- deterministic event replay
- currency-aware rounding
- authorization and settlement handling
- overdraft fee assessment
- daily interest accrual and Day 6 capitalization

The repository will also contain:

- `NUMBERS.md`
- `AMBIGUITIES.md`
- `REJECTED.md`
- `WORKLOG.md`
- automated tests
- one intentionally failing, annotated test as requested

## Language

Python.

The implementation will use `decimal.Decimal` rather than binary floating point
for monetary values.

## Status

Initial project setup only.

The event stream and acceptance criteria are being analysed before implementation
so that domain invariants and ambiguities are made explicit rather than encoded
implicitly in code.
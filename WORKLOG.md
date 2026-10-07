# WORKLOG.md

All times are Dubai time — Gulf Standard Time (GST, UTC+4).

This log records the sequence of work on the assessment. It is kept as an
engineering log rather than rewritten as a polished retrospective.

## 2026-10-05

### 20:00 — Started the assessment

Reviewed the complete brief and extracted the implementation constraints:
in-memory only, append-only ledger behavior, AED/BHD precision, authorization
holds, value dates, overdraft fees, daily interest, and the requirement to reject
incorrect acceptance criteria.

### 20:20 — Reviewed E1-E10

Classified the stream into monetary postings, holds, settlements, back-valued
postings, reversal, and multi-instalment posting. Flagged value date vs processing
date, authorization lifecycle, fee timing, reversal behavior, and rounding as the
main areas requiring explicit decisions.

### 20:40 — Defined initial invariants

Decided that ledger balance should be derived from postings, holds should affect
available balance rather than ledger balance, reversals should be compensating
entries, unknown authorization settlements should not move funds, and monetary
arithmetic should use decimal rather than binary floating point.

### 21:00 — Manually replayed early events

Confirmed Day-1 AED 250.00, Auth-A approval with AED 50.00 available, Day-3 AED
650.00, Auth-A settlement for AED 185.00, and rejection of unknown Auth-Z.

### 21:25 — Investigated E7

Separated value date from processing date. Confirmed that E7 makes the historical
Day-2 balance AED -370.00 when evaluated after E7 is known, while noting that fee
timing remained ambiguous.

### 21:50 — Investigated E10

Confirmed that three BHD 3.334 instalments total BHD 10.002. Chose conservation of
the BHD 10.000 source amount as the stronger invariant.

### 22:10 — Reviewed acceptance criteria

Identified the BHD 3.334 criterion and discarded-interest-remainder criterion as
provably inconsistent. Marked fee timing and reversal consequences for explicit
resolution rather than blind implementation.

### 22:30 — Chose Python and initial structure

Selected Python with `Decimal` to keep the exercise small, deterministic, and easy
to defend. Created the initial repository structure and documentation files.

### 23:27 — Prepared first repository commit

Prepared the initial project/documentation commit before implementing the ledger
engine.

## 2026-10-06

### 21:45 — Corrected repository root

Fixed the accidental nested repository layout and moved the assessment files to
the Git repository root. Kept the correction as a separate commit rather than
rewriting history.

### 22:00 — Added initial domain model and money helpers

Added account, immutable ledger-entry and authorization models, currency-aware
`Decimal` quantization, and initial AED/BHD rounding tests.

### 22:15 — Resolved rounding mode

Selected `ROUND_HALF_UP`; documented the decision in `AMBIGUITIES.md`.

### 23:17 — Started completion pass

With the submission window now short, switched from incremental scaffolding to a
single completion pass focused on correctness and test coverage.

Completed the remaining design decisions:

- bitemporal balance query using value day plus as-of booking day;
- fee assessed on processing Day 5 rather than retroactively on Day 2;
- Auth-A partial settlement treated as terminal, releasing the unused hold;
- E9 modeled as an append-only compensating entry;
- fee remains unless separately reversed;
- BHD split performed in minor units to conserve exactly BHD 10.000;
- daily interest rounded each day and capitalized once on Day 6;
- Day-6 accrual calculated before capitalization.

Added the replay engine, full E1-E10 replay, numeric derivation document, broader
unit/replay tests, and the required deliberately failing design test kept outside
default pytest discovery.

The next step is local verification (`pytest`, replay output, clean checkout), then
one final documentation/architecture pass before submission.

## 2026-10-07

### 05:45 — Completed architecture and trade-offs review

Completed the production architecture and trade-offs document based on the final
ledger implementation.

Covered:

- append-only growth and snapshot/materialized-projection strategy;
- value-dated entries and operational impact;
- maker-checker control for back-valued adjustments;
- production authorization lifecycle beyond settlement;
- concurrency and idempotency controls;
- implementation simplifications and the production risks they defer.

Added a compact production-control matrix tying each control to a failure mode
exposed by the implementation.

The architecture discussion intentionally describes production extensions rather
than changing the scope of the in-memory assessment implementation.
# Architecture and production trade-offs

> Working source for the required 2-4 page architecture/trade-offs PDF.

## Current exercise design

The implementation is intentionally a small in-memory domain engine. Monetary
changes are immutable `LedgerEntry` objects; account balance is derived from
entries rather than stored as mutable state. Authorizations are separate from
ledger postings because holds change available funds but do not themselves move
money.

Two temporal dimensions are kept for monetary postings: `booking_day` (when the
system knows/processes the event) and `value_day` (when it economically applies).
That distinction is what allows E7 to alter the historical Day-2 view without
pretending the system knew E7 on Day 2.

## What breaks at 100x volume

The exercise implementation repeatedly scans Python lists to calculate balances
and checks duplicate event IDs linearly. That is acceptable for ten events and
wrong for large production volumes. At 100x and beyond, I would replace linear
reconstruction on every query with durable append-only storage plus indexed
projections/materialized balances.

A production write path would normally have an idempotency/event key, account
partitioning, transactional append, and optimistic version/sequence checks. Reads
would come from projections keyed by account and effective date rather than by
rescanning an unbounded event list. Hot accounts would need concurrency control so
two simultaneous authorizations cannot both reserve the same available funds.

## Unbounded append-only state

Append-only is valuable for auditability, but an infinite raw event list cannot be
the only read model. I would retain the immutable journal as the system of record
and add checkpoints/snapshots or materialized daily balances. Historical replay
would start from the nearest trusted snapshot and apply later events.

Retention/archival policy should move old immutable partitions to cheaper storage
without changing their audit identity. Reconciliation jobs should continuously
compare journal totals, projections, and downstream settlement records.

## Value-dated entries in a UAE banking context

Value date must not be collapsed into posting timestamp. Back-valued corrections,
settlement adjustments, and operational cut-offs can make an entry economically
apply to an earlier business date than the date on which it arrives.

I would model at least event/booking time and value/effective date explicitly, with
a business-calendar service for UAE cut-offs, weekends/holidays, and product rules.
Operational side effects such as fees should be governed by explicit policy:
retroactive recomputation, prospective assessment, or adjustment posting. This
exercise chooses prospective assessment on Day 5 because E7 was not known earlier;
a real bank policy must be versioned and auditable rather than inferred.

## Authorization lifecycle

The exercise needs APPROVED, DECLINED, and SETTLED. Production card/payment
systems need a richer state machine: approved, partially captured, fully captured,
expired, cancelled/voided, reversed, and possibly disputed/adjusted states.

Each transition should itself be immutable and idempotent. Remaining authorized
amount, capture totals, expiry, merchant/network references, and reason codes
should be explicit. Holds should be derived from active authorization state, not
from mutable balance fields.

The intentionally failing test highlights a simplification here: this assessment
stores the current authorization object, not an immutable transition history that
supports arbitrary historical authorization-state queries.

## Deliberate simplifications and production risks

**In-memory only.** A crash loses all state. Production requires durable,
transactional persistence and recovery.

**Single-process execution.** There is no concurrency protection. Production must
serialize or version operations per account to prevent double spending.

**Append-only by API convention.** `LedgerEntry` is immutable, but the backing
Python list is still mutable by a caller with direct object access. Durable storage
should enforce append semantics and access boundaries.

**Simple currency rules.** Only AED and BHD are configured, both with one chosen
rounding mode. Production needs a currency/product rules registry and versioned
rounding policy.

**Simplified fee policy.** One Day-5 fee is chosen for this exercise. Real fee
assessment needs explicit product rules, grace periods, fee caps, waivers,
reversals, and regulatory/customer-treatment controls.

**Simplified authorization settlement.** E5 is treated as terminal even though it
captures less than the authorized amount. Production needs explicit partial-
capture and expiry semantics.

**No external reconciliation.** A real ledger needs reconciliation against payment
networks, settlement files, GL/sub-ledger postings, and exception workflows.

The guiding production principle is to keep the immutable journal small in
responsibility: facts are appended once; balances, holds, fees, and reporting are
derived through versioned policies and rebuildable projections.

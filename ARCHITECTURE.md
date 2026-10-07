# Architecture & Trade-offs

This document captures the architectural decisions, trade-offs, and production considerations that arise directly from the in-memory ledger implementation.

## 1. Append-only at scale

The current design keeps ledger entries and authorization state in memory and derives balances from append-only postings.

At the assessment scale this keeps the model simple and auditable. At 100× volume, the first pressure point is not the arithmetic itself but repeated balance reconstruction over an ever-growing entry list. Historical value-date queries become increasingly expensive because they require scanning more entries, and the in-memory append-only collection grows without bound.

The design accumulates unbounded state in:

- per-account ledger-entry history;
- authorization history/state;
- daily interest-accrual records;
- error/audit records if retained indefinitely.

The cheapest structural change that defers the problem is to introduce per-account snapshots or materialized balance checkpoints while retaining the append-only source of truth.

A snapshot would contain, for example:

- balance as of a known sequence number / processing point;
- active authorization holds;
- last processed event sequence;
- accrued-but-not-capitalized interest.

Historical replay could then start from the nearest preceding snapshot rather than from account inception.

In production I would combine this with partitioning by account and a durable event store. The event log remains immutable, while balance and authorization views become rebuildable projections.

This preserves the audit advantages of append-only storage without requiring every read to replay an unbounded history.

A further scale concern is concurrency. The assessment implementation is single-process and deterministic. A production ledger would need serialized updates per account, optimistic version checks, or another concurrency-control mechanism so that two simultaneous authorizations cannot both spend the same available balance.

## 2. Value-dated entries in production

The implementation distinguishes processing day from value date. That distinction is operationally significant in a bank because a posting can become known today while economically affecting an earlier balance date.

In production, value-dated entries create several surfaces:

- historical balances can change after a prior business day has closed;
- interest and fee calculations may need recomputation;
- statements and downstream reconciliations may differ from previously published results;
- general-ledger and product-ledger reconciliation can require adjustment entries;
- customer-impacting corrections need traceable reason codes;
- repeated back-valuing can become an operational-risk and conduct issue;
- accounting and regulatory reports may need controlled restatement or adjustment rather than silent mutation.

For a UAE-licensed bank, I would treat back-valued postings as controlled adjustments rather than ordinary postings. The important requirement is not only that the ledger can represent them, but that their operational effects are authorized, traceable, reproducible, and reconcilable.

### Control before go-live

The primary control I would add is maker-checker approval for back-valued postings beyond an agreed threshold or closed-business-date boundary.

The control would require:

- a reason code;
- authenticated maker identity;
- independent approver;
- original processing timestamp;
- requested value date;
- before/after financial impact;
- immutable audit record;
- downstream recalculation/reconciliation status.

This reduces the risk of unauthorized retroactive adjustments while preserving the append-only model.

The production implementation should also define policy explicitly for which consequences are recomputed when an entry is back-valued. In this assessment I deliberately separate historical ledger value from the processing date of operational actions such as fee assessment.

## 3. Authorization lifecycle

The assessment model exercises approval, decline, and settlement. A production authorization has additional terminal paths.

### Declined at authorization time

Real-world scenario: insufficient available funds, velocity/risk rule failure, blocked account, or another authorization policy failure.

Mandated behavior:

- create no active hold;
- return a deterministic decline result;
- retain the decision/audit event;
- never change ledger balance.

### Expired

Real-world scenario: a merchant authorization is approved but no matching settlement arrives before the scheme/product hold-expiry period.

Mandated behavior:

- transition the authorization to `EXPIRED`;
- release any remaining hold exactly once;
- retain the original authorization and expiry event;
- do not create a ledger debit.

Expiry processing must be idempotent because scheduled jobs can retry.

### Reversed / voided by the merchant or network

Real-world scenario: the merchant cancels the authorization before settlement, or the card/network sends an authorization reversal.

Mandated behavior:

- transition to `REVERSED`;
- release the remaining hold;
- preserve both the original authorization and reversal event;
- reject or specially reconcile a later settlement depending on network rules.

### Cancelled by an internal control

Real-world scenario: fraud operations, account closure, duplicate authorization correction, or operational remediation.

Mandated behavior:

- require an explicit cancellation reason and actor;
- release the hold;
- retain the cancellation as a new lifecycle event;
- prevent silent mutation of the original authorization.

### Superseded / replaced

Real-world scenario: an incremental or replacement authorization changes the effective held amount.

Mandated behavior:

- link the replacement to the prior authorization;
- atomically adjust the active hold;
- retain the full transition history;
- ensure retries cannot double-increase or double-release the hold.

The assessment implementation intentionally does not model all these states. It keeps only the current authorization object because the six-day replay does not require a full historical authorization-state projection. The deliberately failing test documents this limitation.

## 4. Production control matrix

| Risk | Production control |
|---|---|
| Back-valued posting changes a closed historical balance | Maker-checker approval, reason code, immutable audit trail, impact preview |
| Duplicate or retried event | Globally unique event/idempotency key with duplicate detection before posting |
| Settlement references an unknown authorization | Reject or route to an exception/suspense workflow; never silently debit |
| Authorization remains open indefinitely | Product/network expiry policy with idempotent scheduled hold release |
| Balance projection drifts from append-only source | Periodic replay/reconciliation from source events to materialized projections |
| Two concurrent authorizations overspend available balance | Per-account serialization, optimistic versioning, or transactional compare-and-set |
| Rounding differences across services | Central currency metadata and deterministic decimal quantization |
| Consequential fee/interest adjustment after back-valued entry | Explicit recalculation policy plus auditable adjustment entries rather than hidden mutation |

The controls are intentionally tied to failure modes exposed by the implementation rather than attempting to be a complete banking-control catalogue.

## 5. What I cut and why

The implementation is deliberately smaller than a production ledger. Each omission keeps the exercise focused but defers a specific production risk.

### Persistence

Cut:

- database/event store;
- crash recovery;
- durable checkpoints.

Why:

The exercise explicitly requires in-memory behavior.

Deferred risk:

A process restart loses state. Production requires durable immutable events and recoverable projections.

### Distributed concurrency

Cut:

- locking;
- optimistic versions;
- account partition ownership;
- cross-node coordination.

Why:

The supplied replay is deterministic and single-threaded.

Deferred risk:

Concurrent authorizations or postings could race and overspend an account.

### Full authorization history

Cut:

Only current authorization state is kept rather than an event-sourced authorization lifecycle.

Why:

The replay only needs current hold/state decisions.

Deferred risk:

Historical authorization state cannot be queried after later transitions. This limitation is captured by the intentionally failing test.

### Complete card/network lifecycle

Cut:

No incremental authorization, partial reversal, expiry scheduler, chargeback, presentment retry, or late settlement model.

Why:

Those states are outside the supplied event stream.

Deferred risk:

Real network messages cannot be handled safely without a richer authorization state machine and scheme-specific rules.

### FX and multi-currency conversion

Cut:

Each account operates only in its native currency; no conversion is performed.

Why:

The exercise supplies fixed-currency accounts.

Deferred risk:

Production needs rate source, timestamp, spread, rounding, accounting legs, and reconciliation for FX.

### General-ledger double entry

Cut:

The implementation models the customer-account ledger only, not balanced accounting legs.

Why:

The assessment asks for an account-ledger core rather than a full accounting platform.

Deferred risk:

Production requires every financial movement to reconcile to balanced GL/control accounts.

### Advanced fee policy

Cut:

One overdraft-fee rule is modeled, with processing-date behavior chosen explicitly for the back-valued event.

Why:

The brief intentionally creates a temporal ambiguity and the solution needs one defensible interpretation.

Deferred risk:

Real products need configurable fee calendars, waivers, caps, refunds, customer-protection rules, and controlled retroactive adjustments.

### Interest engine

Cut:

Only the supplied daily positive-balance accrual and Day-6 capitalization behavior is implemented.

Why:

That is sufficient to exercise rounding and capitalization invariants.

Deferred risk:

Production interest requires product calendars, day-count conventions, rate changes, holidays, tax/withholding rules, back-dated recalculation, and reconciliation.

### External interfaces

Cut:

No API, UI, messaging layer, authentication, or authorization.

Why:

The assessment explicitly excludes them.

Deferred risk:

Production requires authenticated commands, schema/version control, rate limiting, observability, and secure operational access.

### Full regulatory/control framework

Cut:

The implementation includes only controls directly motivated by the exercise.

Why:

A complete bank-control environment is much larger than an in-memory coding assessment.

Deferred risk:

Go-live would additionally require formal operational-risk assessment, access control, segregation of duties, reconciliation ownership, monitoring, retention, incident response, and regulatory/compliance sign-off.

## Closing position

The implementation favors explicit invariants over framework complexity:

- immutable monetary entries;
- deterministic decimal arithmetic;
- separation of ledger balance from authorization holds;
- compensating reversals rather than mutation;
- explicit treatment of processing date versus value date;
- conservation of money across rounding;
- reproducible replay.

For production, I would preserve those invariants but replace the in-memory structures with a durable append-only event store plus account-partitioned projections, snapshots, idempotency, reconciliation, lifecycle automation, and concurrency controls.

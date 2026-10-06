"""Required intentionally failing test against a deliberate simplification.

This file is intentionally named so default `pytest` discovery does not collect it.
Run it explicitly with:

    python -m pytest tests/known_failure_test.py

The failure demonstrates that the current in-memory design does not preserve a
historical authorization-state timeline. It stores current authorization state,
while the replay report captures day-end states as it processes the stream.
A production implementation that supports arbitrary historical authorization
queries would model authorization transitions as immutable events as well.
"""

from ledger.replay import run_replay


def test_historical_authorization_state_can_be_queried_after_replay():
    result = run_replay()
    auth_a = result.engine.account("ACC-001").authorizations["Auth-A"]

    # Deliberately fails: after the full replay the object contains its terminal
    # SETTLED state, not a queryable Day-2 APPROVED snapshot.
    assert auth_a.status.value == "APPROVED"

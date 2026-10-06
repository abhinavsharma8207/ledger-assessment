from decimal import Decimal

from ledger.models import AuthorizationStatus, EntryType
from ledger.replay import run_replay


def test_full_six_day_replay_expected_results():
    result = run_replay()
    engine = result.engine

    assert engine.ledger_balance("ACC-001", value_day=2, as_of_booking_day=5) == Decimal("-370.00")
    assert engine.account("ACC-001").authorizations["Auth-A"].status == AuthorizationStatus.SETTLED
    assert engine.account("ACC-001").authorizations["Auth-B"].status == AuthorizationStatus.DECLINED
    assert any("unknown authorization Auth-Z" in error for error in engine.errors)

    fee_entries = [e for e in engine.account("ACC-001").entries if e.entry_type == EntryType.FEE]
    assert len(fee_entries) == 1
    assert fee_entries[0].booking_day == 5
    assert fee_entries[0].value_day == 5
    assert fee_entries[0].amount == Decimal("-25.00")

    assert engine.daily_interest[("ACC-001", 1)] == Decimal("0.10")
    assert engine.daily_interest[("ACC-001", 2)] == Decimal("0.10")
    assert engine.daily_interest[("ACC-001", 3)] == Decimal("0.26")
    assert engine.daily_interest[("ACC-001", 4)] == Decimal("0.19")
    assert engine.daily_interest[("ACC-001", 5)] == Decimal("0.00")
    assert engine.daily_interest[("ACC-001", 6)] == Decimal("0.18")

    assert engine.daily_interest[("ACC-002", 5)] == Decimal("0.004")
    assert engine.daily_interest[("ACC-002", 6)] == Decimal("0.004")

    assert engine.closing_balance("ACC-001", 6) == Decimal("440.83")
    assert engine.closing_balance("ACC-002", 6) == Decimal("10.008")


def test_reversal_is_append_only_and_does_not_remove_original_entry():
    result = run_replay()
    entries = result.engine.account("ACC-001").entries

    e7 = next(e for e in entries if e.event_id == "E7")
    e9 = next(e for e in entries if e.event_id == "E9")

    assert e7.amount == Decimal("-620.00")
    assert e9.amount == Decimal("620.00")
    assert e9.reference_id == "E7"
    assert e9.entry_type == EntryType.REVERSAL


def test_capitalized_interest_equals_sum_of_rounded_daily_accruals():
    result = run_replay()
    engine = result.engine

    aed_sum = sum(
        (engine.daily_interest[("ACC-001", day)] for day in range(1, 7)),
        Decimal("0"),
    )
    bhd_sum = sum(
        (engine.daily_interest[("ACC-002", day)] for day in (5, 6)),
        Decimal("0"),
    )

    aed_cap = next(e for e in engine.account("ACC-001").entries if e.event_id == "INT-CAP-ACC-001")
    bhd_cap = next(e for e in engine.account("ACC-002").entries if e.event_id == "INT-CAP-ACC-002")

    assert aed_sum == Decimal("0.83") == aed_cap.amount
    assert bhd_sum == Decimal("0.008") == bhd_cap.amount

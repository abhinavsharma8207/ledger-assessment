from decimal import Decimal

from ledger.engine import LedgerEngine
from ledger.models import AuthorizationStatus, EntryType


def make_engine() -> LedgerEngine:
    engine = LedgerEngine()
    engine.add_account("ACC-001", "AED")
    return engine


def test_hold_changes_available_not_ledger_balance():
    engine = make_engine()
    engine.append_entry(
        event_id="E1", account_id="ACC-001", amount=Decimal("250.00"),
        booking_day=1, value_day=1, entry_type=EntryType.CREDIT,
    )

    auth = engine.authorize("Auth-A", "ACC-001", Decimal("200.00"), 2)

    assert auth.status == AuthorizationStatus.APPROVED
    assert engine.closing_balance("ACC-001", 2) == Decimal("250.00")
    assert engine.available_balance("ACC-001", 2) == Decimal("50.00")


def test_valid_partial_settlement_posts_amount_and_releases_entire_hold():
    engine = make_engine()
    engine.append_entry(
        event_id="E1", account_id="ACC-001", amount=Decimal("250.00"),
        booking_day=1, value_day=1, entry_type=EntryType.CREDIT,
    )
    auth = engine.authorize("Auth-A", "ACC-001", Decimal("200.00"), 2)

    accepted = engine.settle(
        event_id="E5", authorization_id="Auth-A", account_id="ACC-001",
        amount=Decimal("185.00"), booking_day=4, value_day=4,
    )

    assert accepted is True
    assert auth.status == AuthorizationStatus.SETTLED
    assert auth.settled_amount == Decimal("185.00")
    assert auth.active_hold == Decimal("0")
    assert engine.closing_balance("ACC-001", 4) == Decimal("65.00")


def test_unknown_authorization_settlement_is_rejected_without_debit():
    engine = make_engine()
    engine.append_entry(
        event_id="E1", account_id="ACC-001", amount=Decimal("250.00"),
        booking_day=1, value_day=1, entry_type=EntryType.CREDIT,
    )

    accepted = engine.settle(
        event_id="E6", authorization_id="Auth-Z", account_id="ACC-001",
        amount=Decimal("180.00"), booking_day=4, value_day=4,
    )

    assert accepted is False
    assert engine.closing_balance("ACC-001", 4) == Decimal("250.00")
    assert len(engine.errors) == 1


def test_back_valued_entry_changes_historical_value_day_only_when_known():
    engine = make_engine()
    engine.append_entry(
        event_id="E1", account_id="ACC-001", amount=Decimal("250.00"),
        booking_day=1, value_day=1, entry_type=EntryType.CREDIT,
    )
    engine.append_entry(
        event_id="E7", account_id="ACC-001", amount=Decimal("-620.00"),
        booking_day=5, value_day=2, entry_type=EntryType.DEBIT,
    )

    assert engine.ledger_balance("ACC-001", value_day=2, as_of_booking_day=2) == Decimal("250.00")
    assert engine.ledger_balance("ACC-001", value_day=2, as_of_booking_day=5) == Decimal("-370.00")

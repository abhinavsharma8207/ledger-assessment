from dataclasses import dataclass
from decimal import Decimal

from .engine import LedgerEngine
from .models import AuthorizationStatus, EntryType
from .money import split_amount


DAILY_INTEREST_RATE = Decimal("0.0004")
OVERDRAFT_FEE_AED = Decimal("25.00")


@dataclass(frozen=True)
class ReplayResult:
    engine: LedgerEngine
    day_summaries: dict[int, list[str]]


def run_replay() -> ReplayResult:
    engine = LedgerEngine()
    engine.add_account("ACC-001", "AED")
    engine.add_account("ACC-002", "BHD")
    summaries: dict[int, list[str]] = {day: [] for day in range(1, 7)}

    # Day 1: E1, E2
    engine.append_entry(
        event_id="E1", account_id="ACC-001", amount=Decimal("1200.00"),
        booking_day=1, value_day=1, entry_type=EntryType.CREDIT,
    )
    engine.append_entry(
        event_id="E2", account_id="ACC-001", amount=Decimal("-950.00"),
        booking_day=1, value_day=1, entry_type=EntryType.DEBIT,
    )
    interest = engine.accrue_interest("ACC-001", 1, DAILY_INTEREST_RATE)
    summaries[1].extend([
        f"ACC-001 closing ledger: AED {engine.closing_balance('ACC-001', 1):.2f}",
        f"ACC-001 interest accrual: AED {interest:.2f}",
    ])

    # Day 2: E3
    auth_a = engine.authorize("Auth-A", "ACC-001", Decimal("200.00"), 2)
    interest = engine.accrue_interest("ACC-001", 2, DAILY_INTEREST_RATE)
    summaries[2].extend([
        f"ACC-001 closing ledger: AED {engine.closing_balance('ACC-001', 2):.2f}",
        f"Auth-A: {auth_a.status.value} (hold AED {auth_a.active_hold:.2f})",
        f"ACC-001 available: AED {engine.available_balance('ACC-001', 2):.2f}",
        f"ACC-001 interest accrual: AED {interest:.2f}",
    ])

    # Day 3: E4
    engine.append_entry(
        event_id="E4", account_id="ACC-001", amount=Decimal("400.00"),
        booking_day=3, value_day=3, entry_type=EntryType.CREDIT,
    )
    interest = engine.accrue_interest("ACC-001", 3, DAILY_INTEREST_RATE)
    summaries[3].extend([
        f"ACC-001 closing ledger: AED {engine.closing_balance('ACC-001', 3):.2f}",
        f"Auth-A: {auth_a.status.value} (hold AED {auth_a.active_hold:.2f})",
        f"ACC-001 available: AED {engine.available_balance('ACC-001', 3):.2f}",
        f"ACC-001 interest accrual: AED {interest:.2f}",
    ])

    # Day 4: E5, E6
    accepted = engine.settle(
        event_id="E5", authorization_id="Auth-A", account_id="ACC-001",
        amount=Decimal("185.00"), booking_day=4, value_day=4,
    )
    rejected = engine.settle(
        event_id="E6", authorization_id="Auth-Z", account_id="ACC-001",
        amount=Decimal("180.00"), booking_day=4, value_day=4,
    )
    interest = engine.accrue_interest("ACC-001", 4, DAILY_INTEREST_RATE)
    summaries[4].extend([
        f"ACC-001 closing ledger: AED {engine.closing_balance('ACC-001', 4):.2f}",
        f"Auth-A settlement: {'ACCEPTED' if accepted else 'REJECTED'} (AED 185.00)",
        f"Auth-A status: {auth_a.status.value}; remaining active hold AED {auth_a.active_hold:.2f}",
        f"Auth-Z settlement: {'ACCEPTED' if rejected else 'REJECTED'}",
        f"ACC-001 interest accrual: AED {interest:.2f}",
    ])

    # Day 5: E7, E8, E10 + fee triggered by E7 processing.
    engine.append_entry(
        event_id="E7", account_id="ACC-001", amount=Decimal("-620.00"),
        booking_day=5, value_day=2, entry_type=EntryType.DEBIT,
    )
    historical_day2 = engine.ledger_balance("ACC-001", value_day=2, as_of_booking_day=5)
    auth_b = engine.authorize("Auth-B", "ACC-001", Decimal("90.00"), 5)
    fee_assessed = engine.assess_overdraft_fee(
        event_id="FEE-E7", account_id="ACC-001", booking_day=5,
        fee=OVERDRAFT_FEE_AED, cause_event_id="E7",
    )

    instalments = split_amount(Decimal("10.000"), 3, "BHD")
    for index, amount in enumerate(instalments, start=1):
        engine.append_entry(
            event_id=f"E10-{index}", account_id="ACC-002", amount=amount,
            booking_day=5, value_day=5, entry_type=EntryType.CREDIT, reference_id="E10",
        )

    interest_1 = engine.accrue_interest("ACC-001", 5, DAILY_INTEREST_RATE)
    interest_2 = engine.accrue_interest("ACC-002", 5, DAILY_INTEREST_RATE)
    summaries[5].extend([
        f"ACC-001 historical Day 2 ledger as of Day 5: AED {historical_day2:.2f}",
        f"Auth-B: {auth_b.status.value}",
        f"Overdraft fee assessed on processing Day 5: {'YES' if fee_assessed else 'NO'}",
        f"ACC-001 closing ledger: AED {engine.closing_balance('ACC-001', 5):.2f}",
        f"ACC-001 interest accrual: AED {interest_1:.2f}",
        f"ACC-002 instalments: {', '.join(str(x) for x in instalments)} BHD",
        f"ACC-002 closing ledger: BHD {engine.closing_balance('ACC-002', 5):.3f}",
        f"ACC-002 interest accrual: BHD {interest_2:.3f}",
    ])

    # Day 6: E9 + daily accrual before capitalization.
    engine.append_entry(
        event_id="E9", account_id="ACC-001", amount=Decimal("620.00"),
        booking_day=6, value_day=2, entry_type=EntryType.REVERSAL, reference_id="E7",
    )
    interest_1 = engine.accrue_interest("ACC-001", 6, DAILY_INTEREST_RATE)
    interest_2 = engine.accrue_interest("ACC-002", 6, DAILY_INTEREST_RATE)
    cap_1 = engine.capitalize_interest("ACC-001", 6, "INT-CAP-ACC-001")
    cap_2 = engine.capitalize_interest("ACC-002", 6, "INT-CAP-ACC-002")

    summaries[6].extend([
        "E9 appended as a compensating reversal of E7; E7 remains in the ledger",
        f"ACC-001 Day 6 interest accrual before capitalization: AED {interest_1:.2f}",
        f"ACC-001 interest capitalization: AED {cap_1:.2f}",
        f"ACC-001 final ledger: AED {engine.closing_balance('ACC-001', 6):.2f}",
        f"ACC-002 Day 6 interest accrual before capitalization: BHD {interest_2:.3f}",
        f"ACC-002 interest capitalization: BHD {cap_2:.3f}",
        f"ACC-002 final ledger: BHD {engine.closing_balance('ACC-002', 6):.3f}",
    ])

    return ReplayResult(engine=engine, day_summaries=summaries)


def main() -> None:
    result = run_replay()
    for day in range(1, 7):
        print(f"DAY {day}")
        for line in result.day_summaries[day]:
            print(f"  {line}")
        day_errors = [error for error in result.engine.errors if error.startswith("E6") and day == 4]
        for error in day_errors:
            print(f"  ERROR: {error}")
        print()


if __name__ == "__main__":
    main()

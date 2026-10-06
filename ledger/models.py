from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum


class EntryType(str, Enum):
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"
    SETTLEMENT = "SETTLEMENT"
    REVERSAL = "REVERSAL"
    FEE = "FEE"
    INTEREST = "INTEREST"


class AuthorizationStatus(str, Enum):
    APPROVED = "APPROVED"
    DECLINED = "DECLINED"
    SETTLED = "SETTLED"


@dataclass(frozen=True)
class LedgerEntry:
    event_id: str
    account_id: str
    amount: Decimal
    booking_day: int
    value_day: int
    entry_type: EntryType
    reference_id: str | None = None


@dataclass
class Authorization:
    authorization_id: str
    account_id: str
    amount: Decimal
    booking_day: int
    status: AuthorizationStatus
    settled_amount: Decimal = Decimal("0")

    @property
    def active_hold(self) -> Decimal:
        return self.amount if self.status == AuthorizationStatus.APPROVED else Decimal("0")


@dataclass
class Account:
    account_id: str
    currency: str
    opening_balance: Decimal = Decimal("0")
    entries: list[LedgerEntry] = field(default_factory=list)
    authorizations: dict[str, Authorization] = field(default_factory=dict)

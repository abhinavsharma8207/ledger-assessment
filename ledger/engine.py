from decimal import Decimal

from .models import Account, Authorization, AuthorizationStatus, EntryType, LedgerEntry
from .money import quantize_amount


class LedgerEngine:
    """Small in-memory ledger engine for the assessment event stream."""

    def __init__(self) -> None:
        self.accounts: dict[str, Account] = {}
        self.errors: list[str] = []
        self.daily_interest: dict[tuple[str, int], Decimal] = {}

    def add_account(self, account_id: str, currency: str, opening_balance: Decimal = Decimal("0")) -> None:
        if account_id in self.accounts:
            raise ValueError(f"Account already exists: {account_id}")
        self.accounts[account_id] = Account(
            account_id=account_id,
            currency=currency,
            opening_balance=quantize_amount(opening_balance, currency),
        )

    def account(self, account_id: str) -> Account:
        try:
            return self.accounts[account_id]
        except KeyError as exc:
            raise ValueError(f"Unknown account: {account_id}") from exc

    def append_entry(
        self,
        *,
        event_id: str,
        account_id: str,
        amount: Decimal,
        booking_day: int,
        value_day: int,
        entry_type: EntryType,
        reference_id: str | None = None,
    ) -> LedgerEntry:
        account = self.account(account_id)
        if any(entry.event_id == event_id for entry in account.entries):
            raise ValueError(f"Duplicate event id for {account_id}: {event_id}")

        entry = LedgerEntry(
            event_id=event_id,
            account_id=account_id,
            amount=quantize_amount(amount, account.currency),
            booking_day=booking_day,
            value_day=value_day,
            entry_type=entry_type,
            reference_id=reference_id,
        )
        account.entries.append(entry)
        return entry

    def ledger_balance(self, account_id: str, value_day: int, as_of_booking_day: int | None = None) -> Decimal:
        """Return the balance for a value day using only entries known by as_of_booking_day.

        This supports both ordinary day-end views and historical recomputation after a
        back-valued event becomes known.
        """
        account = self.account(account_id)
        as_of = value_day if as_of_booking_day is None else as_of_booking_day
        balance = account.opening_balance
        for entry in account.entries:
            if entry.value_day <= value_day and entry.booking_day <= as_of:
                balance += entry.amount
        return quantize_amount(balance, account.currency)

    def closing_balance(self, account_id: str, day: int) -> Decimal:
        return self.ledger_balance(account_id, value_day=day, as_of_booking_day=day)

    def active_holds(self, account_id: str) -> Decimal:
        account = self.account(account_id)
        total = sum((auth.active_hold for auth in account.authorizations.values()), Decimal("0"))
        return quantize_amount(total, account.currency)

    def available_balance(self, account_id: str, day: int) -> Decimal:
        account = self.account(account_id)
        available = self.closing_balance(account_id, day) - self.active_holds(account_id)
        return quantize_amount(available, account.currency)

    def authorize(self, authorization_id: str, account_id: str, amount: Decimal, booking_day: int) -> Authorization:
        account = self.account(account_id)
        if authorization_id in account.authorizations:
            raise ValueError(f"Duplicate authorization id: {authorization_id}")

        amount = quantize_amount(amount, account.currency)
        proposed_available = self.available_balance(account_id, booking_day) - amount
        status = AuthorizationStatus.APPROVED if proposed_available >= Decimal("0") else AuthorizationStatus.DECLINED

        authorization = Authorization(
            authorization_id=authorization_id,
            account_id=account_id,
            amount=amount,
            booking_day=booking_day,
            status=status,
        )
        account.authorizations[authorization_id] = authorization
        return authorization

    def settle(
        self,
        *,
        event_id: str,
        authorization_id: str,
        account_id: str,
        amount: Decimal,
        booking_day: int,
        value_day: int,
    ) -> bool:
        account = self.account(account_id)
        authorization = account.authorizations.get(authorization_id)

        if authorization is None:
            self.errors.append(f"{event_id}: unknown authorization {authorization_id}; settlement rejected")
            return False
        if authorization.status != AuthorizationStatus.APPROVED:
            self.errors.append(
                f"{event_id}: authorization {authorization_id} is {authorization.status.value}; settlement rejected"
            )
            return False

        amount = quantize_amount(amount, account.currency)
        if amount > authorization.amount:
            self.errors.append(
                f"{event_id}: settlement {amount} exceeds authorization {authorization.amount}; settlement rejected"
            )
            return False

        self.append_entry(
            event_id=event_id,
            account_id=account_id,
            amount=-amount,
            booking_day=booking_day,
            value_day=value_day,
            entry_type=EntryType.SETTLEMENT,
            reference_id=authorization_id,
        )
        authorization.settled_amount = amount
        authorization.status = AuthorizationStatus.SETTLED
        return True

    def assess_overdraft_fee(
        self,
        *,
        event_id: str,
        account_id: str,
        booking_day: int,
        fee: Decimal,
        cause_event_id: str,
    ) -> bool:
        """Assess a fee on the processing day if the current closing balance is negative."""
        if self.closing_balance(account_id, booking_day) >= Decimal("0"):
            return False
        self.append_entry(
            event_id=event_id,
            account_id=account_id,
            amount=-fee,
            booking_day=booking_day,
            value_day=booking_day,
            entry_type=EntryType.FEE,
            reference_id=cause_event_id,
        )
        return True

    def accrue_interest(self, account_id: str, day: int, daily_rate: Decimal) -> Decimal:
        account = self.account(account_id)
        balance = self.closing_balance(account_id, day)
        raw = balance * daily_rate if balance > Decimal("0") else Decimal("0")
        amount = quantize_amount(raw, account.currency)
        self.daily_interest[(account_id, day)] = amount
        return amount

    def capitalize_interest(self, account_id: str, day: int, event_id: str) -> Decimal:
        account = self.account(account_id)
        total = sum(
            (amount for (acct_id, accrual_day), amount in self.daily_interest.items()
             if acct_id == account_id and accrual_day <= day),
            Decimal("0"),
        )
        total = quantize_amount(total, account.currency)
        if total != Decimal("0"):
            self.append_entry(
                event_id=event_id,
                account_id=account_id,
                amount=total,
                booking_day=day,
                value_day=day,
                entry_type=EntryType.INTEREST,
            )
        return total

from decimal import Decimal, ROUND_HALF_UP


CURRENCY_QUANTUM = {
    "AED": Decimal("0.01"),
    "BHD": Decimal("0.001"),
}


def quantize_amount(amount: Decimal, currency: str) -> Decimal:
    return amount.quantize(
        CURRENCY_QUANTUM[currency],
        rounding=ROUND_HALF_UP,
    )
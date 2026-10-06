from decimal import Decimal, ROUND_HALF_UP


CURRENCY_QUANTUM = {
    "AED": Decimal("0.01"),
    "BHD": Decimal("0.001"),
}


def quantize_amount(amount: Decimal, currency: str) -> Decimal:
    """Quantize a monetary amount to the currency's supported precision."""
    try:
        quantum = CURRENCY_QUANTUM[currency]
    except KeyError as exc:
        raise ValueError(f"Unsupported currency: {currency}") from exc
    return amount.quantize(quantum, rounding=ROUND_HALF_UP)


def split_amount(amount: Decimal, parts: int, currency: str) -> list[Decimal]:
    """Split an amount while conserving minor units exactly.

    Any remainder is allocated one minor unit at a time from the first part.
    For BHD 10.000 / 3 this yields 3.334, 3.333, 3.333.
    """
    if parts <= 0:
        raise ValueError("parts must be greater than zero")

    amount = quantize_amount(amount, currency)
    quantum = CURRENCY_QUANTUM[currency]
    units = int(amount / quantum)
    base_units, remainder = divmod(units, parts)

    return [
        (Decimal(base_units + (1 if index < remainder else 0)) * quantum).quantize(quantum)
        for index in range(parts)
    ]

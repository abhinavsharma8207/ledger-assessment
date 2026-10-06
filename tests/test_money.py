from decimal import Decimal

from ledger.money import quantize_amount, split_amount


def test_aed_rounding():
    assert quantize_amount(Decimal("1.005"), "AED") == Decimal("1.01")


def test_bhd_rounding():
    assert quantize_amount(Decimal("1.2345"), "BHD") == Decimal("1.235")


def test_bhd_split_conserves_amount():
    parts = split_amount(Decimal("10.000"), 3, "BHD")
    assert parts == [Decimal("3.334"), Decimal("3.333"), Decimal("3.333")]
    assert sum(parts, Decimal("0")) == Decimal("10.000")

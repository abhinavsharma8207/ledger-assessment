from decimal import Decimal

from ledger.money import quantize_amount


def test_aed_rounding():
    assert quantize_amount(Decimal("1.005"), "AED") == Decimal("1.01")


def test_bhd_rounding():
    assert quantize_amount(Decimal("1.2345"), "BHD") == Decimal("1.235")
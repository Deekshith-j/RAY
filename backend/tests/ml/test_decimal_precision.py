"""Financial Decimal Precision Tests per Section 5 & 13.

Verifies:
- Monetary calculations never use binary floating point
- Expected recovery: (Decimal(str(amount)) * Decimal(str(prob))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
- Exact precision across scale boundaries from ₹0.01 to ₹1 Crore
- No premature probability rounding
- Zero floating point rounding error in financial aggregations
"""

import pytest
from decimal import Decimal, ROUND_HALF_UP
from app.ml.schemas import calculate_expected_recovery
from app.core.financial import to_decimal, quantize_inr


def test_no_premature_probability_rounding_extended():
    """Verify that unrounded high-precision probability gives mathematically exact expected recovery."""
    amount = 24999.00
    prob_high_precision = 0.8374629158291

    # If rounded to 4 decimals (0.8375):
    # 24999 * 0.8375 = 20936.6625 -> 20936.66
    rounded_calc = (Decimal("24999.00") * Decimal("0.8375")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    assert rounded_calc == Decimal("20936.66")

    # True full precision:
    # 24999 * 0.8374629158291 = 20935.73543281167 -> 20935.74
    actual = calculate_expected_recovery(amount, prob_high_precision)
    assert actual == Decimal("20935.74")
    assert isinstance(actual, Decimal)


def test_monetary_edge_cases_quantization():
    """Verify edge monetary quantities and zero/penny amounts."""
    assert calculate_expected_recovery(0.01, 0.50) == Decimal("0.01")
    assert calculate_expected_recovery(0.01, 0.01) == Decimal("0.00")
    assert calculate_expected_recovery(999.99, 0.333333333) == Decimal("333.33")
    assert calculate_expected_recovery(50000.00, 0.777777777) == Decimal("38888.89")
    assert calculate_expected_recovery(75000.00, 0.85) == Decimal("63750.00")
    assert calculate_expected_recovery(10000000.00, 0.99999) == Decimal("9999900.00")


def test_quantize_inr_utility():
    """Verify quantize_inr utility consistently outputs Decimal with 2 decimal places."""
    assert quantize_inr("123.456") == Decimal("123.46")
    assert quantize_inr(123.454) == Decimal("123.45")
    assert quantize_inr(Decimal("50000")) == Decimal("50000.00")
    assert quantize_inr("0") == Decimal("0.00")

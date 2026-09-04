import pytest
from decimal import Decimal, ROUND_HALF_UP
from app.ml.schemas import calculate_expected_recovery


def test_full_precision_decimal_multiplication():
    """
    Verify that probability is NOT prematurely rounded before expected recovery calculation.
    Example from prompt:
    ₹10,000 × 0.913472183 -> ₹9,134.72
    """
    amount = 10000.0
    full_precision_prob = 0.913472183

    # If probability were prematurely rounded to 4 decimal places (0.9135):
    # 10000 * 0.9135 = 9135.00 (INCORRECT!)
    prematurely_rounded = Decimal("10000.00") * Decimal("0.9135")
    assert prematurely_rounded == Decimal("9135.00")

    # Correct full precision calculation:
    actual = calculate_expected_recovery(amount, full_precision_prob)
    assert actual == Decimal("9134.72")
    assert isinstance(actual, Decimal)


def test_exact_paise_quantization():
    """Verify exact 2-decimal-place monetary quantization using ROUND_HALF_UP."""
    # 24999.00 * 0.913472183 = 22835.891102817 -> 22835.89
    amount = 24999.00
    prob = 0.913472183

    expected = calculate_expected_recovery(amount, prob)
    assert expected == Decimal("22835.89")
    # Must never exceed the amount at risk
    assert expected <= Decimal(str(amount))


@pytest.mark.parametrize(
    "amount,prob,expected_str",
    [
        (0.01, 0.50, "0.01"),       # ₹0.01
        (0.10, 0.75, "0.08"),       # ₹0.10
        (999.99, 0.833333333, "833.32"),  # ₹999.99
        (24999.00, 0.565222405, "14129.99"),  # ₹24,999.00
        (50000.00, 0.666666666, "33333.33"),  # ₹50,000.00
        (75000.00, 0.90, "67500.00"),         # ₹75,000.00
        (10000000.00, 0.999999, "9999990.00"),  # ₹1,00,00,000.00 (₹1 Crore)
    ]
)
def test_edge_monetary_values_precision(amount, prob, expected_str):
    """Verify precision across all scale boundaries from 1 paisa to 1 crore."""
    result = calculate_expected_recovery(amount, prob)
    assert isinstance(result, Decimal)
    assert result == Decimal(expected_str)
    assert result <= Decimal(str(amount))


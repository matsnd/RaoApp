"""Unit tests for format_position_conditions_cascading function."""

from types import SimpleNamespace
from contracts.service import format_position_conditions_cascading
from contracts.models import PositionCondition
from reports.service import generate_fees_text, _format_fee_display


class MockCondition:
    """Mock PositionCondition for testing."""
    def __init__(self, period_count, rate1, rate2, billing_label):
        self.period_count = period_count
        self.rate1 = rate1
        self.rate2 = rate2
        self.billing_label = billing_label


def test_cascading_3_conditions_matches_old_app():
    """Test with 3 conditions matching the old WinForms app example."""
    conditions = [
        MockCondition(period_count=3, rate1=540, rate2=None, billing_label='doba'),
        MockCondition(period_count=16, rate1=410, rate2=None, billing_label='doba'),
        MockCondition(period_count=None, rate1=None, rate2=350, billing_label='doba'),
    ]
    result = format_position_conditions_cascading(conditions)
    expected = (
        "1 - 3 dni - 540,00 / doba\n"
        "4 - 16 dni - 410,00 / doba\n"
        "powyżej 16 dni - 350,00 / doba"
    )
    assert result == expected


def test_cascading_empty_list():
    """Test with empty conditions list."""
    conditions = []
    result = format_position_conditions_cascading(conditions)
    assert result == ""


def test_cascading_single_condition():
    """Test with single condition."""
    conditions = [
        MockCondition(period_count=7, rate1=500, rate2=None, billing_label='doba'),
    ]
    result = format_position_conditions_cascading(conditions)
    expected = "1 - 7 dni - 500,00 / doba"
    assert result == expected


def test_cascading_custom_billing_label():
    """Test with custom billing label."""
    conditions = [
        MockCondition(period_count=3, rate1=100, rate2=None, billing_label='godzina'),
        MockCondition(period_count=None, rate1=None, rate2=80, billing_label='godzina'),
    ]
    result = format_position_conditions_cascading(conditions)
    expected = (
        "1 - 3 dni - 100,00 / godzina\n"
        "powyżej 3 dni - 80,00 / godzina"
    )
    assert result == expected


# ── RAO-P1-100: KISS service-fee display ─────────────────────────────────────

class MockFee:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def test_generate_fees_text_uses_description_directly():
    """If description is filled, use it as the printed line (with polish separators)."""
    fee = MockFee(
        name="Transport", description="1 200,00 zł dostawa / 1 200,00 zł odbiór",
        is_active=True, sort_order=1, amount_from=None, amount_to=None, unit=None,
    )
    text = generate_fees_text([fee])
    assert text == "- Transport: 1 200,00 zł dostawa / 1 200,00 zł odbiór"


def test_generate_fees_text_fallback_to_amount():
    """If description empty, fallback to name + formatted amount."""
    fee = MockFee(
        name="Serwis", description="", is_active=True, sort_order=1,
        amount_from=280.00, amount_to=None, unit="wizyta",
    )
    text = generate_fees_text([fee])
    assert "- Serwis: 280,00 zł / wizyta" == text


def test_generate_fees_text_decimal_zero_not_falsy():
    """Decimal(0) must not hide the amount line."""
    from decimal import Decimal
    fee = MockFee(
        name="Czyszczenie", description="", is_active=True, sort_order=1,
        amount_from=Decimal("0.00"), amount_to=None, unit="sztuka",
    )
    text = generate_fees_text([fee])
    assert text == "- Czyszczenie: 0,00 zł / sztuka"


def test_format_fee_display_uses_description():
    fee = MockFee(
        name="Transport", description="1 200,00 zł dostawa / 1 200,00 zł odbiór",
        amount_from=None, amount_to=None, unit=None,
    )
    assert _format_fee_display(fee) == "- Transport: 1 200,00 zł dostawa / 1 200,00 zł odbiór"


def test_format_fee_display_replaces_placeholders():
    """Description placeholders $1/$2 are replaced with formatted amount + zł."""
    fee = MockFee(
        name="Transport", description="$1 dostawa / $2 odbiór",
        amount_from=1200.00, amount_to=1200.00, unit="dostawa",
    )
    display = _format_fee_display(fee)
    assert display == "- Transport: 1\u00a0200,00 zł dostawa / 1\u00a0200,00 zł odbiór"

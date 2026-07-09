"""Unit tests for format_position_conditions_cascading function."""

from decimal import Decimal
from contracts.service import format_position_conditions_cascading
from contracts.models import PositionCondition
from reports.service import generate_fees_text, _format_fee_display


class MockCondition:
    """Mock PositionCondition for testing (Phase 2 source fields)."""
    def __init__(self, period_from=None, period_to=None, rate1=None, rate2=None,
                 is_flat_rate=True, billing_label=None, period_count=None):
        self.period_from = period_from
        self.period_to = period_to
        self.rate1 = rate1
        self.rate2 = rate2
        self.is_flat_rate = is_flat_rate
        self.billing_label = billing_label
        self.period_count = period_count


def test_cascading_3_conditions_matches_old_app():
    """Test with 3 conditions converted to new period_from/period_to/rate1 fields.
    P1-101: ryczałt (is_flat_rate=True) → kwota całkowita, BEZ / unit."""
    conditions = [
        MockCondition(period_from=1, period_to=3, rate1=Decimal("540"), billing_label='doba'),
        MockCondition(period_from=4, period_to=16, rate1=Decimal("410"), billing_label='doba'),
        MockCondition(period_from=17, period_to=None, rate1=Decimal("350"), billing_label='doba'),
    ]
    result = format_position_conditions_cascading(conditions)
    expected = (
        "1 - 3 dni - 540,00zł\n"
        "4 - 16 dni - 410,00zł\n"
        "powyżej 16 dni - 350,00zł"
    )
    assert result == expected


def test_cascading_empty_list():
    """Test with empty conditions list."""
    conditions = []
    result = format_position_conditions_cascading(conditions)
    assert result == ""


def test_cascading_single_condition():
    """Test with single closed condition (ryczałt — no / unit)."""
    conditions = [
        MockCondition(period_from=1, period_to=7, rate1=Decimal("500"), billing_label='doba'),
    ]
    result = format_position_conditions_cascading(conditions)
    expected = "1 - 7 dni - 500,00zł"
    assert result == expected


def test_cascading_custom_billing_label():
    """Test with custom billing label (service hours, ryczałt).
    Legacy format: 'powyżej X godzin' for open-ended. Ryczałt → no / unit."""
    conditions = [
        MockCondition(period_from=1, period_to=3, rate1=Decimal("100"), billing_label='godzina'),
        MockCondition(period_from=4, period_to=None, rate1=Decimal("80"), billing_label='godzina'),
    ]
    result = format_position_conditions_cascading(conditions)
    expected = (
        "1 - 3 godzin - 100,00zł\n"
        "powyżej 3 godzin - 80,00zł"
    )
    assert result == expected


def test_service_open_ended_from_zero():
    """Service condition with period_from=0, ryczałt → 'do X godzin - {rate}zł' (no / unit)."""
    conditions = [
        MockCondition(period_from=0, period_to=8, rate1=Decimal("100"), billing_label='godzina'),
    ]
    result = format_position_conditions_cascading(conditions, contract_type='U')
    expected = "do 8 godzin - 100,00zł"
    assert result == expected


def test_service_stawka_from_zero():
    """P1-101: stawka (is_flat_rate=False) with period_from=0 → '0 - X godzin - {rate}zł / godzina'."""
    conditions = [
        MockCondition(period_from=0, period_to=8, rate1=Decimal("1450"), is_flat_rate=False, billing_label='godzina'),
    ]
    result = format_position_conditions_cascading(conditions, contract_type='U')
    expected = "0 - 8 godzin - 1450,00zł / godzina"
    assert result == expected


def test_legacy_rate2_fallback():
    """Legacy conditions using period_count/rate2 still render correctly.
    Ryczałt (default True) → no / unit."""
    conditions = [
        MockCondition(period_count=3, rate1=Decimal("540"), billing_label='doba'),
        MockCondition(period_count=16, rate1=Decimal("410"), billing_label='doba'),
        MockCondition(period_count=None, rate2=Decimal("350"), billing_label='doba'),
    ]
    result = format_position_conditions_cascading(conditions)
    expected = (
        "1 - 3 dni - 540,00zł\n"
        "4 - 16 dni - 410,00zł\n"
        "powyżej 16 dni - 350,00zł"
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
    """If description empty, fallback to name + formatted amount (no unit — RAO-P1-102)."""
    fee = MockFee(
        name="Serwis", description="", is_active=True, sort_order=1,
        amount_from=280.00, amount_to=None, unit="wizyta",
    )
    text = generate_fees_text([fee])
    assert "- Serwis: 280,00 zł" == text


def test_generate_fees_text_decimal_zero_not_falsy():
    """Decimal(0) must not hide the amount line."""
    from decimal import Decimal
    fee = MockFee(
        name="Czyszczenie", description="", is_active=True, sort_order=1,
        amount_from=Decimal("0.00"), amount_to=None, unit="sztuka",
    )
    text = generate_fees_text([fee])
    assert text == "- Czyszczenie: 0,00 zł"


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

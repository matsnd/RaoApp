"""Unit tests for format_position_conditions_cascading function."""

from contracts.service import format_position_conditions_cascading
from contracts.models import PositionCondition


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

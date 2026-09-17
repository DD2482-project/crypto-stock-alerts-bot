from app.conditions import is_triggered
from app.models import ConditionType


def test_price_rising_target_triggers_when_price_reaches_target():
    assert is_triggered(ConditionType.PRICE, target_value=110, base_price=100, current_price=110)
    assert not is_triggered(
        ConditionType.PRICE, target_value=110, base_price=100, current_price=109.99
    )


def test_price_falling_target_triggers_when_price_drops_to_target():
    assert is_triggered(ConditionType.PRICE, target_value=90, base_price=100, current_price=90)
    assert not is_triggered(
        ConditionType.PRICE, target_value=90, base_price=100, current_price=90.01
    )


def test_percent_positive_target_triggers_on_rise():
    assert is_triggered(ConditionType.PERCENT, target_value=5, base_price=100, current_price=105)
    assert not is_triggered(
        ConditionType.PERCENT, target_value=5, base_price=100, current_price=104.99
    )


def test_percent_negative_target_triggers_on_drop():
    assert is_triggered(ConditionType.PERCENT, target_value=-5, base_price=100, current_price=95)
    assert not is_triggered(
        ConditionType.PERCENT, target_value=-5, base_price=100, current_price=95.01
    )


def test_percent_with_zero_base_price_never_triggers():
    assert not is_triggered(ConditionType.PERCENT, target_value=5, base_price=0, current_price=10)

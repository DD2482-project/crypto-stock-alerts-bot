"""Pure alert-condition evaluation logic (no DB / network dependencies).

For PRICE conditions, the direction (alert on rise vs. drop) is inferred
from where the target sits relative to the price at subscribe time: a
target above the base price triggers on rise-to-or-above, a target below
triggers on drop-to-or-below.

For PERCENT conditions, target_value is a signed percentage: a positive
value triggers once the price has risen by at least that percent from the
base price, a negative value triggers once it has fallen by at least that
percent.
"""

from __future__ import annotations

from app.models import ConditionType


def is_triggered(
    condition_type: ConditionType,
    target_value: float,
    base_price: float,
    current_price: float,
) -> bool:
    if condition_type == ConditionType.PRICE:
        if target_value >= base_price:
            return current_price >= target_value
        return current_price <= target_value

    if condition_type == ConditionType.PERCENT:
        if base_price == 0:
            return False
        pct_change = (current_price - base_price) / base_price * 100
        if target_value >= 0:
            return pct_change >= target_value
        return pct_change <= target_value

    raise ValueError(f"Unknown condition type: {condition_type}")

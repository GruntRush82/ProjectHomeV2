"""Allowance tier calculation.

Rules (from DECISIONS.md #40):
  - 100% completion  → full allowance
  - >= 50% completion → half allowance
  - < 50% completion  → $0
"""


def calculate_allowance(
    total_chores: int, completed_chores: int, full_amount: float
) -> float:
    """Return earned allowance based on the 100/50/0 tier rule.

    Args:
        total_chores: total number of chores assigned this week
        completed_chores: number completed
        full_amount: the user's configured full weekly allowance

    Returns:
        Dollar amount earned (0, half, or full).
    """
    if total_chores == 0:
        return 0.0

    pct = completed_chores / total_chores

    if pct >= 1.0:
        return float(full_amount)
    if pct >= 0.5:
        return round(full_amount * 0.5, 2)
    return 0.0

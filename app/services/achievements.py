"""Achievement checking engine.

Called from blueprints at trigger points. Checks relevant achievements,
creates UserAchievement records with notified=False, and grants XP.
Returns newly unlocked achievements sorted gold-first.
"""

from flask import current_app

from app.extensions import db
from app.models.achievement import Achievement, UserAchievement
from app.models.bank import BankAccount, SavingsDeposit, SavingsGoal
from app.models.user import User
from app.services.xp import grant_xp

# Tier sort order: gold first, then silver, then bronze
_TIER_ORDER = {"gold": 0, "silver": 1, "bronze": 2}


def check_achievements(user_id: int, trigger: str, context: dict | None = None) -> list[dict]:
    """Check and unlock achievements for a trigger event.

    Args:
        user_id: The user to check achievements for.
        trigger: One of 'chore_complete', 'weekly_reset', 'savings_deposit',
                 'cashout', 'interest_credited', 'savings_goal_completed'.
        context: Optional extra data for the trigger.

    Returns:
        List of newly unlocked achievement dicts, sorted gold-first.
    """
    context = context or {}
    user = db.session.get(User, user_id)
    if not user:
        return []

    newly_unlocked = []

    if trigger == "chore_complete":
        newly_unlocked.extend(_check_first_chore(user))
    elif trigger == "weekly_reset":
        newly_unlocked.extend(_check_perfect_weeks(user))
        newly_unlocked.extend(_check_streak_milestones(user))
    elif trigger == "savings_deposit":
        newly_unlocked.extend(_check_first_deposit(user))
        newly_unlocked.extend(_check_savings_maxed(user))
    elif trigger == "cashout":
        newly_unlocked.extend(_check_first_cashout(user))
        newly_unlocked.extend(_check_big_spender(user))
    elif trigger == "interest_credited":
        newly_unlocked.extend(_check_interest_earner(user))
    elif trigger == "savings_goal_completed":
        newly_unlocked.extend(_check_goal_getter(user))

    # Sort: gold first, then silver, then bronze
    newly_unlocked.sort(key=lambda a: _TIER_ORDER.get(a["tier"], 99))

    return newly_unlocked


def _already_unlocked(user_id: int, achievement_name: str) -> bool:
    """Check if user already has this achievement."""
    achievement = Achievement.query.filter_by(name=achievement_name).first()
    if not achievement:
        return True  # If achievement doesn't exist, treat as unlocked (skip)
    return UserAchievement.query.filter_by(
        user_id=user_id, achievement_id=achievement.id
    ).first() is not None


def _unlock(user: User, achievement_name: str) -> dict | None:
    """Unlock an achievement for a user. Returns achievement dict or None."""
    achievement = Achievement.query.filter_by(name=achievement_name).first()
    if not achievement:
        return None

    # Already unlocked?
    existing = UserAchievement.query.filter_by(
        user_id=user.id, achievement_id=achievement.id
    ).first()
    if existing:
        return None

    ua = UserAchievement(
        user_id=user.id,
        achievement_id=achievement.id,
        notified=False,
    )
    db.session.add(ua)
    db.session.flush()

    # Grant XP reward
    if achievement.xp_reward > 0:
        grant_xp(user.id, achievement.xp_reward, f"achievement:{achievement.name}")

    return achievement.to_dict()


# ── Trigger checkers ────────────────────────────────────────────────

def _check_first_chore(user: User) -> list[dict]:
    """First Steps — complete any chore."""
    result = _unlock(user, "First Steps")
    return [result] if result else []


def _check_perfect_weeks(user: User) -> list[dict]:
    """Week Warrior (1 perfect week) and Chore Machine (4 perfect weeks)."""
    results = []
    if user.perfect_weeks_total >= 1:
        r = _unlock(user, "Week Warrior")
        if r:
            results.append(r)
    if user.perfect_weeks_total >= 4:
        r = _unlock(user, "Chore Machine")
        if r:
            results.append(r)
    return results


def _check_streak_milestones(user: User) -> list[dict]:
    """Check all streak milestones: 1/2/4/8/12 weeks."""
    milestones = [
        (1, "Streak Starter"),
        (2, "On Fire"),
        (4, "Unstoppable"),
        (8, "Legendary"),
        (12, "Immortal"),
    ]
    results = []
    for weeks, name in milestones:
        if user.streak_current >= weeks:
            r = _unlock(user, name)
            if r:
                results.append(r)
    return results


def _check_first_deposit(user: User) -> list[dict]:
    """Penny Saver — first savings deposit."""
    result = _unlock(user, "Penny Saver")
    return [result] if result else []


def _check_savings_maxed(user: User) -> list[dict]:
    """Savings Pro — savings maxed out."""
    savings_max = current_app.config.get("SAVINGS_MAX", 100.0)
    total = sum(
        d.amount for d in SavingsDeposit.query.filter_by(
            user_id=user.id, withdrawn=False
        ).all()
    )
    if total >= savings_max:
        result = _unlock(user, "Savings Pro")
        return [result] if result else []
    return []


def _check_first_cashout(user: User) -> list[dict]:
    """First Cashout — cash out for the first time."""
    result = _unlock(user, "First Cashout")
    return [result] if result else []


def _check_big_spender(user: User) -> list[dict]:
    """Big Spender — total cashed out >= $100."""
    account = BankAccount.query.filter_by(user_id=user.id).first()
    if account and account.total_cashed_out >= 100:
        result = _unlock(user, "Big Spender")
        return [result] if result else []
    return []


def _check_interest_earner(user: User) -> list[dict]:
    """Interest Earner — total interest >= $10."""
    account = BankAccount.query.filter_by(user_id=user.id).first()
    if account and account.total_interest_earned >= 10:
        result = _unlock(user, "Interest Earner")
        return [result] if result else []
    return []


def _check_goal_getter(user: User) -> list[dict]:
    """Goal Getter — completed a savings goal."""
    result = _unlock(user, "Goal Getter")
    return [result] if result else []

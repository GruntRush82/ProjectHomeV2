"""Seed the 14 achievement definitions — idempotent."""

from app.extensions import db
from app.models.achievement import Achievement


ACHIEVEMENT_DEFINITIONS = [
    # ── Chores ──
    {
        "name": "First Steps",
        "description": "Complete your first chore",
        "icon": "\u2705",
        "category": "chores",
        "requirement_type": "first_chore",
        "requirement_value": 1,
        "xp_reward": 25,
        "tier": "bronze",
        "display_order": 1,
    },
    {
        "name": "Week Warrior",
        "description": "Complete 100% of your chores in a week",
        "icon": "\u2b50",
        "category": "chores",
        "requirement_type": "perfect_weeks",
        "requirement_value": 1,
        "xp_reward": 100,
        "tier": "silver",
        "display_order": 2,
    },
    {
        "name": "Chore Machine",
        "description": "Complete 100% of your chores for 4 weeks total",
        "icon": "\u2699\ufe0f",
        "category": "chores",
        "requirement_type": "perfect_weeks",
        "requirement_value": 4,
        "xp_reward": 250,
        "tier": "gold",
        "display_order": 3,
    },
    # ── Streaks ──
    {
        "name": "Streak Starter",
        "description": "Achieve a 1-week streak of 100% completion",
        "icon": "\U0001f525",
        "category": "streaks",
        "requirement_type": "streak_weeks",
        "requirement_value": 1,
        "xp_reward": 50,
        "tier": "bronze",
        "display_order": 4,
    },
    {
        "name": "On Fire",
        "description": "Achieve a 2-week streak of 100% completion",
        "icon": "\U0001f525",
        "category": "streaks",
        "requirement_type": "streak_weeks",
        "requirement_value": 2,
        "xp_reward": 100,
        "tier": "silver",
        "display_order": 5,
    },
    {
        "name": "Unstoppable",
        "description": "Achieve a 4-week streak of 100% completion",
        "icon": "\U0001f4a5",
        "category": "streaks",
        "requirement_type": "streak_weeks",
        "requirement_value": 4,
        "xp_reward": 500,
        "tier": "gold",
        "display_order": 6,
    },
    {
        "name": "Legendary",
        "description": "Achieve an 8-week streak of 100% completion",
        "icon": "\U0001f451",
        "category": "streaks",
        "requirement_type": "streak_weeks",
        "requirement_value": 8,
        "xp_reward": 750,
        "tier": "gold",
        "display_order": 7,
    },
    {
        "name": "Immortal",
        "description": "Achieve a 12-week streak of 100% completion",
        "icon": "\u267e\ufe0f",
        "category": "streaks",
        "requirement_type": "streak_weeks",
        "requirement_value": 12,
        "xp_reward": 1000,
        "tier": "gold",
        "display_order": 8,
    },
    # ── Bank ──
    {
        "name": "Penny Saver",
        "description": "Make your first savings deposit",
        "icon": "\U0001f48e",
        "category": "bank",
        "requirement_type": "first_deposit",
        "requirement_value": 1,
        "xp_reward": 25,
        "tier": "bronze",
        "display_order": 9,
    },
    {
        "name": "Savings Pro",
        "description": "Max out your savings",
        "icon": "\U0001f3e6",
        "category": "bank",
        "requirement_type": "savings_maxed",
        "requirement_value": 1,
        "xp_reward": 200,
        "tier": "silver",
        "display_order": 10,
    },
    {
        "name": "First Cashout",
        "description": "Cash out for the first time",
        "icon": "\U0001f4b8",
        "category": "bank",
        "requirement_type": "first_cashout",
        "requirement_value": 1,
        "xp_reward": 25,
        "tier": "bronze",
        "display_order": 11,
    },
    {
        "name": "Big Spender",
        "description": "Cash out a total of $100 or more",
        "icon": "\U0001f4b0",
        "category": "bank",
        "requirement_type": "total_cashed_out",
        "requirement_value": 100,
        "xp_reward": 100,
        "tier": "silver",
        "display_order": 12,
    },
    {
        "name": "Interest Earner",
        "description": "Earn $10 or more in total interest",
        "icon": "\U0001f4c8",
        "category": "bank",
        "requirement_type": "total_interest",
        "requirement_value": 10,
        "xp_reward": 100,
        "tier": "silver",
        "display_order": 13,
    },
    {
        "name": "Goal Getter",
        "description": "Complete a savings goal",
        "icon": "\U0001f3af",
        "category": "bank",
        "requirement_type": "goal_completed",
        "requirement_value": 1,
        "xp_reward": 200,
        "tier": "silver",
        "display_order": 14,
    },
]


def seed_achievements():
    """Insert achievement definitions if they don't already exist."""
    created = 0
    for defn in ACHIEVEMENT_DEFINITIONS:
        existing = Achievement.query.filter_by(name=defn["name"]).first()
        if not existing:
            achievement = Achievement(**defn)
            db.session.add(achievement)
            created += 1

    if created:
        db.session.commit()
    return created


if __name__ == "__main__":
    from app import create_app

    app = create_app()
    with app.app_context():
        count = seed_achievements()
        print(f"Seeded {count} achievement definition(s).")

"""Seed mission definitions — Multiplication Master and Piano Performance."""

from app.extensions import db
from app.models.mission import Mission


MISSION_DEFINITIONS = [
    {
        "title": "Multiplication Master",
        "description": (
            "Master your multiplication tables from 1x1 to 12x12! "
            "Train with adaptive practice sessions, then pass three test levels "
            "to prove your skills and earn the Lightning Brain icon."
        ),
        "mission_type": "multiplication",
        "config": {
            "range_min": 1,
            "range_max": 12,
            "test_questions": 45,
            "levels": {
                "1": {"time_limit": None, "label": "Level 1 — No time limit"},
                "2": {"time_limit": 120, "label": "Level 2 — 2 minutes"},
                "3": {"time_limit": 60, "label": "Level 3 — 1 minute"},
            },
            "training_questions_per_session": 20,
        },
        "reward_cash": 50.0,
        "reward_icon": "lightning_brain",
    },
    {
        "title": "Piano Performance",
        "description": (
            "Learn and perform a piano piece! Practice on your own, "
            "then tell us when you're ready. An admin will listen to your "
            "performance and approve your mission completion."
        ),
        "mission_type": "piano",
        "config": {
            "piece_name": "Fur Elise",
            "description": "Play Fur Elise all the way through without mistakes",
            "verification": "admin_approval",
        },
        "reward_cash": 50.0,
        "reward_icon": "golden_music_note",
    },
]


def seed_missions():
    """Delete all existing missions and leave DB empty for admin to recreate.

    Admin will manually create missions with gem/XP selections via the admin UI.
    This function is intentionally a no-op seeder — it clears old seeds so
    the admin can define missions with the new reward fields.
    """
    deleted = Mission.query.count()
    if deleted > 0:
        Mission.query.delete()
        db.session.commit()
    return 0  # no missions seeded — admin will create via UI


if __name__ == "__main__":
    from app import create_app

    app = create_app()
    with app.app_context():
        count = seed_missions()
        print(f"Seeded {count} mission definition(s).")

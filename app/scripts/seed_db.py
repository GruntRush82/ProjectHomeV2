"""Seed the database from production_seed.json.

Usage:
    python -m app.scripts.seed_db          # Reset to clean production state
    python -m app.scripts.seed_db --export # Re-export current DB to production_seed.json

This gives you a clean DB with all users and chores (completed=False, xp=0,
balances=0, etc.) — ready for production or a fresh dev cycle.
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SEED_FILE = Path(__file__).resolve().parent / "production_seed.json"

sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.chore import Chore


def export_seed():
    """Export current users and chores to production_seed.json."""
    users = []
    for u in User.query.order_by(User.id).all():
        users.append({
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "allowance": u.allowance,
            "is_admin": u.is_admin,
            "icon": u.icon,
            "theme_color": u.theme_color,
        })

    chores = []
    for c in Chore.query.order_by(Chore.id).all():
        chores.append({
            "description": c.description,
            "user_id": c.user_id,
            "day": c.day,
            "rotation_type": c.rotation_type,
            "rotation_order": c.rotation_order or [],
            "base_user_id": c.base_user_id,
        })

    data = {"users": users, "chores": chores}
    with open(SEED_FILE, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Exported {len(users)} users and {len(chores)} chores to {SEED_FILE}")


def seed_db():
    """Drop all data and re-seed from production_seed.json."""
    if not SEED_FILE.exists():
        print(f"ERROR: {SEED_FILE} not found.")
        sys.exit(1)

    with open(SEED_FILE) as f:
        data = json.load(f)

    # Clear existing data (chores first due to FK)
    Chore.query.delete()
    User.query.delete()
    db.session.commit()

    # Insert users with explicit IDs
    for u in data["users"]:
        user = User(
            id=u["id"],
            username=u["username"],
            email=u.get("email"),
            allowance=u.get("allowance", 0),
            is_admin=u.get("is_admin", False),
            icon=u.get("icon", "question_mark"),
            theme_color=u.get("theme_color", "cyan"),
        )
        db.session.add(user)
    db.session.flush()

    # Insert chores (all completed=False for a fresh start)
    for c in data["chores"]:
        chore = Chore(
            description=c["description"],
            user_id=c["user_id"],
            day=c["day"],
            completed=False,
            rotation_type=c.get("rotation_type", "static"),
            rotation_order=c.get("rotation_order", []),
            base_user_id=c.get("base_user_id"),
        )
        db.session.add(chore)

    db.session.commit()
    print(f"Seeded {len(data['users'])} users and {len(data['chores'])} chores (all completed=False).")


def main():
    app = create_app()
    with app.app_context():
        if "--export" in sys.argv:
            export_seed()
        else:
            seed_db()


if __name__ == "__main__":
    main()

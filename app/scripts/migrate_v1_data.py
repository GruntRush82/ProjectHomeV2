"""One-time data migration: reporting_config.yaml -> User model.

Run with:
    python -m app.scripts.migrate_v1_data

This copies email and allowance from reporting_config.yaml into the
User table, and sets Travis as admin. Safe to run multiple times
(idempotent — only sets values if the user exists).
"""

import sys
from pathlib import Path

import yaml

# Ensure the project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app
from app.extensions import db
from app.models.user import User


def migrate_reporting_config():
    """Read reporting_config.yaml and update User rows."""
    config_path = PROJECT_ROOT / "reporting_config.yaml"
    if not config_path.exists():
        print(f"[skip] {config_path} not found — nothing to migrate.")
        return

    with open(config_path) as f:
        config = yaml.safe_load(f) or {}

    updated = 0
    for username, values in config.items():
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"[skip] User '{username}' not found in DB.")
            continue

        email = values.get("email", "")
        allowance = values.get("allowance", 0)

        user.email = email if email else user.email
        user.allowance = float(allowance) if allowance else user.allowance
        updated += 1
        print(f"[ok]   {username}: email={user.email}, allowance={user.allowance}")

    # Set Travis as admin
    travis = User.query.filter_by(username="Travis").first()
    if travis:
        travis.is_admin = True
        print(f"[ok]   Travis set as admin")
    else:
        print(f"[skip] User 'Travis' not found — admin not set")

    db.session.commit()
    print(f"\nMigration complete. Updated {updated} user(s).")


def main():
    app = create_app()
    with app.app_context():
        migrate_reporting_config()


if __name__ == "__main__":
    main()

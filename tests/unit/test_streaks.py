"""Tests for streak tracking logic."""
from app.models.user import User
from app.models.chore import Chore


class TestUpdateStreaks:
    """Streak updates based on chore completion percentage."""

    def test_100_percent_increments_streak(self, app, db, sample_users, sample_chores):
        """All chores completed -> streak_current increments."""
        kid = sample_users["kid1"]

        Chore.query.filter_by(user_id=kid.id).update({"completed": True})
        db.session.commit()

        from app.blueprints.chores import _update_streaks
        _update_streaks()
        db.session.commit()

        refreshed = db.session.get(User, kid.id)
        assert refreshed.streak_current == 1
        assert refreshed.streak_best == 1

    def test_partial_completion_resets_streak(self, app, db, sample_users, sample_chores):
        """Less than 100% -> streak resets to 0."""
        kid = sample_users["kid1"]

        # Set initial streak via direct update
        User.query.filter_by(id=kid.id).update(
            {"streak_current": 3, "streak_best": 5}
        )
        # Complete only the first chore
        first_chore = Chore.query.filter_by(user_id=kid.id).first()
        first_chore.completed = True
        db.session.commit()

        from app.blueprints.chores import _update_streaks
        _update_streaks()
        db.session.commit()

        refreshed = db.session.get(User, kid.id)
        assert refreshed.streak_current == 0
        assert refreshed.streak_best == 5  # Best unchanged

    def test_streak_best_updates_on_new_record(self, app, db, sample_users, sample_chores):
        """streak_best updates when streak_current surpasses it."""
        kid = sample_users["kid1"]

        User.query.filter_by(id=kid.id).update(
            {"streak_current": 4, "streak_best": 4}
        )
        Chore.query.filter_by(user_id=kid.id).update({"completed": True})
        db.session.commit()

        from app.blueprints.chores import _update_streaks
        _update_streaks()
        db.session.commit()

        refreshed = db.session.get(User, kid.id)
        assert refreshed.streak_current == 5
        assert refreshed.streak_best == 5

    def test_user_with_no_chores_skipped(self, app, db, sample_users):
        """Users with zero chores are not affected."""
        admin = sample_users["admin"]

        User.query.filter_by(id=admin.id).update({"streak_current": 2})
        db.session.commit()

        from app.blueprints.chores import _update_streaks
        _update_streaks()
        db.session.commit()

        refreshed = db.session.get(User, admin.id)
        assert refreshed.streak_current == 2  # Unchanged

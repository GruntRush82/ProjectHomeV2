"""Tests for Achievement and UserAchievement models + seed script."""

import pytest

from app.models.achievement import Achievement, UserAchievement
from app.models.user import User
from app.scripts.seed_achievements import seed_achievements, ACHIEVEMENT_DEFINITIONS


class TestAchievementModel:
    """Achievement catalog model tests."""

    def test_create_achievement(self, app, db):
        a = Achievement(
            name="Test Achievement",
            description="A test",
            icon="\u2b50",
            category="chores",
            requirement_type="first_chore",
            requirement_value=1,
            xp_reward=25,
            tier="bronze",
        )
        db.session.add(a)
        db.session.commit()
        assert a.id is not None
        assert a.name == "Test Achievement"
        assert a.tier == "bronze"

    def test_achievement_unique_name(self, app, db):
        a1 = Achievement(
            name="Unique", description="A", icon="X",
            category="chores", requirement_type="x", requirement_value=1,
            xp_reward=10, tier="bronze",
        )
        a2 = Achievement(
            name="Unique", description="B", icon="Y",
            category="bank", requirement_type="y", requirement_value=2,
            xp_reward=20, tier="silver",
        )
        db.session.add(a1)
        db.session.commit()
        db.session.add(a2)
        with pytest.raises(Exception):
            db.session.commit()
        db.session.rollback()

    def test_achievement_to_dict(self, app, db):
        a = Achievement(
            name="Dict Test", description="Desc", icon="\u2705",
            category="chores", requirement_type="first_chore",
            requirement_value=1, xp_reward=25, tier="bronze",
            display_order=5,
        )
        db.session.add(a)
        db.session.commit()
        d = a.to_dict()
        assert d["name"] == "Dict Test"
        assert d["xp_reward"] == 25
        assert d["display_order"] == 5


class TestUserAchievementModel:
    """UserAchievement per-user unlock tests."""

    def test_create_user_achievement(self, app, db, sample_users):
        a = Achievement(
            name="Test", description="T", icon="X",
            category="chores", requirement_type="first_chore",
            requirement_value=1, xp_reward=25, tier="bronze",
        )
        db.session.add(a)
        db.session.commit()

        ua = UserAchievement(
            user_id=sample_users["kid1"].id,
            achievement_id=a.id,
        )
        db.session.add(ua)
        db.session.commit()
        assert ua.id is not None
        assert ua.notified is False

    def test_unique_user_achievement(self, app, db, sample_users):
        a = Achievement(
            name="Uniq", description="T", icon="X",
            category="chores", requirement_type="x",
            requirement_value=1, xp_reward=10, tier="bronze",
        )
        db.session.add(a)
        db.session.commit()

        ua1 = UserAchievement(user_id=sample_users["kid1"].id, achievement_id=a.id)
        db.session.add(ua1)
        db.session.commit()

        ua2 = UserAchievement(user_id=sample_users["kid1"].id, achievement_id=a.id)
        db.session.add(ua2)
        with pytest.raises(Exception):
            db.session.commit()
        db.session.rollback()

    def test_user_achievement_to_dict(self, app, db, sample_users):
        a = Achievement(
            name="DictUA", description="T", icon="X",
            category="chores", requirement_type="x",
            requirement_value=1, xp_reward=10, tier="bronze",
        )
        db.session.add(a)
        db.session.commit()

        ua = UserAchievement(user_id=sample_users["kid1"].id, achievement_id=a.id)
        db.session.add(ua)
        db.session.commit()

        d = ua.to_dict()
        assert d["user_id"] == sample_users["kid1"].id
        assert d["achievement"]["name"] == "DictUA"
        assert d["notified"] is False


class TestSeedAchievements:
    """Seed script tests."""

    def test_seed_creates_all_achievements(self, app, db):
        count = seed_achievements()
        assert count == 17
        assert Achievement.query.count() == 17

    def test_seed_is_idempotent(self, app, db):
        seed_achievements()
        count2 = seed_achievements()
        assert count2 == 0
        assert Achievement.query.count() == 17

    def test_seed_has_correct_tiers(self, app, db):
        seed_achievements()
        bronze = Achievement.query.filter_by(tier="bronze").count()
        silver = Achievement.query.filter_by(tier="silver").count()
        gold = Achievement.query.filter_by(tier="gold").count()
        # bronze: First Steps, Streak Starter, Penny Saver, First Cashout,
        #         Privilege Unlocked, Calendar Explorer
        assert bronze == 6
        # silver: Week Warrior, On Fire, Savings Pro, Big Spender,
        #         Interest Earner, Goal Getter, Lifestyle Achiever
        assert silver == 7
        assert gold == 4    # Chore Machine, Unstoppable, Legendary, Immortal


class TestUserModelAdditions:
    """Test new User model fields."""

    def test_perfect_weeks_total_default(self, app, db):
        u = User(username="PerfTest")
        db.session.add(u)
        db.session.commit()
        assert u.perfect_weeks_total == 0

    def test_fire_mode_default(self, app, db):
        u = User(username="FireTest")
        db.session.add(u)
        db.session.commit()
        assert u.fire_mode is False

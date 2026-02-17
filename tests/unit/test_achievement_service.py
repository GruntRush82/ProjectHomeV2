"""Tests for the achievement checking engine."""

from app.models.achievement import Achievement, UserAchievement
from app.models.bank import BankAccount, SavingsDeposit, SavingsGoal
from app.models.user import User
from app.scripts.seed_achievements import seed_achievements
from app.services.achievements import check_achievements

from datetime import datetime, timedelta


class TestCheckAchievements:
    """Test achievement triggers."""

    def _seed(self, db):
        seed_achievements()

    def test_chore_complete_first_steps(self, app, db, sample_users):
        self._seed(db)
        kid = sample_users["kid1"]
        results = check_achievements(kid.id, "chore_complete")
        assert len(results) == 1
        assert results[0]["name"] == "First Steps"
        assert results[0]["tier"] == "bronze"

    def test_chore_complete_no_double_unlock(self, app, db, sample_users):
        self._seed(db)
        kid = sample_users["kid1"]
        check_achievements(kid.id, "chore_complete")
        results2 = check_achievements(kid.id, "chore_complete")
        assert len(results2) == 0

    def test_weekly_reset_perfect_week(self, app, db, sample_users):
        self._seed(db)
        kid = sample_users["kid1"]
        kid.perfect_weeks_total = 1
        kid.streak_current = 1
        db.session.commit()
        results = check_achievements(kid.id, "weekly_reset")
        names = [r["name"] for r in results]
        assert "Week Warrior" in names
        assert "Streak Starter" in names

    def test_weekly_reset_chore_machine(self, app, db, sample_users):
        self._seed(db)
        kid = sample_users["kid1"]
        kid.perfect_weeks_total = 4
        kid.streak_current = 4
        db.session.commit()
        results = check_achievements(kid.id, "weekly_reset")
        names = [r["name"] for r in results]
        assert "Chore Machine" in names
        assert "Unstoppable" in names

    def test_streak_milestones(self, app, db, sample_users):
        self._seed(db)
        kid = sample_users["kid1"]
        kid.streak_current = 12
        kid.perfect_weeks_total = 12
        db.session.commit()
        results = check_achievements(kid.id, "weekly_reset")
        names = [r["name"] for r in results]
        for milestone in ["Streak Starter", "On Fire", "Unstoppable", "Legendary", "Immortal"]:
            assert milestone in names

    def test_savings_deposit_penny_saver(self, app, db, sample_users):
        self._seed(db)
        kid = sample_users["kid1"]
        results = check_achievements(kid.id, "savings_deposit")
        assert len(results) == 1
        assert results[0]["name"] == "Penny Saver"

    def test_savings_maxed(self, app, db, sample_users):
        self._seed(db)
        kid = sample_users["kid1"]
        # Max out savings
        dep = SavingsDeposit(
            user_id=kid.id, amount=100.0,
            deposited_at=datetime.utcnow(),
            lock_until=datetime.utcnow() + timedelta(days=30),
            interest_rate=0.05,
        )
        db.session.add(dep)
        db.session.commit()

        results = check_achievements(kid.id, "savings_deposit")
        names = [r["name"] for r in results]
        assert "Savings Pro" in names

    def test_cashout_achievements(self, app, db, sample_users):
        self._seed(db)
        kid = sample_users["kid1"]
        account = BankAccount(user_id=kid.id, total_cashed_out=150.0)
        db.session.add(account)
        db.session.commit()

        results = check_achievements(kid.id, "cashout")
        names = [r["name"] for r in results]
        assert "First Cashout" in names
        assert "Big Spender" in names

    def test_interest_earner(self, app, db, sample_users):
        self._seed(db)
        kid = sample_users["kid1"]
        account = BankAccount(user_id=kid.id, total_interest_earned=15.0)
        db.session.add(account)
        db.session.commit()

        results = check_achievements(kid.id, "interest_credited")
        assert len(results) == 1
        assert results[0]["name"] == "Interest Earner"

    def test_goal_getter(self, app, db, sample_users):
        self._seed(db)
        kid = sample_users["kid1"]
        results = check_achievements(kid.id, "savings_goal_completed")
        assert len(results) == 1
        assert results[0]["name"] == "Goal Getter"

    def test_gold_first_sorting(self, app, db, sample_users):
        """Gold achievements should sort before silver and bronze."""
        self._seed(db)
        kid = sample_users["kid1"]
        kid.perfect_weeks_total = 4
        kid.streak_current = 4
        db.session.commit()

        results = check_achievements(kid.id, "weekly_reset")
        # Chore Machine (gold) and Unstoppable (gold) should come before
        # Week Warrior (silver) and others
        tiers = [r["tier"] for r in results]
        for i in range(len(tiers) - 1):
            tier_order = {"gold": 0, "silver": 1, "bronze": 2}
            assert tier_order[tiers[i]] <= tier_order[tiers[i + 1]]

    def test_achievement_xp_granted(self, app, db, sample_users):
        """Unlocking an achievement should grant its XP reward."""
        self._seed(db)
        kid = sample_users["kid1"]
        assert kid.xp == 0
        check_achievements(kid.id, "chore_complete")  # First Steps = 25 XP
        db.session.refresh(kid)
        assert kid.xp == 25

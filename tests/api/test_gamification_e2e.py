"""End-to-end gamification tests — full flows across chores, bank, achievements."""

from datetime import date, datetime, timedelta

from app.extensions import db
from app.models.achievement import Achievement, UserAchievement
from app.models.bank import BankAccount, SavingsDeposit, SavingsGoal, Transaction
from app.models.chore import Chore, ChoreHistory
from app.models.user import User
from app.scripts.seed_achievements import seed_achievements


class TestFullWeekCycle:
    """Complete chores → weekly reset → XP + achievements."""

    def test_chore_xp_accumulation(self, app, logged_in_client, sample_users, sample_chores):
        """Completing 5 chores should accumulate XP correctly."""
        seed_achievements()
        kid_id = sample_users["kid1"].id
        client = logged_in_client(user_id=kid_id)

        # Complete all 4 chores for kid1 (3 static + 1 rotating)
        total_xp = 0
        for chore in Chore.query.filter_by(user_id=kid_id).all():
            resp = client.put(f"/chores/{chore.id}",
                              json={"completed": True},
                              content_type="application/json")
            data = resp.get_json()
            total_xp += data["xp"]["xp_granted"]

        # 3 static(10) + 1 rotating(25) = 55
        assert total_xp == 55

        kid = db.session.get(User, kid_id)
        # 55 chore XP + 25 First Steps achievement XP
        assert kid.xp == 80

    def test_weekly_100_percent_bonus(self, app, logged_in_client, sample_users, sample_chores):
        """100% week doubles chore XP via bonus."""
        seed_achievements()
        kid_id = sample_users["kid1"].id
        client = logged_in_client(user_id=kid_id)

        # Complete all chores via direct DB (skip individual XP for cleaner test)
        for chore in Chore.query.filter_by(user_id=kid_id).all():
            chore.completed = True
        db.session.commit()

        ChoreHistory.query.filter_by(date=date.today()).delete()
        db.session.commit()

        client.post("/chores/reset", json={}, content_type="application/json")

        kid = db.session.get(User, kid_id)
        # Weekly bonus = 3*10 + 1*25 = 55 XP
        # Plus achievement XP (Week Warrior 100 + Streak Starter 50 = 150)
        assert kid.xp >= 55
        assert kid.perfect_weeks_total == 1
        assert kid.streak_current == 1

    def test_streak_progression(self, app, logged_in_client, sample_users, sample_chores):
        """Simulate 2 consecutive perfect weeks → streak achievements."""
        seed_achievements()
        kid_id = sample_users["kid1"].id
        kid = db.session.get(User, kid_id)
        kid.streak_current = 1
        kid.perfect_weeks_total = 1
        db.session.commit()

        client = logged_in_client(user_id=kid_id)

        # Week 2: complete all chores
        for chore in Chore.query.filter_by(user_id=kid_id).all():
            chore.completed = True
        db.session.commit()

        ChoreHistory.query.filter_by(date=date.today()).delete()
        db.session.commit()

        client.post("/chores/reset", json={}, content_type="application/json")

        kid = db.session.get(User, kid_id)
        assert kid.streak_current == 2
        assert kid.perfect_weeks_total == 2

        # Check streak achievements unlocked
        unlocked = [
            ua.achievement.name for ua in
            UserAchievement.query.filter_by(user_id=kid_id).all()
        ]
        assert "Streak Starter" in unlocked
        assert "On Fire" in unlocked


class TestBankAchievementChain:
    """Bank achievement chain: deposit → Penny Saver, cashout → First Cashout."""

    def test_deposit_then_cashout_chain(self, app, logged_in_client, sample_users):
        seed_achievements()
        kid_id = sample_users["kid1"].id
        account = BankAccount(user_id=kid_id, cash_balance=50.0)
        db.session.add(account)
        db.session.commit()

        client = logged_in_client(user_id=kid_id)

        # Deposit
        resp = client.post("/bank/savings/deposit",
                           json={"amount": 5.0},
                           content_type="application/json")
        data = resp.get_json()
        deposit_achievements = [a["name"] for a in data.get("achievements", [])]
        assert "Penny Saver" in deposit_achievements

        # Cashout remaining cash
        resp = client.post("/bank/cashout",
                           json={}, content_type="application/json")
        data = resp.get_json()
        cashout_achievements = [a["name"] for a in data.get("achievements", [])]
        assert "First Cashout" in cashout_achievements


class TestMultipleAchievementsInOneAction:
    """Multiple achievements unlocking from a single trigger."""

    def test_weekly_reset_multiple_achievements(self, app, logged_in_client, sample_users, sample_chores):
        """A user at streak=3 completing a 4th perfect week should unlock
        Unstoppable + Chore Machine in the same reset."""
        seed_achievements()
        kid_id = sample_users["kid1"].id
        kid = db.session.get(User, kid_id)
        kid.streak_current = 3
        kid.perfect_weeks_total = 3
        db.session.commit()

        client = logged_in_client(user_id=kid_id)

        for chore in Chore.query.filter_by(user_id=kid_id).all():
            chore.completed = True
        db.session.commit()

        ChoreHistory.query.filter_by(date=date.today()).delete()
        db.session.commit()

        client.post("/chores/reset", json={}, content_type="application/json")

        unlocked = [
            ua.achievement.name for ua in
            UserAchievement.query.filter_by(user_id=kid_id).all()
        ]
        assert "Unstoppable" in unlocked
        assert "Chore Machine" in unlocked


class TestLevelUpFromAchievementXP:
    """Achievement XP can trigger a level-up."""

    def test_achievement_xp_causes_level_up(self, app, logged_in_client, sample_users, sample_chores):
        """User at 190 XP completing a chore should get First Steps (25 XP)
        and level up to 2."""
        seed_achievements()
        kid_id = sample_users["kid1"].id
        kid = db.session.get(User, kid_id)
        kid.xp = 165  # 165 + 10 (chore) + 25 (First Steps) = 200 = Level 2
        db.session.commit()

        client = logged_in_client(user_id=kid_id)
        chore = Chore.query.filter_by(user_id=kid_id, rotation_type="static").first()

        resp = client.put(f"/chores/{chore.id}",
                          json={"completed": True},
                          content_type="application/json")
        data = resp.get_json()

        kid = db.session.get(User, kid_id)
        assert kid.xp == 200
        assert kid.level == 2


class TestFireModeFullCycle:
    """Fire Mode activation, deactivation, and allowance boost."""

    def test_fire_mode_activates_at_3_weeks(self, app, logged_in_client, sample_users, sample_chores):
        seed_achievements()
        kid_id = sample_users["kid1"].id
        kid = db.session.get(User, kid_id)
        kid.streak_current = 2
        kid.perfect_weeks_total = 2
        db.session.commit()

        client = logged_in_client(user_id=kid_id)

        for chore in Chore.query.filter_by(user_id=kid_id).all():
            chore.completed = True
        db.session.commit()

        ChoreHistory.query.filter_by(date=date.today()).delete()
        db.session.commit()

        client.post("/chores/reset", json={}, content_type="application/json")

        kid = db.session.get(User, kid_id)
        assert kid.fire_mode is True
        assert kid.streak_current == 3

    def test_fire_mode_deactivates_on_break(self, app, logged_in_client, sample_users, sample_chores):
        seed_achievements()
        kid_id = sample_users["kid1"].id
        kid = db.session.get(User, kid_id)
        kid.streak_current = 4
        kid.fire_mode = True
        db.session.commit()

        client = logged_in_client(user_id=kid_id)

        # Don't complete chores → streak breaks
        ChoreHistory.query.filter_by(date=date.today()).delete()
        db.session.commit()

        client.post("/chores/reset", json={}, content_type="application/json")

        kid = db.session.get(User, kid_id)
        assert kid.fire_mode is False
        assert kid.streak_current == 0

    def test_fire_mode_50_percent_allowance_boost(self, app, logged_in_client, sample_users, sample_chores):
        """Fire mode user at 100% should get 1.5x allowance."""
        seed_achievements()
        kid_id = sample_users["kid1"].id
        kid = db.session.get(User, kid_id)
        kid.streak_current = 2
        kid.allowance = 20.0
        db.session.commit()

        client = logged_in_client(user_id=kid_id)

        for chore in Chore.query.filter_by(user_id=kid_id).all():
            chore.completed = True
        db.session.commit()

        ChoreHistory.query.filter_by(date=date.today()).delete()
        db.session.commit()

        client.post("/chores/reset", json={}, content_type="application/json")

        kid = db.session.get(User, kid_id)
        assert kid.fire_mode is True

        txn = Transaction.query.filter_by(
            user_id=kid_id, type=Transaction.TYPE_ALLOWANCE
        ).first()
        assert txn is not None
        assert txn.amount == 30.0  # $20 * 1.5


class TestNotificationQueue:
    """Achievement notification queue returns gold-first."""

    def test_notification_queue_gold_first(self, app, logged_in_client, sample_users):
        seed_achievements()
        kid_id = sample_users["kid1"].id

        bronze = Achievement.query.filter_by(name="First Steps").first()
        silver = Achievement.query.filter_by(name="Week Warrior").first()
        gold = Achievement.query.filter_by(name="Chore Machine").first()

        for a in [bronze, silver, gold]:
            db.session.add(UserAchievement(
                user_id=kid_id, achievement_id=a.id, notified=False
            ))
        db.session.commit()

        client = logged_in_client(user_id=kid_id)
        resp = client.get("/api/achievements/notifications")
        data = resp.get_json()

        tiers = [n["achievement"]["tier"] for n in data["notifications"]]
        assert tiers == ["gold", "silver", "bronze"]

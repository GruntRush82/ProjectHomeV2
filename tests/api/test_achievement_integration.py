"""Integration tests for gamification hooks in chores, bank, missions."""

from datetime import date, datetime, timedelta

from app.extensions import db
from app.models.bank import BankAccount, SavingsDeposit, Transaction
from app.models.chore import Chore, ChoreHistory
from app.models.user import User
from app.scripts.seed_achievements import seed_achievements


class TestChoreXP:
    """XP grants on chore completion."""

    def test_static_chore_grants_10_xp(self, app, logged_in_client, sample_users, sample_chores):
        seed_achievements()
        kid = sample_users["kid1"]
        client = logged_in_client(user_id=kid.id)
        chore = Chore.query.filter_by(user_id=kid.id, rotation_type="static").first()

        resp = client.put(f"/chores/{chore.id}",
                          json={"completed": True},
                          content_type="application/json")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["xp"]["xp_granted"] == 10

    def test_rotating_chore_grants_25_xp(self, app, logged_in_client, sample_users, sample_chores):
        seed_achievements()
        kid = sample_users["kid1"]
        client = logged_in_client(user_id=kid.id)
        chore = Chore.query.filter_by(user_id=kid.id, rotation_type="rotating").first()

        resp = client.put(f"/chores/{chore.id}",
                          json={"completed": True},
                          content_type="application/json")
        data = resp.get_json()
        assert data["xp"]["xp_granted"] == 25

    def test_no_xp_on_undo(self, app, logged_in_client, sample_users, sample_chores):
        """Unchecking a chore should not deduct XP."""
        seed_achievements()
        kid_id = sample_users["kid1"].id
        client = logged_in_client(user_id=kid_id)
        chore = Chore.query.filter_by(user_id=kid_id, rotation_type="static").first()
        chore_id = chore.id

        # Complete
        client.put(f"/chores/{chore_id}", json={"completed": True},
                   content_type="application/json")
        xp_after_complete = db.session.get(User, kid_id).xp

        # Undo
        resp = client.put(f"/chores/{chore_id}", json={"completed": False},
                          content_type="application/json")
        data = resp.get_json()
        assert "xp" not in data  # No XP action on undo
        assert db.session.get(User, kid_id).xp == xp_after_complete

    def test_first_chore_achievement(self, app, logged_in_client, sample_users, sample_chores):
        seed_achievements()
        kid = sample_users["kid1"]
        client = logged_in_client(user_id=kid.id)
        chore = Chore.query.filter_by(user_id=kid.id, rotation_type="static").first()

        resp = client.put(f"/chores/{chore.id}", json={"completed": True},
                          content_type="application/json")
        data = resp.get_json()
        assert len(data["achievements"]) == 1
        assert data["achievements"][0]["name"] == "First Steps"


class TestWeeklyReset:
    """Weekly reset XP bonus, streak achievements, Fire Mode."""

    def test_perfect_week_bonus_xp(self, app, logged_in_client, sample_users, sample_chores):
        """100% week should grant bonus XP equal to chore XP."""
        seed_achievements()
        kid_id = sample_users["kid1"].id
        client = logged_in_client(user_id=kid_id)

        # Complete all kid1's chores (3 static + 1 rotating = 4)
        for chore in Chore.query.filter_by(user_id=kid_id).all():
            chore.completed = True
        db.session.commit()

        ChoreHistory.query.filter_by(date=date.today()).delete()
        db.session.commit()

        resp = client.post("/chores/reset", json={}, content_type="application/json")
        assert resp.status_code == 200

        kid = db.session.get(User, kid_id)
        # Bonus XP = 3 static(10 each) + 1 rotating(25) = 55
        assert kid.xp >= 55  # At least the bonus XP (plus achievement XP)

    def test_streak_updates_fire_mode(self, app, logged_in_client, sample_users, sample_chores):
        """Fire mode activates at 3+ consecutive perfect weeks."""
        seed_achievements()
        kid_id = sample_users["kid1"].id
        kid = db.session.get(User, kid_id)
        kid.streak_current = 2
        db.session.commit()
        client = logged_in_client(user_id=kid_id)

        for chore in Chore.query.filter_by(user_id=kid_id).all():
            chore.completed = True
        db.session.commit()

        ChoreHistory.query.filter_by(date=date.today()).delete()
        db.session.commit()

        client.post("/chores/reset", json={}, content_type="application/json")

        kid = db.session.get(User, kid_id)
        assert kid.streak_current == 3
        assert kid.fire_mode is True

    def test_fire_mode_deactivates_on_break(self, app, logged_in_client, sample_users, sample_chores):
        """Fire mode deactivates when streak breaks."""
        seed_achievements()
        kid_id = sample_users["kid1"].id
        kid = db.session.get(User, kid_id)
        kid.streak_current = 3
        kid.fire_mode = True
        db.session.commit()
        client = logged_in_client(user_id=kid_id)

        ChoreHistory.query.filter_by(date=date.today()).delete()
        db.session.commit()

        client.post("/chores/reset", json={}, content_type="application/json")

        kid = db.session.get(User, kid_id)
        assert kid.streak_current == 0
        assert kid.fire_mode is False

    def test_fire_mode_allowance_boost(self, app, logged_in_client, sample_users, sample_chores):
        """Fire Mode should give 50% allowance boost."""
        seed_achievements()
        kid_id = sample_users["kid1"].id
        kid = db.session.get(User, kid_id)
        kid.streak_current = 2
        kid.allowance = 10.0
        db.session.commit()
        client = logged_in_client(user_id=kid_id)

        for chore in Chore.query.filter_by(user_id=kid_id).all():
            chore.completed = True
        db.session.commit()

        ChoreHistory.query.filter_by(date=date.today()).delete()
        db.session.commit()

        client.post("/chores/reset", json={}, content_type="application/json")

        kid = db.session.get(User, kid_id)
        assert kid.fire_mode is True  # Now at 3 weeks

        # Check allowance transaction — should be $15 (10 * 1.5)
        txn = Transaction.query.filter_by(
            user_id=kid_id, type=Transaction.TYPE_ALLOWANCE
        ).first()
        assert txn is not None
        assert txn.amount == 15.0
        assert "FIRE MODE" in txn.description


class TestBankAchievements:
    """Achievement checks in bank operations."""

    def test_cashout_achievement(self, app, logged_in_client, sample_users):
        seed_achievements()
        kid_id = sample_users["kid1"].id
        account = BankAccount(user_id=kid_id, cash_balance=50.0)
        db.session.add(account)
        db.session.commit()

        client = logged_in_client(user_id=kid_id)
        resp = client.post("/bank/cashout",
                           json={}, content_type="application/json")
        data = resp.get_json()
        assert "achievements" in data
        names = [a["name"] for a in data["achievements"]]
        assert "First Cashout" in names

    def test_savings_deposit_achievement(self, app, logged_in_client, sample_users):
        seed_achievements()
        kid_id = sample_users["kid1"].id
        account = BankAccount(user_id=kid_id, cash_balance=50.0)
        db.session.add(account)
        db.session.commit()

        client = logged_in_client(user_id=kid_id)
        resp = client.post("/bank/savings/deposit",
                           json={"amount": 5.0},
                           content_type="application/json")
        data = resp.get_json()
        assert "achievements" in data
        names = [a["name"] for a in data["achievements"]]
        assert "Penny Saver" in names


class TestMissionXP:
    """Mission completion grants XP."""

    def test_mission_reward_grants_xp(self, app, db, sample_users):
        """_grant_mission_reward should grant 500 XP."""
        from app.models.mission import Mission, MissionAssignment
        from app.blueprints.missions import _grant_mission_reward

        kid = sample_users["kid1"]
        mission = Mission(
            title="Test Mission", description="Test",
            mission_type="multiplication",
            config={}, reward_cash=10.0, reward_icon="test_icon",
        )
        db.session.add(mission)
        db.session.commit()

        assignment = MissionAssignment(
            mission_id=mission.id, user_id=kid.id,
            state=MissionAssignment.STATE_COMPLETED,
        )
        db.session.add(assignment)
        db.session.commit()

        _grant_mission_reward(assignment)

        db.session.refresh(kid)
        assert kid.xp == 500

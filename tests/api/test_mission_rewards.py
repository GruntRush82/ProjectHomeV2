"""Tests for mission reward fields, gem assignment, and admin undo — Feature 3."""
import pytest

from app.models.mission import Mission, MissionAssignment
from app.models.bank import BankAccount, Transaction
from app.models.user import User


@pytest.fixture
def mission_with_rewards(app, db, sample_users):
    """A Mission with all reward fields populated."""
    with app.app_context():
        mission = Mission(
            title="Test Gem Mission",
            description="A test mission",
            mission_type="piano",
            reward_cash=5.00,
            reward_icon="🎵",
            reward_xp=300,
            reward_description="You earned the ruby gem!",
            gem_type="ruby",
            gem_size="medium",
        )
        db.session.add(mission)
        db.session.commit()
        yield mission


@pytest.fixture
def assignment_for_kid(app, db, sample_users, mission_with_rewards):
    """An assigned MissionAssignment for kid1."""
    with app.app_context():
        kid = db.session.get(User, sample_users["kid1"].id)
        mission = db.session.get(Mission, mission_with_rewards.id)
        # Ensure bank account exists
        if not BankAccount.query.filter_by(user_id=kid.id).first():
            db.session.add(BankAccount(user_id=kid.id, cash_balance=0))
        assignment = MissionAssignment(
            mission_id=mission.id,
            user_id=kid.id,
            state=MissionAssignment.STATE_ASSIGNED,
            current_level=0,
        )
        db.session.add(assignment)
        db.session.commit()
        yield assignment


class TestMissionRewardFields:
    def test_mission_has_reward_xp(self, app, db, mission_with_rewards):
        with app.app_context():
            m = db.session.get(Mission, mission_with_rewards.id)
            assert m.reward_xp == 300

    def test_mission_has_gem_type(self, app, db, mission_with_rewards):
        with app.app_context():
            m = db.session.get(Mission, mission_with_rewards.id)
            assert m.gem_type == "ruby"

    def test_mission_has_gem_size(self, app, db, mission_with_rewards):
        with app.app_context():
            m = db.session.get(Mission, mission_with_rewards.id)
            assert m.gem_size == "medium"

    def test_mission_has_reward_description(self, app, db, mission_with_rewards):
        with app.app_context():
            m = db.session.get(Mission, mission_with_rewards.id)
            assert m.reward_description == "You earned the ruby gem!"

    def test_mission_to_dict_includes_reward_fields(
        self, app, db, mission_with_rewards
    ):
        with app.app_context():
            m = db.session.get(Mission, mission_with_rewards.id)
            d = m.to_dict()
            assert d["reward_xp"] == 300
            assert d["gem_type"] == "ruby"
            assert d["gem_size"] == "medium"
            assert d["reward_description"] == "You earned the ruby gem!"


class TestAdminEditMission:
    def test_admin_can_edit_reward_fields(
        self, admin_client, app, db, mission_with_rewards
    ):
        mid = mission_with_rewards.id
        resp = admin_client.put(
            f"/api/admin/missions/{mid}",
            json={
                "reward_xp": 750,
                "reward_description": "Updated description",
                "gem_type": "diamond",
                "gem_size": "large",
            },
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["reward_xp"] == 750
        assert data["gem_type"] == "diamond"

    def test_invalid_gem_type_returns_400(
        self, admin_client, app, db, mission_with_rewards
    ):
        mid = mission_with_rewards.id
        resp = admin_client.put(
            f"/api/admin/missions/{mid}",
            json={"gem_type": "obsidian"},
        )
        assert resp.status_code == 400

    def test_invalid_gem_size_returns_400(
        self, admin_client, app, db, mission_with_rewards
    ):
        mid = mission_with_rewards.id
        resp = admin_client.put(
            f"/api/admin/missions/{mid}",
            json={"gem_size": "giant"},
        )
        assert resp.status_code == 400


class TestAdminUndoMission:
    def _complete_assignment(self, app, db, assignment, mission):
        """Fast-track an assignment to completed state and grant reward."""
        # Already inside the app context from the `app` fixture — no nesting
        a = db.session.get(MissionAssignment, assignment.id)
        m = db.session.get(Mission, mission.id)
        user = db.session.get(User, a.user_id)

        # Grant XP
        user.xp = (user.xp or 0) + m.reward_xp
        user.level = 2

        # Grant cash
        account = BankAccount.query.filter_by(user_id=user.id).first()
        account.cash_balance += m.reward_cash
        db.session.add(Transaction(
            user_id=user.id,
            type=Transaction.TYPE_MISSION_REWARD,
            amount=m.reward_cash,
            balance_after=account.cash_balance,
            description=f"Mission reward: {m.title}",
        ))

        a.state = MissionAssignment.STATE_COMPLETED
        a.current_level = 3
        db.session.commit()

    def test_undo_reverts_state_to_assigned(
        self, admin_client, app, db, assignment_for_kid, mission_with_rewards
    ):
        self._complete_assignment(app, db, assignment_for_kid, mission_with_rewards)
        aid = assignment_for_kid.id
        resp = admin_client.post(f"/api/admin/missions/{aid}/undo")
        assert resp.status_code == 200
        with app.app_context():
            a = db.session.get(MissionAssignment, aid)
            assert a.state == MissionAssignment.STATE_ASSIGNED
            assert a.current_level == 0
            assert a.completed_at is None

    def test_undo_deducts_xp(
        self, admin_client, app, db, assignment_for_kid, mission_with_rewards
    ):
        self._complete_assignment(app, db, assignment_for_kid, mission_with_rewards)
        aid = assignment_for_kid.id
        uid = assignment_for_kid.user_id
        with app.app_context():
            xp_before = db.session.get(User, uid).xp

        admin_client.post(f"/api/admin/missions/{aid}/undo")

        with app.app_context():
            xp_after = db.session.get(User, uid).xp
            assert xp_after == xp_before - mission_with_rewards.reward_xp

    def test_undo_deducts_cash(
        self, admin_client, app, db, assignment_for_kid, mission_with_rewards
    ):
        self._complete_assignment(app, db, assignment_for_kid, mission_with_rewards)
        aid = assignment_for_kid.id
        uid = assignment_for_kid.user_id
        with app.app_context():
            acct = BankAccount.query.filter_by(user_id=uid).first()
            cash_before = acct.cash_balance

        admin_client.post(f"/api/admin/missions/{aid}/undo")

        with app.app_context():
            acct = BankAccount.query.filter_by(user_id=uid).first()
            assert acct.cash_balance == pytest.approx(
                cash_before - mission_with_rewards.reward_cash, abs=0.01
            )

    def test_undo_on_non_completed_returns_400(
        self, admin_client, app, db, assignment_for_kid
    ):
        aid = assignment_for_kid.id
        resp = admin_client.post(f"/api/admin/missions/{aid}/undo")
        assert resp.status_code == 400

    def test_undo_creates_negative_transaction(
        self, admin_client, app, db, assignment_for_kid, mission_with_rewards
    ):
        self._complete_assignment(app, db, assignment_for_kid, mission_with_rewards)
        aid = assignment_for_kid.id
        uid = assignment_for_kid.user_id
        admin_client.post(f"/api/admin/missions/{aid}/undo")
        with app.app_context():
            neg_txn = Transaction.query.filter(
                Transaction.user_id == uid,
                Transaction.amount < 0,
                Transaction.type == Transaction.TYPE_MISSION_REWARD,
            ).first()
            assert neg_txn is not None


class TestProfileCompletedMissions:
    def test_profile_includes_completed_missions(
        self, app, db, logged_in_client, sample_users, mission_with_rewards
    ):
        kid = sample_users["kid1"]
        with app.app_context():
            assignment = MissionAssignment(
                mission_id=mission_with_rewards.id,
                user_id=kid.id,
                state=MissionAssignment.STATE_COMPLETED,
                current_level=3,
            )
            db.session.add(assignment)
            db.session.commit()

        client = logged_in_client(user_id=kid.id)
        resp = client.get("/api/profile")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "completed_missions" in data
        assert len(data["completed_missions"]) == 1
        cm = data["completed_missions"][0]
        assert cm["gem_type"] == "ruby"
        assert cm["gem_size"] == "medium"

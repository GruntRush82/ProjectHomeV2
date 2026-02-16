"""API tests for the missions blueprint."""

import pytest

from app.extensions import db
from app.models.bank import BankAccount, Transaction
from app.models.mission import Mission, MissionAssignment, MissionProgress
from app.models.user import User


@pytest.fixture
def mult_mission(app, db):
    m = Mission(
        title="Multiplication Master",
        description="Master multiplication",
        mission_type="multiplication",
        config={"range_min": 1, "range_max": 12},
        reward_cash=50.0,
        reward_icon="lightning_brain",
    )
    db.session.add(m)
    db.session.commit()
    return m


@pytest.fixture
def piano_mission(app, db):
    m = Mission(
        title="Piano Performance",
        description="Play a piece",
        mission_type="piano",
        config={
            "piece_name": "Fur Elise",
            "description": "Play Fur Elise without mistakes",
            "verification": "admin_approval",
        },
        reward_cash=50.0,
        reward_icon="golden_music_note",
    )
    db.session.add(m)
    db.session.commit()
    return m


@pytest.fixture
def kid_assignment(app, db, mult_mission, sample_users):
    a = MissionAssignment(
        mission_id=mult_mission.id,
        user_id=sample_users["kid1"].id,
    )
    db.session.add(a)
    db.session.commit()
    return a


@pytest.fixture
def piano_assignment(app, db, piano_mission, sample_users):
    a = MissionAssignment(
        mission_id=piano_mission.id,
        user_id=sample_users["kid1"].id,
    )
    db.session.add(a)
    db.session.commit()
    return a


# ── Auth tests ───────────────────────────────────────────────────────

class TestMissionsAuth:
    def test_list_missions_requires_login(self, auth_client):
        resp = auth_client.get("/api/missions")
        assert resp.status_code == 401

    def test_admin_routes_require_admin(self, logged_in_client, sample_users):
        client = logged_in_client(user_id=sample_users["kid1"].id)
        resp = client.get("/api/admin/missions")
        assert resp.status_code == 403


# ── User API tests ───────────────────────────────────────────────────

class TestListMissions:
    def test_list_empty(self, logged_in_client, sample_users):
        client = logged_in_client(user_id=sample_users["kid1"].id)
        resp = client.get("/api/missions")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["active"] == []
        assert data["completed"] == []

    def test_list_with_assignment(self, logged_in_client, sample_users, kid_assignment):
        client = logged_in_client(user_id=sample_users["kid1"].id)
        resp = client.get("/api/missions")
        data = resp.get_json()
        assert len(data["active"]) == 1
        assert data["active"][0]["id"] == kid_assignment.id


class TestMissionProgress:
    def test_get_progress(self, logged_in_client, sample_users, kid_assignment):
        client = logged_in_client(user_id=sample_users["kid1"].id)
        resp = client.get(f"/api/missions/{kid_assignment.id}/progress")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "mastered_count" in data
        assert data["assignment"]["id"] == kid_assignment.id

    def test_progress_wrong_user(self, logged_in_client, sample_users, kid_assignment):
        client = logged_in_client(user_id=sample_users["kid2"].id)
        resp = client.get(f"/api/missions/{kid_assignment.id}/progress")
        assert resp.status_code == 404


class TestStartMission:
    def test_start_mission(self, app, logged_in_client, sample_users, kid_assignment):
        client = logged_in_client(user_id=sample_users["kid1"].id)
        resp = client.post(f"/missions/{kid_assignment.id}/start")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["state"] == "training"

    def test_start_already_started(self, app, logged_in_client, sample_users, kid_assignment):
        kid_assignment.state = "training"
        db.session.commit()
        client = logged_in_client(user_id=sample_users["kid1"].id)
        resp = client.post(f"/missions/{kid_assignment.id}/start")
        assert resp.status_code == 400


class TestTraining:
    def test_get_training(self, app, logged_in_client, sample_users, kid_assignment):
        client = logged_in_client(user_id=sample_users["kid1"].id)
        resp = client.get(f"/api/missions/{kid_assignment.id}/train")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["type"] == "training"
        assert len(data["questions"]) == 20

    def test_submit_training(self, app, logged_in_client, sample_users, kid_assignment):
        client = logged_in_client(user_id=sample_users["kid1"].id)
        questions = [
            {"a": 2, "b": 3, "user_answer": 6, "correct": True},
            {"a": 4, "b": 5, "user_answer": 20, "correct": True},
        ]
        resp = client.post(
            f"/missions/{kid_assignment.id}/train",
            json={"questions": questions, "duration_seconds": 30},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["correct"] == 2

    def test_cannot_train_when_completed(self, app, logged_in_client, sample_users, kid_assignment):
        kid_assignment.state = MissionAssignment.STATE_COMPLETED
        db.session.commit()
        client = logged_in_client(user_id=sample_users["kid1"].id)
        resp = client.get(f"/api/missions/{kid_assignment.id}/train")
        assert resp.status_code == 400


class TestTesting:
    def test_get_test(self, app, logged_in_client, sample_users, kid_assignment):
        kid_assignment.state = MissionAssignment.STATE_TRAINING
        db.session.commit()
        client = logged_in_client(user_id=sample_users["kid1"].id)
        resp = client.get(f"/api/missions/{kid_assignment.id}/test?level=1")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["type"] == "test"
        assert len(data["questions"]) == 45
        assert "_answers" not in data  # answers stripped

    def test_cannot_test_when_assigned(self, app, logged_in_client, sample_users, kid_assignment):
        """Must be in training or failed state to test."""
        client = logged_in_client(user_id=sample_users["kid1"].id)
        resp = client.get(f"/api/missions/{kid_assignment.id}/test")
        assert resp.status_code == 400

    def test_submit_test_pass(self, app, logged_in_client, sample_users, kid_assignment):
        kid_assignment.state = MissionAssignment.STATE_TRAINING
        db.session.commit()

        client = logged_in_client(user_id=sample_users["kid1"].id)
        # Get test questions
        resp = client.get(f"/api/missions/{kid_assignment.id}/test?level=1")
        test_data = resp.get_json()
        questions = test_data["questions"]
        # Compute correct answers
        answers = [q["a"] * q["b"] for q in questions]

        resp = client.post(
            f"/missions/{kid_assignment.id}/test",
            json={
                "level": 1,
                "answers": answers,
                "questions": questions,
                "duration_seconds": 120,
            },
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["passed"] is True
        assert data["current_level"] == 1

    def test_submit_test_fail(self, app, logged_in_client, sample_users, kid_assignment):
        kid_assignment.state = MissionAssignment.STATE_TRAINING
        db.session.commit()

        client = logged_in_client(user_id=sample_users["kid1"].id)
        resp = client.get(f"/api/missions/{kid_assignment.id}/test?level=1")
        test_data = resp.get_json()
        questions = test_data["questions"]
        answers = [0] * len(questions)  # all wrong

        resp = client.post(
            f"/missions/{kid_assignment.id}/test",
            json={
                "level": 1,
                "answers": answers,
                "questions": questions,
                "duration_seconds": 60,
            },
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["passed"] is False

    def test_level3_pass_grants_reward(self, app, logged_in_client, sample_users, kid_assignment):
        kid_assignment.state = MissionAssignment.STATE_TRAINING
        kid_assignment.current_level = 2
        db.session.commit()

        client = logged_in_client(user_id=sample_users["kid1"].id)
        resp = client.get(f"/api/missions/{kid_assignment.id}/test?level=3")
        test_data = resp.get_json()
        questions = test_data["questions"]
        answers = [q["a"] * q["b"] for q in questions]

        resp = client.post(
            f"/missions/{kid_assignment.id}/test",
            json={
                "level": 3,
                "answers": answers,
                "questions": questions,
                "duration_seconds": 50,
            },
        )
        data = resp.get_json()
        assert data["passed"] is True
        assert data["completed"] is True
        assert data["reward"]["cash"] == 50.0
        assert data["reward"]["icon"] == "lightning_brain"

        # Verify bank account
        account = BankAccount.query.filter_by(user_id=sample_users["kid1"].id).first()
        assert account is not None
        assert account.cash_balance == 50.0

        # Verify transaction
        txn = Transaction.query.filter_by(
            user_id=sample_users["kid1"].id,
            type=Transaction.TYPE_MISSION_REWARD,
        ).first()
        assert txn is not None
        assert txn.amount == 50.0

        # Verify icon auto-equipped
        user = db.session.get(User, sample_users["kid1"].id)
        assert user.icon == "lightning_brain"


# ── Notification tests ───────────────────────────────────────────────

class TestNotifications:
    def test_get_unnotified(self, logged_in_client, sample_users, kid_assignment):
        client = logged_in_client(user_id=sample_users["kid1"].id)
        resp = client.get("/api/missions/notifications")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["notifications"]) == 1

    def test_dismiss_notifications(self, app, logged_in_client, sample_users, kid_assignment):
        client = logged_in_client(user_id=sample_users["kid1"].id)
        resp = client.post("/api/missions/notifications/dismiss")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["dismissed"] == 1

        # Verify dismissed
        resp = client.get("/api/missions/notifications")
        data = resp.get_json()
        assert len(data["notifications"]) == 0

    def test_no_notifications_for_other_user(self, logged_in_client, sample_users, kid_assignment):
        client = logged_in_client(user_id=sample_users["kid2"].id)
        resp = client.get("/api/missions/notifications")
        data = resp.get_json()
        assert len(data["notifications"]) == 0


# ── Admin tests ──────────────────────────────────────────────────────

class TestAdminMissions:
    def test_admin_list(self, admin_client, mult_mission, piano_mission):
        resp = admin_client.get("/api/admin/missions")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["missions"]) == 2
        assert len(data["users"]) == 2  # kid1 and kid2 (non-admin)

    def test_admin_assign(self, app, admin_client, mult_mission, sample_users):
        resp = admin_client.post("/api/admin/missions/assign", json={
            "mission_id": mult_mission.id,
            "user_id": sample_users["kid1"].id,
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["state"] == "assigned"
        assert data["mission"]["title"] == "Multiplication Master"

    def test_admin_assign_missing_fields(self, admin_client):
        resp = admin_client.post("/api/admin/missions/assign", json={})
        assert resp.status_code == 400

    def test_admin_approve_piano(self, app, admin_client, piano_assignment, sample_users):
        piano_assignment.state = MissionAssignment.STATE_PENDING_APPROVAL
        db.session.commit()

        resp = admin_client.post(f"/api/admin/missions/{piano_assignment.id}/approve")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["approved"] is True
        assert data["reward"]["cash"] == 50.0

        # Verify user icon
        from app.models.user import User
        user = db.session.get(User, sample_users["kid1"].id)
        assert user.icon == "golden_music_note"

    def test_admin_reject_piano(self, app, admin_client, piano_assignment):
        piano_assignment.state = MissionAssignment.STATE_PENDING_APPROVAL
        db.session.commit()

        resp = admin_client.post(f"/api/admin/missions/{piano_assignment.id}/reject")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["rejected"] is True
        assert data["assignment"]["state"] == "training"

    def test_approve_non_pending_fails(self, admin_client, kid_assignment):
        resp = admin_client.post(f"/api/admin/missions/{kid_assignment.id}/approve")
        assert resp.status_code == 400

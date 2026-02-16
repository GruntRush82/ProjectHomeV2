"""Integration tests for full mission flows end-to-end."""

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
        description="Play Fur Elise",
        mission_type="piano",
        config={
            "piece_name": "Fur Elise",
            "description": "Play without mistakes",
            "verification": "admin_approval",
        },
        reward_cash=50.0,
        reward_icon="golden_music_note",
    )
    db.session.add(m)
    db.session.commit()
    return m


class TestMultiplicationFullFlow:
    """Full flow: admin assigns → kid trains → L1 → L2 → L3 → cash + icon."""

    def test_full_multiplication_flow(self, app, admin_client, logged_in_client, sample_users, mult_mission):
        kid = sample_users["kid1"]

        # 1. Admin assigns mission
        resp = admin_client.post("/api/admin/missions/assign", json={
            "mission_id": mult_mission.id,
            "user_id": kid.id,
        })
        assert resp.status_code == 201
        assignment_id = resp.get_json()["id"]

        # 2. Kid sees notification
        kid_client = logged_in_client(user_id=kid.id)
        resp = kid_client.get("/api/missions/notifications")
        data = resp.get_json()
        assert len(data["notifications"]) == 1

        # 3. Kid dismisses notification
        resp = kid_client.post("/api/missions/notifications/dismiss")
        assert resp.get_json()["dismissed"] == 1

        # 4. Kid starts mission
        resp = kid_client.post(f"/missions/{assignment_id}/start")
        assert resp.get_json()["state"] == "training"

        # 5. Kid does a training session
        resp = kid_client.get(f"/api/missions/{assignment_id}/train")
        assert resp.status_code == 200
        training = resp.get_json()
        assert len(training["questions"]) == 20

        # Submit training results
        questions = [
            {"a": q["a"], "b": q["b"], "user_answer": q["a"] * q["b"], "correct": True}
            for q in training["questions"]
        ]
        resp = kid_client.post(f"/missions/{assignment_id}/train", json={
            "questions": questions,
            "duration_seconds": 120,
        })
        assert resp.status_code == 200

        # 6. Pass L1 (no time limit)
        resp = kid_client.get(f"/api/missions/{assignment_id}/test?level=1")
        test_data = resp.get_json()
        answers = [q["a"] * q["b"] for q in test_data["questions"]]
        resp = kid_client.post(f"/missions/{assignment_id}/test", json={
            "level": 1, "answers": answers,
            "questions": test_data["questions"], "duration_seconds": 200,
        })
        data = resp.get_json()
        assert data["passed"] is True
        assert data["current_level"] == 1

        # 7. Pass L2 (120s limit)
        resp = kid_client.get(f"/api/missions/{assignment_id}/test?level=2")
        test_data = resp.get_json()
        answers = [q["a"] * q["b"] for q in test_data["questions"]]
        resp = kid_client.post(f"/missions/{assignment_id}/test", json={
            "level": 2, "answers": answers,
            "questions": test_data["questions"], "duration_seconds": 90,
        })
        data = resp.get_json()
        assert data["passed"] is True
        assert data["current_level"] == 2

        # 8. Pass L3 (60s limit) → mission complete
        resp = kid_client.get(f"/api/missions/{assignment_id}/test?level=3")
        test_data = resp.get_json()
        answers = [q["a"] * q["b"] for q in test_data["questions"]]
        resp = kid_client.post(f"/missions/{assignment_id}/test", json={
            "level": 3, "answers": answers,
            "questions": test_data["questions"], "duration_seconds": 50,
        })
        data = resp.get_json()
        assert data["passed"] is True
        assert data["completed"] is True
        assert data["reward"]["cash"] == 50.0
        assert data["reward"]["icon"] == "lightning_brain"

        # 9. Verify bank account has reward
        account = BankAccount.query.filter_by(user_id=kid.id).first()
        assert account is not None
        assert account.cash_balance == 50.0

        # 10. Verify transaction record
        txn = Transaction.query.filter_by(
            user_id=kid.id, type=Transaction.TYPE_MISSION_REWARD,
        ).first()
        assert txn is not None
        assert txn.amount == 50.0
        assert "Multiplication Master" in txn.description

        # 11. Verify icon auto-equipped
        user = db.session.get(User, kid.id)
        assert user.icon == "lightning_brain"

        # 12. Verify mission shows as completed
        resp = kid_client.get("/api/missions")
        data = resp.get_json()
        assert len(data["completed"]) == 1
        assert len(data["active"]) == 0


class TestPianoFullFlow:
    """Full flow: assign → kid says "I did it" → admin approves → cash + icon."""

    def test_full_piano_flow(self, app, logged_in_client, sample_users, piano_mission):
        kid = sample_users["kid1"]
        admin = sample_users["admin"]

        # 1. Admin assigns
        client = logged_in_client(user_id=admin.id)
        resp = client.post("/api/admin/missions/assign", json={
            "mission_id": piano_mission.id,
            "user_id": kid.id,
        })
        assert resp.status_code == 201
        assignment_id = resp.get_json()["id"]

        # 2. Kid starts and submits "I did it"
        logged_in_client(user_id=kid.id)
        resp = client.post(f"/missions/{assignment_id}/start")
        assert resp.get_json()["state"] == "training"

        resp = client.post(f"/missions/{assignment_id}/test", json={
            "piece_name": "Fur Elise",
        })
        data = resp.get_json()
        assert data["pending_approval"] is True

        # 3. Admin approves (re-login as admin)
        logged_in_client(user_id=admin.id)
        resp = client.post(f"/api/admin/missions/{assignment_id}/approve")
        data = resp.get_json()
        assert data["approved"] is True
        assert data["reward"]["cash"] == 50.0
        assert data["reward"]["icon"] == "golden_music_note"

        # 4. Verify bank + icon
        account = BankAccount.query.filter_by(user_id=kid.id).first()
        assert account.cash_balance == 50.0

        user = db.session.get(User, kid.id)
        assert user.icon == "golden_music_note"


class TestPianoRejectFlow:
    """Piano rejection sends kid back to training."""

    def test_reject_then_resubmit(self, app, logged_in_client, sample_users, piano_mission):
        kid = sample_users["kid1"]
        admin = sample_users["admin"]

        # Assign as admin
        client = logged_in_client(user_id=admin.id)
        resp = client.post("/api/admin/missions/assign", json={
            "mission_id": piano_mission.id, "user_id": kid.id,
        })
        assignment_id = resp.get_json()["id"]

        # Kid starts + submits
        logged_in_client(user_id=kid.id)
        client.post(f"/missions/{assignment_id}/start")
        client.post(f"/missions/{assignment_id}/test", json={"piece_name": "Fur Elise"})

        # Admin rejects
        logged_in_client(user_id=admin.id)
        resp = client.post(f"/api/admin/missions/{assignment_id}/reject")
        data = resp.get_json()
        assert data["rejected"] is True
        assert data["assignment"]["state"] == "training"

        # Kid resubmits
        logged_in_client(user_id=kid.id)
        resp = client.post(f"/missions/{assignment_id}/test", json={"piece_name": "Fur Elise"})
        assert resp.get_json()["pending_approval"] is True

        # Admin approves
        logged_in_client(user_id=admin.id)
        resp = client.post(f"/api/admin/missions/{assignment_id}/approve")
        assert resp.get_json()["approved"] is True


class TestMultipleMissions:
    """Multiple missions per user and same mission to multiple users."""

    def test_multiple_missions_per_user(self, app, logged_in_client, sample_users, mult_mission, piano_mission):
        kid = sample_users["kid1"]
        admin = sample_users["admin"]

        # Assign both missions as admin
        client = logged_in_client(user_id=admin.id)
        client.post("/api/admin/missions/assign", json={
            "mission_id": mult_mission.id, "user_id": kid.id,
        })
        client.post("/api/admin/missions/assign", json={
            "mission_id": piano_mission.id, "user_id": kid.id,
        })

        # Kid sees both
        logged_in_client(user_id=kid.id)
        resp = client.get("/api/missions")
        data = resp.get_json()
        assert len(data["active"]) == 2

    def test_same_mission_multiple_users(self, app, logged_in_client, sample_users, mult_mission):
        kid1 = sample_users["kid1"]
        kid2 = sample_users["kid2"]
        admin = sample_users["admin"]

        # Assign same mission to both kids
        client = logged_in_client(user_id=admin.id)
        client.post("/api/admin/missions/assign", json={
            "mission_id": mult_mission.id, "user_id": kid1.id,
        })
        client.post("/api/admin/missions/assign", json={
            "mission_id": mult_mission.id, "user_id": kid2.id,
        })

        # Kid1 sees their own
        logged_in_client(user_id=kid1.id)
        resp = client.get("/api/missions")
        assert len(resp.get_json()["active"]) == 1

        # Kid2 also has one
        assignments = MissionAssignment.query.filter_by(user_id=kid2.id).all()
        assert len(assignments) == 1

    def test_mission_privacy(self, app, logged_in_client, sample_users, mult_mission):
        """Kid1's mission not visible to kid2."""
        kid1 = sample_users["kid1"]
        kid2 = sample_users["kid2"]
        admin = sample_users["admin"]

        client = logged_in_client(user_id=admin.id)
        resp = client.post("/api/admin/missions/assign", json={
            "mission_id": mult_mission.id, "user_id": kid1.id,
        })
        assignment_id = resp.get_json()["id"]

        # Kid2 can't access kid1's assignment
        logged_in_client(user_id=kid2.id)
        resp = client.get(f"/api/missions/{assignment_id}/progress")
        assert resp.status_code == 404

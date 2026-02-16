"""Unit tests for Mission, MissionAssignment, MissionProgress models."""

from datetime import datetime

from app.models.mission import Mission, MissionAssignment, MissionProgress


class TestMissionModel:
    """Tests for the Mission definition model."""

    def test_create_mission(self, app, db):
        m = Mission(
            title="Test Mission",
            description="A test mission",
            mission_type="test_type",
            config={"key": "value"},
            reward_cash=25.0,
            reward_icon="test_icon",
        )
        db.session.add(m)
        db.session.commit()

        assert m.id is not None
        assert m.title == "Test Mission"
        assert m.mission_type == "test_type"
        assert m.config == {"key": "value"}
        assert m.reward_cash == 25.0
        assert m.reward_icon == "test_icon"
        assert m.created_at is not None

    def test_mission_to_dict(self, app, db):
        m = Mission(
            title="Dict Test",
            description="Testing to_dict",
            mission_type="multiplication",
            config={"range_min": 1},
            reward_cash=50.0,
            reward_icon="lightning_brain",
        )
        db.session.add(m)
        db.session.commit()

        d = m.to_dict()
        assert d["title"] == "Dict Test"
        assert d["mission_type"] == "multiplication"
        assert d["reward_cash"] == 50.0
        assert d["config"]["range_min"] == 1

    def test_mission_repr(self, app, db):
        m = Mission(
            title="Repr Test",
            description="test",
            mission_type="piano",
            reward_icon="note",
        )
        assert "piano" in repr(m)
        assert "Repr Test" in repr(m)


class TestMissionAssignmentModel:
    """Tests for the MissionAssignment model."""

    def test_create_assignment(self, app, db, sample_users):
        m = Mission(
            title="Assign Test",
            description="test",
            mission_type="test",
            reward_icon="icon",
        )
        db.session.add(m)
        db.session.commit()

        a = MissionAssignment(
            mission_id=m.id,
            user_id=sample_users["kid1"].id,
        )
        db.session.add(a)
        db.session.commit()

        assert a.id is not None
        assert a.state == MissionAssignment.STATE_ASSIGNED
        assert a.current_level == 0
        assert a.notified is False
        assert a.mission.title == "Assign Test"
        assert a.user.username == "TestKid1"

    def test_assignment_state_constants(self):
        assert MissionAssignment.STATE_ASSIGNED == "assigned"
        assert MissionAssignment.STATE_TRAINING == "training"
        assert MissionAssignment.STATE_TESTING == "testing"
        assert MissionAssignment.STATE_COMPLETED == "completed"
        assert MissionAssignment.STATE_FAILED == "failed"
        assert MissionAssignment.STATE_PENDING_APPROVAL == "pending_approval"
        assert len(MissionAssignment.VALID_STATES) == 6

    def test_assignment_to_dict(self, app, db, sample_users):
        m = Mission(
            title="Dict Mission",
            description="test",
            mission_type="test",
            reward_icon="icon",
            reward_cash=10.0,
        )
        db.session.add(m)
        db.session.commit()

        a = MissionAssignment(
            mission_id=m.id,
            user_id=sample_users["kid1"].id,
        )
        db.session.add(a)
        db.session.commit()

        d = a.to_dict()
        assert d["state"] == "assigned"
        assert d["current_level"] == 0
        assert d["mission"]["title"] == "Dict Mission"
        assert d["started_at"] is None
        assert d["completed_at"] is None

    def test_assignment_relationships(self, app, db, sample_users):
        m = Mission(
            title="Rel Test",
            description="test",
            mission_type="test",
            reward_icon="icon",
        )
        db.session.add(m)
        db.session.commit()

        a = MissionAssignment(
            mission_id=m.id,
            user_id=sample_users["kid1"].id,
        )
        db.session.add(a)
        db.session.commit()

        assert len(m.assignments) == 1
        assert m.assignments[0].id == a.id
        assert len(sample_users["kid1"].mission_assignments) == 1


class TestMissionProgressModel:
    """Tests for the MissionProgress model."""

    def test_create_progress(self, app, db, sample_users):
        m = Mission(
            title="Progress Test",
            description="test",
            mission_type="test",
            reward_icon="icon",
        )
        db.session.add(m)
        db.session.commit()

        a = MissionAssignment(mission_id=m.id, user_id=sample_users["kid1"].id)
        db.session.add(a)
        db.session.commit()

        p = MissionProgress(
            assignment_id=a.id,
            session_type="training",
            data={"questions": 20, "correct": 15},
            score=15,
            duration_seconds=120,
        )
        db.session.add(p)
        db.session.commit()

        assert p.id is not None
        assert p.session_type == "training"
        assert p.score == 15
        assert p.data["correct"] == 15
        assert p.assignment.id == a.id

    def test_progress_to_dict(self, app, db, sample_users):
        m = Mission(
            title="Progress Dict",
            description="test",
            mission_type="test",
            reward_icon="icon",
        )
        db.session.add(m)
        db.session.commit()

        a = MissionAssignment(mission_id=m.id, user_id=sample_users["kid1"].id)
        db.session.add(a)
        db.session.commit()

        p = MissionProgress(
            assignment_id=a.id,
            session_type="test",
            data={"level": 1},
            score=45,
        )
        db.session.add(p)
        db.session.commit()

        d = p.to_dict()
        assert d["session_type"] == "test"
        assert d["score"] == 45
        assert d["data"]["level"] == 1
        assert d["duration_seconds"] is None

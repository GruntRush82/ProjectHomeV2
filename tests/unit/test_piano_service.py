"""Unit tests for the piano mission handler."""

import pytest

from app.models.mission import Mission, MissionAssignment, MissionProgress
from app.services.missions import get_handler, MISSION_HANDLERS
from app.services.missions.piano import PianoHandler


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
def piano_assignment(app, db, piano_mission, sample_users):
    a = MissionAssignment(
        mission_id=piano_mission.id,
        user_id=sample_users["kid1"].id,
    )
    db.session.add(a)
    db.session.commit()
    return a


class TestHandlerRegistry:
    def test_multiplication_registered(self):
        assert "multiplication" in MISSION_HANDLERS

    def test_piano_registered(self):
        assert "piano" in MISSION_HANDLERS

    def test_get_handler_returns_correct_type(self):
        handler = get_handler("piano")
        assert isinstance(handler, PianoHandler)

    def test_get_handler_unknown_returns_none(self):
        assert get_handler("nonexistent") is None


class TestPianoHandler:
    def test_get_training_session(self, app, db, piano_assignment):
        handler = get_handler("piano")
        session = handler.get_training_session(piano_assignment)
        assert session["type"] == "training"
        assert session["piece_name"] == "Fur Elise"

    def test_evaluate_test_sets_pending_approval(self, app, db, piano_assignment):
        handler = get_handler("piano")
        piano_assignment.state = MissionAssignment.STATE_TRAINING
        db.session.commit()

        result = handler.evaluate_test(piano_assignment, {"piece_name": "Fur Elise"})
        assert result["pending_approval"] is True
        assert piano_assignment.state == MissionAssignment.STATE_PENDING_APPROVAL

        # Should have a progress record
        progress = MissionProgress.query.filter_by(
            assignment_id=piano_assignment.id
        ).all()
        assert len(progress) == 1

    def test_progress_summary(self, app, db, piano_assignment):
        handler = get_handler("piano")
        summary = handler.get_progress_summary(piano_assignment)
        assert summary["piece_name"] == "Fur Elise"
        assert summary["state"] == "assigned"
        assert summary["completed"] is False

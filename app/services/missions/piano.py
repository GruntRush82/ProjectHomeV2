"""Piano mission handler.

Simplified flow: kid clicks "I did it" → admin approves.
No real training or testing logic.
"""

from datetime import datetime

from app.extensions import db
from app.models.mission import MissionAssignment, MissionProgress
from app.services.missions.base import BaseMissionHandler


class PianoHandler(BaseMissionHandler):
    """Handler for the Piano Performance mission."""

    def get_training_session(self, assignment):
        """Return info about what to practice."""
        config = assignment.mission.config or {}
        return {
            "type": "training",
            "piece_name": config.get("piece_name", "Unknown piece"),
            "description": config.get("description", "Practice your piece!"),
            "message": "Practice your piece and click 'I did it!' when you're ready to perform.",
        }

    def evaluate_training(self, assignment, results):
        """Piano training is just informational — no scoring."""
        if assignment.state == MissionAssignment.STATE_ASSIGNED:
            assignment.state = MissionAssignment.STATE_TRAINING
            assignment.started_at = datetime.utcnow()

        db.session.commit()

        return {
            "message": "Keep practicing! Click 'I did it!' when you're ready.",
        }

    def get_test(self, assignment, level=None):
        """Piano test is just the 'I did it' confirmation."""
        config = assignment.mission.config or {}
        return {
            "type": "test",
            "piece_name": config.get("piece_name", "Unknown piece"),
            "message": "Did you perform the piece? Click to submit for approval.",
        }

    def evaluate_test(self, assignment, results):
        """Mark the mission as pending admin approval.

        Args:
            results: {"piece_name": str (optional)}
        """
        piece_name = results.get("piece_name", "")

        progress = MissionProgress(
            assignment_id=assignment.id,
            session_type="test",
            data={"piece_name": piece_name, "submitted": True},
            score=None,
        )
        db.session.add(progress)

        assignment.state = MissionAssignment.STATE_PENDING_APPROVAL
        db.session.commit()

        return {
            "pending_approval": True,
            "message": "Submitted! An admin will review your performance.",
        }

    def get_progress_summary(self, assignment):
        """Return progress summary for the piano mission."""
        config = assignment.mission.config or {}
        return {
            "piece_name": config.get("piece_name", "Unknown piece"),
            "state": assignment.state,
            "submitted": assignment.state in (
                MissionAssignment.STATE_PENDING_APPROVAL,
                MissionAssignment.STATE_COMPLETED,
            ),
            "completed": assignment.state == MissionAssignment.STATE_COMPLETED,
        }

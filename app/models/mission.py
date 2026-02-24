"""Mission models — Mission, MissionAssignment, MissionProgress."""

from datetime import datetime

from app.extensions import db


class Mission(db.Model):
    """Definition of a mission type (seeded, not user-created)."""

    __tablename__ = "mission"

    VALID_GEM_TYPES = {"ruby", "emerald", "diamond", "sapphire", "amethyst", "topaz"}
    VALID_GEM_SIZES = {"small", "medium", "large"}

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    mission_type = db.Column(db.String(50), nullable=False)
    config = db.Column(db.JSON, nullable=False, default=dict)
    reward_cash = db.Column(db.Float, nullable=False, default=0.0)
    reward_icon = db.Column(db.String(50), nullable=False)
    reward_xp = db.Column(db.Integer, nullable=False, default=500)
    reward_description = db.Column(db.String(300), nullable=True)
    gem_type = db.Column(db.String(20), nullable=True)   # ruby/emerald/diamond/sapphire/amethyst/topaz
    gem_size = db.Column(db.String(10), nullable=True)   # small/medium/large
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    assignments = db.relationship(
        "MissionAssignment", backref="mission", lazy=True
    )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "mission_type": self.mission_type,
            "config": self.config,
            "reward_cash": round(self.reward_cash, 2),
            "reward_icon": self.reward_icon,
            "reward_xp": self.reward_xp or 500,
            "reward_description": self.reward_description,
            "gem_type": self.gem_type,
            "gem_size": self.gem_size,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self):
        return f"<Mission id={self.id} type={self.mission_type!r} title={self.title!r}>"


class MissionAssignment(db.Model):
    """A specific mission assigned to a specific user."""

    __tablename__ = "mission_assignment"

    # State constants
    STATE_ASSIGNED = "assigned"
    STATE_TRAINING = "training"
    STATE_TESTING = "testing"
    STATE_COMPLETED = "completed"
    STATE_FAILED = "failed"
    STATE_PENDING_APPROVAL = "pending_approval"

    VALID_STATES = {
        STATE_ASSIGNED, STATE_TRAINING, STATE_TESTING,
        STATE_COMPLETED, STATE_FAILED, STATE_PENDING_APPROVAL,
    }

    id = db.Column(db.Integer, primary_key=True)
    mission_id = db.Column(
        db.Integer, db.ForeignKey("mission.id"), nullable=False
    )
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=False
    )
    state = db.Column(db.String(20), nullable=False, default=STATE_ASSIGNED)
    current_level = db.Column(db.Integer, nullable=False, default=0)
    notified = db.Column(db.Boolean, nullable=False, default=False)
    assigned_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship(
        "User", backref=db.backref("mission_assignments", lazy=True)
    )
    progress_records = db.relationship(
        "MissionProgress", backref="assignment", lazy=True,
        order_by="MissionProgress.created_at.desc()",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "mission_id": self.mission_id,
            "user_id": self.user_id,
            "state": self.state,
            "current_level": self.current_level,
            "notified": self.notified,
            "assigned_at": self.assigned_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "mission": self.mission.to_dict() if self.mission else None,
        }

    def __repr__(self):
        return (
            f"<MissionAssignment id={self.id} mission_id={self.mission_id} "
            f"user_id={self.user_id} state={self.state!r}>"
        )


class MissionProgress(db.Model):
    """Log of a training or test session for a mission assignment."""

    __tablename__ = "mission_progress"

    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(
        db.Integer, db.ForeignKey("mission_assignment.id"), nullable=False
    )
    session_type = db.Column(db.String(20), nullable=False)  # 'training' or 'test'
    data = db.Column(db.JSON, nullable=False, default=dict)
    score = db.Column(db.Integer, nullable=True)
    duration_seconds = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "assignment_id": self.assignment_id,
            "session_type": self.session_type,
            "data": self.data,
            "score": self.score,
            "duration_seconds": self.duration_seconds,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self):
        return (
            f"<MissionProgress id={self.id} assignment_id={self.assignment_id} "
            f"type={self.session_type!r} score={self.score}>"
        )

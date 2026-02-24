"""Lifestyle Points models — goals, logs, privileges, redemptions."""

from datetime import date as _date, timedelta

from app.extensions import db


class LifestyleGoal(db.Model):
    __tablename__ = "lifestyle_goal"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    weekly_target = db.Column(db.Integer, nullable=False, default=5)
    active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)

    logs = db.relationship(
        "LifestyleLog", backref="goal", lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self, week_start=None):
        today = _date.today()
        if week_start is None:
            week_start = today - timedelta(days=today.weekday())
        this_week_count = sum(1 for log in self.logs if log.log_date >= week_start)
        today_logged = any(log.log_date == today for log in self.logs)
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "weekly_target": self.weekly_target,
            "active": self.active,
            "this_week_count": this_week_count,
            "today_logged": today_logged,
            "on_track": this_week_count >= self.weekly_target,
        }


class LifestyleLog(db.Model):
    __tablename__ = "lifestyle_log"
    __table_args__ = (
        db.UniqueConstraint("goal_id", "log_date", name="uq_goal_log_date"),
    )

    id = db.Column(db.Integer, primary_key=True)
    goal_id = db.Column(db.Integer, db.ForeignKey("lifestyle_goal.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    log_date = db.Column(db.Date, nullable=False)


class LifestylePrivilege(db.Model):
    __tablename__ = "lifestyle_privilege"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    point_cost = db.Column(db.Integer, nullable=False, default=1)
    active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "point_cost": self.point_cost,
            "active": self.active,
        }


class LifestyleRedemption(db.Model):
    __tablename__ = "lifestyle_redemption"

    STATUS_PENDING = "pending"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    privilege_id = db.Column(
        db.Integer, db.ForeignKey("lifestyle_privilege.id"), nullable=False
    )
    points_spent = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending")
    redeemed_at = db.Column(db.DateTime, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)

    privilege = db.relationship("LifestylePrivilege", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "privilege_id": self.privilege_id,
            "privilege_name": self.privilege.name if self.privilege else None,
            "privilege_description": (
                self.privilege.description if self.privilege else None
            ),
            "points_spent": self.points_spent,
            "status": self.status,
            "redeemed_at": self.redeemed_at.isoformat() if self.redeemed_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "cancelled_at": (
                self.cancelled_at.isoformat() if self.cancelled_at else None
            ),
        }

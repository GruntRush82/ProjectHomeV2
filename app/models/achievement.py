"""Achievement and UserAchievement models for the gamification system."""

from datetime import datetime

from app.extensions import db


class Achievement(db.Model):
    """Catalog of all available achievements."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    icon = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # chores, streaks, bank
    requirement_type = db.Column(db.String(50), nullable=False)
    requirement_value = db.Column(db.Integer, nullable=False)
    xp_reward = db.Column(db.Integer, nullable=False, default=0)
    tier = db.Column(db.String(10), nullable=False)  # bronze, silver, gold
    is_visible = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)

    user_achievements = db.relationship(
        "UserAchievement", backref="achievement", lazy=True
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "category": self.category,
            "requirement_type": self.requirement_type,
            "requirement_value": self.requirement_value,
            "xp_reward": self.xp_reward,
            "tier": self.tier,
            "is_visible": self.is_visible,
            "display_order": self.display_order,
        }

    def __repr__(self):
        return f"<Achievement {self.name}>"


class UserAchievement(db.Model):
    """Tracks which achievements each user has unlocked."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    achievement_id = db.Column(
        db.Integer, db.ForeignKey("achievement.id"), nullable=False
    )
    unlocked_at = db.Column(db.DateTime, default=datetime.utcnow)
    notified = db.Column(db.Boolean, default=False)

    __table_args__ = (
        db.UniqueConstraint("user_id", "achievement_id", name="uq_user_achievement"),
    )

    user = db.relationship("User", backref="user_achievements")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "achievement_id": self.achievement_id,
            "unlocked_at": self.unlocked_at.isoformat() + "Z" if self.unlocked_at else None,
            "notified": self.notified,
            "achievement": self.achievement.to_dict() if self.achievement else None,
        }

    def __repr__(self):
        return f"<UserAchievement user={self.user_id} achievement={self.achievement_id}>"

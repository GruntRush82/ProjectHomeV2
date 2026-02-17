from app.extensions import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)

    # V2 additions
    email = db.Column(db.String(200), nullable=True)
    allowance = db.Column(db.Float, default=0)
    is_admin = db.Column(db.Boolean, default=False)
    icon = db.Column(db.String(50), default="?")
    theme_color = db.Column(db.String(20), default="cyan")
    xp = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    streak_current = db.Column(db.Integer, default=0)
    streak_best = db.Column(db.Integer, default=0)
    perfect_weeks_total = db.Column(db.Integer, default=0)
    fire_mode = db.Column(db.Boolean, default=False)

    # Relationships
    chores = db.relationship(
        "Chore", backref="user", lazy=True, foreign_keys="Chore.user_id"
    )

    def __repr__(self):
        return f"<User {self.username}>"

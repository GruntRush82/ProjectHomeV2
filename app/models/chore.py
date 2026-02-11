from sqlalchemy.dialects.sqlite import JSON

from app.extensions import db


class Chore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    day = db.Column(db.String(100), nullable=False, default="Monday")
    rotation_type = db.Column(db.String(10), nullable=False, default="static")
    rotation_order = db.Column(JSON, nullable=True)
    base_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)

    history = db.relationship("ChoreHistory", backref="chore", lazy=True)

    def __repr__(self):
        return f"<Chore {self.id}: {self.description}>"


class ChoreHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chore_id = db.Column(db.Integer, db.ForeignKey("chore.id"), nullable=False)
    username = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    completed = db.Column(db.Boolean, nullable=False)
    day = db.Column(db.String(100), nullable=False)
    rotation_type = db.Column(db.String(10), nullable=False)

    def __repr__(self):
        return f"<ChoreHistory {self.id}: {self.username} on {self.date}>"

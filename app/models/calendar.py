"""Calendar event model."""
from datetime import datetime

from app.extensions import db


class CalendarEvent(db.Model):
    __tablename__ = "calendar_event"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    event_date = db.Column(db.Date, nullable=False)
    event_time = db.Column(db.Time, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    google_event_id = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    creator = db.relationship("User", backref=db.backref("calendar_events", lazy=True))

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "event_date": self.event_date.isoformat(),
            "event_time": self.event_time.strftime("%H:%M") if self.event_time else None,
            "created_by": self.created_by,
            "creator_name": self.creator.username if self.creator else None,
            "google_event_id": self.google_event_id,
            "created_at": self.created_at.isoformat(),
        }

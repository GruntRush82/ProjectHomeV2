from datetime import datetime

from app.extensions import db


class TrustedIP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), unique=True, nullable=False)
    trusted_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.utcnow()
    )
    last_seen = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.utcnow()
    )

    def __repr__(self):
        return f"<TrustedIP {self.ip_address}>"


class PinAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False)
    attempted_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.utcnow()
    )
    success = db.Column(db.Boolean, nullable=False)

    def __repr__(self):
        return f"<PinAttempt {self.ip_address} success={self.success}>"


class AppConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"<AppConfig {self.key}={self.value}>"

    @staticmethod
    def get(key, default=None):
        """Retrieve a config value by key, returning default if not found."""
        row = AppConfig.query.filter_by(key=key).first()
        return row.value if row else default

    @staticmethod
    def set(key, value):
        """Set a config value, creating or updating the row."""
        row = AppConfig.query.filter_by(key=key).first()
        if row:
            row.value = str(value)
        else:
            row = AppConfig(key=key, value=str(value))
            from app.extensions import db

            db.session.add(row)

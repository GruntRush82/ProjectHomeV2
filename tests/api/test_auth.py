"""API tests for auth — PIN validation, IP trust, rate limiting."""

import bcrypt
import pytest
from datetime import datetime, timedelta

from app.models.security import AppConfig, PinAttempt, TrustedIP


def _set_pin(db, pin="1234"):
    """Set a PIN hash in AppConfig."""
    hashed = bcrypt.hashpw(pin.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    AppConfig.set("pin_hash", hashed)
    db.session.commit()


class TestIPTrust:
    def test_untrusted_ip_redirects_to_pin(self, client, db, app):
        """Without a trusted IP and with a PIN set, requests redirect to /pin."""
        with app.app_context():
            _set_pin(db)
        resp = client.get("/users")
        assert resp.status_code == 302
        assert "/pin" in resp.headers["Location"]

    def test_no_pin_configured_allows_access(self, client, db):
        """With no PIN in AppConfig, all requests are allowed through."""
        resp = client.get("/users")
        assert resp.status_code == 200

    def test_static_files_exempt_from_auth(self, client, db, app):
        """Static file requests bypass PIN auth."""
        with app.app_context():
            _set_pin(db)
        resp = client.get("/static/css/style.css")
        # Should not redirect (either 200 or 404 for missing file, but not 302)
        assert resp.status_code != 302

    def test_trusted_ip_allows_access(self, client, db, app):
        """With a trusted IP entry, requests go through without PIN."""
        with app.app_context():
            _set_pin(db)
            trust = TrustedIP(
                ip_address="127.0.0.1",
                trusted_at=datetime.utcnow(),
                last_seen=datetime.utcnow(),
            )
            db.session.add(trust)
            db.session.commit()
        resp = client.get("/users")
        assert resp.status_code == 200

    def test_expired_ip_requires_pin_again(self, client, db, app):
        """A trusted IP older than 7 days should not pass."""
        with app.app_context():
            _set_pin(db)
            old_time = datetime.utcnow() - timedelta(days=8)
            trust = TrustedIP(
                ip_address="127.0.0.1",
                trusted_at=old_time,
                last_seen=old_time,
            )
            db.session.add(trust)
            db.session.commit()
        resp = client.get("/users")
        assert resp.status_code == 302
        assert "/pin" in resp.headers["Location"]


class TestPinValidation:
    def test_correct_pin_trusts_ip(self, client, db, app):
        """Submitting the correct PIN trusts the IP and redirects to login."""
        with app.app_context():
            _set_pin(db, "5678")
        resp = client.post("/pin", data={"pin": "5678"}, follow_redirects=False)
        assert resp.status_code == 302
        # IP should now be trusted — verify by accessing a protected route
        resp2 = client.get("/users")
        assert resp2.status_code == 200

    def test_wrong_pin_rejected(self, client, db, app):
        """Wrong PIN shows the PIN page again with an error."""
        with app.app_context():
            _set_pin(db, "1234")
        resp = client.post("/pin", data={"pin": "0000"})
        assert resp.status_code == 200
        assert b"Incorrect PIN" in resp.data

    def test_pin_page_accessible(self, client, db, app):
        """GET /pin returns 200 even with PIN set (it's exempt)."""
        with app.app_context():
            _set_pin(db)
        resp = client.get("/pin")
        assert resp.status_code == 200

    def test_pin_lockout_after_5_attempts(self, client, db, app):
        """After 5 wrong attempts, the user is locked out."""
        with app.app_context():
            _set_pin(db, "1234")
        for _ in range(5):
            client.post("/pin", data={"pin": "0000"})
        # 6th attempt should show lockout
        resp = client.post("/pin", data={"pin": "1234"})
        assert resp.status_code == 200
        assert b"Too many attempts" in resp.data


class TestPinAttemptRecording:
    def test_failed_attempt_recorded(self, client, db, app):
        """A wrong PIN attempt is recorded in PinAttempt table."""
        with app.app_context():
            _set_pin(db, "1234")
        client.post("/pin", data={"pin": "9999"})
        with app.app_context():
            attempts = PinAttempt.query.all()
            assert len(attempts) == 1
            assert attempts[0].success is False

    def test_successful_attempt_recorded(self, client, db, app):
        """A correct PIN attempt is recorded as success."""
        with app.app_context():
            _set_pin(db, "1234")
        client.post("/pin", data={"pin": "1234"})
        with app.app_context():
            attempts = PinAttempt.query.filter_by(success=True).all()
            assert len(attempts) == 1

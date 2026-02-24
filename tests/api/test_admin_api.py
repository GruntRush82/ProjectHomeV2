"""Admin API tests — Phase 6.

Target: ~20 tests covering auth, overview, user management,
config, trusted IPs, and digest trigger.
"""

import pytest

from app.models.security import AppConfig, TrustedIP
from app.models.user import User


# ── fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def non_admin_client(logged_in_client, sample_users):
    """Client logged in as a non-admin kid."""
    return logged_in_client(user_id=sample_users["kid1"].id)


@pytest.fixture
def extra_ip(app, db):
    """A second TrustedIP record for revocation tests."""
    from datetime import datetime
    with app.app_context():
        ip = TrustedIP(
            ip_address="192.168.1.99",
            trusted_at=datetime.utcnow(),
            last_seen=datetime.utcnow(),
        )
        db.session.add(ip)
        db.session.commit()
        yield ip


# ═══════════════════════════════════════════════════════════════════════
# AdminAuthTests
# ═══════════════════════════════════════════════════════════════════════

class TestAdminAuth:
    def test_non_admin_gets_403(self, non_admin_client):
        resp = non_admin_client.get("/api/admin/overview")
        assert resp.status_code == 403
        assert "error" in resp.get_json()

    def test_logged_out_gets_401(self, auth_client):
        resp = auth_client.get("/api/admin/overview")
        assert resp.status_code == 401
        assert "error" in resp.get_json()

    def test_admin_gets_overview_200(self, admin_client):
        resp = admin_client.get("/api/admin/overview")
        assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════════════════
# AdminOverviewTests
# ═══════════════════════════════════════════════════════════════════════

class TestAdminOverview:
    def test_overview_returns_all_users(self, admin_client, sample_users):
        resp = admin_client.get("/api/admin/overview")
        data = resp.get_json()
        assert "users" in data
        # sample_users creates 3 users (admin + kid1 + kid2)
        assert len(data["users"]) == 3

    def test_overview_user_has_required_fields(self, admin_client, sample_users):
        resp = admin_client.get("/api/admin/overview")
        user_data = resp.get_json()["users"][0]
        required = {
            "id", "username", "icon", "level", "level_name", "xp",
            "next_level_xp", "cash_balance", "total_savings",
            "cashout_available", "fire_mode", "streak_current",
            "streak_best", "allowance", "email", "is_admin",
        }
        assert required.issubset(user_data.keys())

    def test_overview_includes_bank_data(self, app, admin_client, sample_users, db):
        """Cash balance reflects actual bank account state."""
        from app.models.bank import BankAccount
        from datetime import datetime

        kid = sample_users["kid1"]
        with app.app_context():
            account = BankAccount(user_id=kid.id, cash_balance=42.50, created_at=datetime.utcnow())
            db.session.add(account)
            db.session.commit()

        resp = admin_client.get("/api/admin/overview")
        users = resp.get_json()["users"]
        kid_data = next(u for u in users if u["id"] == kid.id)
        assert kid_data["cash_balance"] == 42.50


# ═══════════════════════════════════════════════════════════════════════
# AdminUserTests
# ═══════════════════════════════════════════════════════════════════════

class TestAdminUsers:
    def test_list_users_returns_full_fields(self, admin_client, sample_users):
        resp = admin_client.get("/api/admin/users")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "users" in data
        user = data["users"][0]
        for field in ("id", "username", "email", "allowance", "is_admin", "level", "xp"):
            assert field in user

    def test_create_user(self, admin_client, app, db):
        resp = admin_client.post(
            "/api/admin/users",
            json={"username": "NewKid", "allowance": 10.0},
            content_type="application/json",
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["username"] == "NewKid"
        with app.app_context():
            assert User.query.filter_by(username="NewKid").first() is not None

    def test_update_allowance(self, admin_client, sample_users, app, db):
        kid = sample_users["kid1"]
        resp = admin_client.put(
            f"/api/admin/users/{kid.id}",
            json={"allowance": 20.0},
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.get_json()["allowance"] == 20.0
        with app.app_context():
            u = db.session.get(User, kid.id)
            assert u.allowance == 20.0

    def test_update_is_admin(self, admin_client, sample_users, app, db):
        kid = sample_users["kid1"]
        resp = admin_client.put(
            f"/api/admin/users/{kid.id}",
            json={"is_admin": True},
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.get_json()["is_admin"] is True
        with app.app_context():
            u = db.session.get(User, kid.id)
            assert u.is_admin is True

    def test_delete_user(self, admin_client, sample_users, app, db):
        kid = sample_users["kid2"]
        resp = admin_client.delete(f"/api/admin/users/{kid.id}")
        assert resp.status_code == 200
        with app.app_context():
            assert db.session.get(User, kid.id) is None

    def test_delete_nonexistent_404(self, admin_client):
        resp = admin_client.delete("/api/admin/users/99999")
        assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════════════════
# AdminConfigTests
# ═══════════════════════════════════════════════════════════════════════

class TestAdminConfig:
    def test_get_config_returns_all_keys(self, admin_client):
        resp = admin_client.get("/api/admin/config")
        assert resp.status_code == 200
        data = resp.get_json()
        expected_keys = {
            "interest_rate", "savings_max", "savings_deposit_min",
            "cashout_min", "savings_lock_days", "fire_mode_bonus_pct",
            "idle_timeout_min",
        }
        assert expected_keys.issubset(data.keys())
        # Each key should have value, default, label, unit
        for key in expected_keys:
            entry = data[key]
            assert "value" in entry
            assert "default" in entry
            assert "label" in entry
            assert "unit" in entry

    def test_update_single_config_value(self, admin_client, app, db):
        resp = admin_client.post(
            "/api/admin/config",
            json={"interest_rate": "0.08"},
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert "interest_rate" in resp.get_json()["updated"]
        with app.app_context():
            assert AppConfig.get("interest_rate") == "0.08"

    def test_update_multiple_config_values(self, admin_client, app, db):
        resp = admin_client.post(
            "/api/admin/config",
            json={"savings_max": "200.0", "cashout_min": "5.0"},
            content_type="application/json",
        )
        assert resp.status_code == 200
        updated = resp.get_json()["updated"]
        assert "savings_max" in updated
        assert "cashout_min" in updated

    def test_update_invalid_value_400(self, admin_client):
        resp = admin_client.post(
            "/api/admin/config",
            json={"interest_rate": "not-a-number"},
            content_type="application/json",
        )
        assert resp.status_code == 400
        assert "error" in resp.get_json()


# ═══════════════════════════════════════════════════════════════════════
# AdminIPTests
# ═══════════════════════════════════════════════════════════════════════

class TestAdminIPs:
    def test_list_trusted_ips(self, admin_client, extra_ip):
        resp = admin_client.get("/api/admin/trusted-ips")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "trusted_ips" in data
        # Should include at least the auth_client IP (127.0.0.1) and extra_ip
        assert len(data["trusted_ips"]) >= 1
        ip_entry = data["trusted_ips"][0]
        assert "id" in ip_entry
        assert "ip_address" in ip_entry
        assert "trusted_at" in ip_entry
        assert "last_seen" in ip_entry

    def test_revoke_ip(self, admin_client, extra_ip, app, db):
        resp = admin_client.delete(f"/api/admin/trusted-ips/{extra_ip.id}")
        assert resp.status_code == 200
        with app.app_context():
            assert db.session.get(TrustedIP, extra_ip.id) is None

    def test_revoke_nonexistent_404(self, admin_client):
        resp = admin_client.delete("/api/admin/trusted-ips/99999")
        assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════════════════
# DigestTests
# ═══════════════════════════════════════════════════════════════════════

class TestDigest:
    def test_manual_digest_trigger_200(self, admin_client):
        resp = admin_client.post("/api/admin/digest/send")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "sent_to" in data
        assert "count" in data
        assert isinstance(data["sent_to"], list)

    def test_send_weekly_digest_dry_run(self, app, sample_users):
        """Digest service returns empty list when no admin emails configured."""
        with app.app_context():
            from app.services.digest import send_weekly_digest
            sent_to = send_weekly_digest()
            # sample_users admin (TestDad) has no email — should be empty list
            assert sent_to == []

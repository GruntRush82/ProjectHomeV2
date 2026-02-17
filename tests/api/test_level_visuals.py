"""Tests for level visual data attributes in templates."""

from app.extensions import db
from app.models.user import User


class TestLevelDataAttributes:
    """Verify data-level and data-fire-mode attributes render correctly."""

    def test_base_template_has_data_level(self, app, logged_in_client, sample_users):
        """Body tag should include data-level attribute."""
        kid = sample_users["kid1"]
        kid.level = 7
        db.session.commit()

        client = logged_in_client(user_id=kid.id)
        resp = client.get("/calendar")
        assert resp.status_code == 200
        assert b'data-level="7"' in resp.data

    def test_base_template_has_fire_mode(self, app, logged_in_client, sample_users):
        """Body tag should include data-fire-mode attribute."""
        kid = sample_users["kid1"]
        kid.fire_mode = True
        db.session.commit()

        client = logged_in_client(user_id=kid.id)
        resp = client.get("/calendar")
        assert resp.status_code == 200
        assert b'data-fire-mode="true"' in resp.data

    def test_login_cards_have_fire_mode(self, app, auth_client, sample_users):
        """Login page user cards should have data-fire-mode attribute."""
        kid = sample_users["kid1"]
        kid.fire_mode = True
        db.session.commit()

        resp = auth_client.get("/")
        assert resp.status_code == 200
        assert b'data-fire-mode="true"' in resp.data
        assert b'data-fire-mode="false"' in resp.data  # Other users

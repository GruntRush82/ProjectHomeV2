"""Tests for the profile API (render, icon, theme, level gating)."""

from app.extensions import db
from app.models.achievement import Achievement, UserAchievement
from app.models.mission import Mission, MissionAssignment
from app.models.user import User
from app.scripts.seed_achievements import seed_achievements


class TestProfilePage:
    """Profile page rendering."""

    def test_profile_renders(self, app, logged_in_client, sample_users):
        client = logged_in_client(user_id=sample_users["kid1"].id)
        resp = client.get("/profile")
        assert resp.status_code == 200
        assert b"profileApp" in resp.data


class TestProfileAPI:
    """GET /api/profile tests."""

    def test_profile_requires_login(self, app, auth_client):
        resp = auth_client.get("/api/profile")
        assert resp.status_code == 401

    def test_profile_returns_user_data(self, app, logged_in_client, sample_users):
        seed_achievements()
        kid = sample_users["kid1"]
        kid.xp = 300
        kid.level = 2
        kid.streak_current = 2
        kid.streak_best = 5
        kid.fire_mode = False
        db.session.commit()

        client = logged_in_client(user_id=kid.id)
        resp = client.get("/api/profile")
        data = resp.get_json()

        assert data["username"] == "TestKid1"
        assert data["level"] == 2
        assert data["level_name"] == "Apprentice"
        assert data["xp"] == 300
        assert data["streak_current"] == 2
        assert data["streak_best"] == 5
        assert data["fire_mode"] is False
        assert "available_icons" in data
        assert "recent_achievements" in data

    def test_profile_shows_recent_achievements(self, app, logged_in_client, sample_users):
        seed_achievements()
        kid = sample_users["kid1"]
        a = Achievement.query.filter_by(name="First Steps").first()
        db.session.add(UserAchievement(user_id=kid.id, achievement_id=a.id))
        db.session.commit()

        client = logged_in_client(user_id=kid.id)
        data = client.get("/api/profile").get_json()
        assert data["achievements_unlocked"] == 1
        assert len(data["recent_achievements"]) == 1
        assert data["recent_achievements"][0]["name"] == "First Steps"


class TestIconUpdate:
    """POST /api/profile/icon tests."""

    def test_set_starter_icon(self, app, logged_in_client, sample_users):
        """L1 icons (star_basic, rocket, etc.) are always available."""
        client = logged_in_client(user_id=sample_users["kid1"].id)
        resp = client.post("/api/profile/icon",
                           json={"icon": "star_basic"},
                           content_type="application/json")
        assert resp.status_code == 200
        assert resp.get_json()["icon"] == "star_basic"

    def test_reject_level_locked_icon(self, app, logged_in_client, sample_users):
        """User at level 1 cannot use a level-3 icon."""
        kid = sample_users["kid1"]
        kid.level = 1
        db.session.commit()

        client = logged_in_client(user_id=kid.id)
        resp = client.post("/api/profile/icon",
                           json={"icon": "shield"},
                           content_type="application/json")
        assert resp.status_code == 403
        assert "level 3" in resp.get_json()["error"].lower()

    def test_accept_level_unlocked_icon(self, app, logged_in_client, sample_users):
        """User at level 5 can use a level-3 icon."""
        kid = sample_users["kid1"]
        kid.level = 5
        db.session.commit()

        client = logged_in_client(user_id=kid.id)
        resp = client.post("/api/profile/icon",
                           json={"icon": "crown"},
                           content_type="application/json")
        assert resp.status_code == 200

    def test_reject_unearned_mission_icon(self, app, logged_in_client, sample_users):
        """User without completed mission cannot use mission icon."""
        client = logged_in_client(user_id=sample_users["kid1"].id)
        resp = client.post("/api/profile/icon",
                           json={"icon": "lightning_brain"},
                           content_type="application/json")
        assert resp.status_code == 403

    def test_accept_earned_mission_icon(self, app, logged_in_client, sample_users):
        """User with completed mission can use its icon."""
        kid = sample_users["kid1"]
        mission = Mission(
            title="Test", description="Test", mission_type="multiplication",
            config={}, reward_cash=50.0, reward_icon="lightning_brain",
        )
        db.session.add(mission)
        db.session.commit()
        ma = MissionAssignment(
            mission_id=mission.id, user_id=kid.id,
            state=MissionAssignment.STATE_COMPLETED,
        )
        db.session.add(ma)
        db.session.commit()

        client = logged_in_client(user_id=kid.id)
        resp = client.post("/api/profile/icon",
                           json={"icon": "lightning_brain"},
                           content_type="application/json")
        assert resp.status_code == 200

    def test_reject_invalid_icon(self, app, logged_in_client, sample_users):
        client = logged_in_client(user_id=sample_users["kid1"].id)
        resp = client.post("/api/profile/icon",
                           json={"icon": "totally_fake_icon"},
                           content_type="application/json")
        assert resp.status_code == 400


class TestThemeUpdate:
    """POST /api/profile/theme tests."""

    def test_set_starter_theme(self, app, logged_in_client, sample_users):
        client = logged_in_client(user_id=sample_users["kid1"].id)
        resp = client.post("/api/profile/theme",
                           json={"theme_color": "purple"},
                           content_type="application/json")
        assert resp.status_code == 200
        assert resp.get_json()["theme_color"] == "purple"

    def test_reject_level_locked_theme(self, app, logged_in_client, sample_users):
        """User at level 1 cannot use gold theme (requires level 5)."""
        kid = sample_users["kid1"]
        kid.level = 1
        db.session.commit()

        client = logged_in_client(user_id=kid.id)
        resp = client.post("/api/profile/theme",
                           json={"theme_color": "gold"},
                           content_type="application/json")
        assert resp.status_code == 403

    def test_accept_level_unlocked_theme(self, app, logged_in_client, sample_users):
        kid = sample_users["kid1"]
        kid.level = 7
        db.session.commit()

        client = logged_in_client(user_id=kid.id)
        resp = client.post("/api/profile/theme",
                           json={"theme_color": "red"},
                           content_type="application/json")
        assert resp.status_code == 200

    def test_reject_invalid_theme(self, app, logged_in_client, sample_users):
        client = logged_in_client(user_id=sample_users["kid1"].id)
        resp = client.post("/api/profile/theme",
                           json={"theme_color": "rainbow"},
                           content_type="application/json")
        assert resp.status_code == 400

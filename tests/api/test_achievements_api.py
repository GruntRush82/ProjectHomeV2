"""Tests for the achievements API (notifications, catalog, user achievements)."""

from app.extensions import db
from app.models.achievement import Achievement, UserAchievement
from app.scripts.seed_achievements import seed_achievements


class TestAchievementNotifications:
    """Notification endpoint tests."""

    def test_get_notifications_requires_login(self, app, auth_client):
        resp = auth_client.get("/api/achievements/notifications")
        assert resp.status_code == 401

    def test_get_notifications_empty(self, app, logged_in_client, sample_users):
        seed_achievements()
        client = logged_in_client(user_id=sample_users["kid1"].id)
        resp = client.get("/api/achievements/notifications")
        assert resp.status_code == 200
        assert len(resp.get_json()["notifications"]) == 0

    def test_get_notifications_returns_unnotified(self, app, logged_in_client, sample_users):
        seed_achievements()
        kid = sample_users["kid1"]
        achievement = Achievement.query.filter_by(name="First Steps").first()
        ua = UserAchievement(user_id=kid.id, achievement_id=achievement.id, notified=False)
        db.session.add(ua)
        db.session.commit()

        client = logged_in_client(user_id=kid.id)
        resp = client.get("/api/achievements/notifications")
        data = resp.get_json()
        assert len(data["notifications"]) == 1
        assert data["notifications"][0]["achievement"]["name"] == "First Steps"

    def test_get_notifications_gold_first(self, app, logged_in_client, sample_users):
        seed_achievements()
        kid = sample_users["kid1"]
        bronze = Achievement.query.filter_by(name="First Steps").first()
        gold = Achievement.query.filter_by(name="Chore Machine").first()
        db.session.add(UserAchievement(user_id=kid.id, achievement_id=bronze.id, notified=False))
        db.session.add(UserAchievement(user_id=kid.id, achievement_id=gold.id, notified=False))
        db.session.commit()

        client = logged_in_client(user_id=kid.id)
        resp = client.get("/api/achievements/notifications")
        data = resp.get_json()
        assert data["notifications"][0]["achievement"]["tier"] == "gold"
        assert data["notifications"][1]["achievement"]["tier"] == "bronze"

    def test_dismiss_all_notifications(self, app, logged_in_client, sample_users):
        seed_achievements()
        kid = sample_users["kid1"]
        achievement = Achievement.query.filter_by(name="First Steps").first()
        ua = UserAchievement(user_id=kid.id, achievement_id=achievement.id, notified=False)
        db.session.add(ua)
        db.session.commit()

        client = logged_in_client(user_id=kid.id)
        resp = client.post("/api/achievements/notifications/dismiss",
                           json={}, content_type="application/json")
        assert resp.status_code == 200

        # Verify dismissed
        resp2 = client.get("/api/achievements/notifications")
        assert len(resp2.get_json()["notifications"]) == 0

    def test_dismiss_specific_notification(self, app, logged_in_client, sample_users):
        seed_achievements()
        kid = sample_users["kid1"]
        a1 = Achievement.query.filter_by(name="First Steps").first()
        a2 = Achievement.query.filter_by(name="Penny Saver").first()
        db.session.add(UserAchievement(user_id=kid.id, achievement_id=a1.id, notified=False))
        db.session.add(UserAchievement(user_id=kid.id, achievement_id=a2.id, notified=False))
        db.session.commit()

        client = logged_in_client(user_id=kid.id)
        resp = client.post("/api/achievements/notifications/dismiss",
                           json={"achievement_ids": [a1.id]},
                           content_type="application/json")
        assert resp.status_code == 200

        # Should still have one unnotified
        resp2 = client.get("/api/achievements/notifications")
        data = resp2.get_json()
        assert len(data["notifications"]) == 1
        assert data["notifications"][0]["achievement"]["name"] == "Penny Saver"


class TestAchievementCatalog:
    """Catalog endpoint tests."""

    def test_catalog_returns_all_14(self, app, logged_in_client, sample_users):
        seed_achievements()
        client = logged_in_client(user_id=sample_users["kid1"].id)
        resp = client.get("/api/achievements/catalog")
        data = resp.get_json()
        assert len(data["achievements"]) == 14

    def test_catalog_shows_locked_unlocked(self, app, logged_in_client, sample_users):
        seed_achievements()
        kid = sample_users["kid1"]
        achievement = Achievement.query.filter_by(name="First Steps").first()
        db.session.add(UserAchievement(user_id=kid.id, achievement_id=achievement.id))
        db.session.commit()

        client = logged_in_client(user_id=kid.id)
        resp = client.get("/api/achievements/catalog")
        data = resp.get_json()

        first_steps = next(a for a in data["achievements"] if a["name"] == "First Steps")
        assert first_steps["unlocked"] is True

        week_warrior = next(a for a in data["achievements"] if a["name"] == "Week Warrior")
        assert week_warrior["unlocked"] is False

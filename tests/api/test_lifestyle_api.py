"""Tests for the Lifestyle Points system — Feature 4."""
from datetime import date, datetime, timedelta

import pytest

from app.models.lifestyle import (
    LifestyleGoal,
    LifestyleLog,
    LifestylePrivilege,
    LifestyleRedemption,
)
from app.models.user import User


# ── fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def kid_client(logged_in_client, sample_users):
    return logged_in_client(user_id=sample_users["kid1"].id)


@pytest.fixture
def kid_id(sample_users):
    return sample_users["kid1"].id


@pytest.fixture
def goal(app, db, sample_users):
    with app.app_context():
        g = LifestyleGoal(
            user_id=sample_users["kid1"].id,
            name="Exercise",
            weekly_target=3,
            active=True,
            created_at=datetime.utcnow(),
        )
        db.session.add(g)
        db.session.commit()
        yield g


@pytest.fixture
def privilege(app, db):
    with app.app_context():
        p = LifestylePrivilege(
            name="Extra Screen Time",
            description="30 minutes extra",
            point_cost=2,
            active=True,
            created_at=datetime.utcnow(),
        )
        db.session.add(p)
        db.session.commit()
        yield p


# ── Goals CRUD ─────────────────────────────────────────────────────────

class TestGoalsCRUD:
    def test_create_goal(self, kid_client):
        resp = kid_client.post(
            "/api/lifestyle/goals",
            json={"name": "Read", "weekly_target": 5},
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["name"] == "Read"
        assert data["weekly_target"] == 5

    def test_create_goal_requires_name(self, kid_client):
        resp = kid_client.post("/api/lifestyle/goals", json={"weekly_target": 3})
        assert resp.status_code == 400

    def test_get_goals_returns_active_only(self, kid_client, app, db, sample_users):
        with app.app_context():
            active = LifestyleGoal(
                user_id=sample_users["kid1"].id, name="Active",
                weekly_target=3, active=True, created_at=datetime.utcnow()
            )
            inactive = LifestyleGoal(
                user_id=sample_users["kid1"].id, name="Inactive",
                weekly_target=3, active=False, created_at=datetime.utcnow()
            )
            db.session.add_all([active, inactive])
            db.session.commit()
        resp = kid_client.get("/api/lifestyle/goals")
        assert resp.status_code == 200
        data = resp.get_json()
        names = [g["name"] for g in data["goals"]]
        assert "Active" in names
        assert "Inactive" not in names

    def test_update_goal_name(self, kid_client, goal):
        resp = kid_client.put(
            f"/api/lifestyle/goals/{goal.id}",
            json={"name": "Morning Jog"},
        )
        assert resp.status_code == 200
        assert resp.get_json()["name"] == "Morning Jog"

    def test_update_goal_target(self, kid_client, goal):
        resp = kid_client.put(
            f"/api/lifestyle/goals/{goal.id}",
            json={"weekly_target": 7},
        )
        assert resp.status_code == 200
        assert resp.get_json()["weekly_target"] == 7

    def test_deactivate_goal(self, kid_client, app, db, goal):
        resp = kid_client.delete(f"/api/lifestyle/goals/{goal.id}")
        assert resp.status_code == 200
        with app.app_context():
            g = db.session.get(LifestyleGoal, goal.id)
            assert g.active is False

    def test_cannot_update_other_users_goal(
        self, logged_in_client, sample_users, goal
    ):
        client = logged_in_client(user_id=sample_users["kid2"].id)
        resp = client.put(
            f"/api/lifestyle/goals/{goal.id}",
            json={"name": "Hacked"},
        )
        assert resp.status_code == 404


# ── Logging ────────────────────────────────────────────────────────────

class TestGoalLogging:
    def test_log_today(self, kid_client, app, db, goal):
        resp = kid_client.post(f"/api/lifestyle/goals/{goal.id}/log")
        assert resp.status_code == 200
        with app.app_context():
            log = LifestyleLog.query.filter_by(
                goal_id=goal.id, log_date=date.today()
            ).first()
            assert log is not None

    def test_log_is_idempotent(self, kid_client, app, db, goal):
        kid_client.post(f"/api/lifestyle/goals/{goal.id}/log")
        kid_client.post(f"/api/lifestyle/goals/{goal.id}/log")
        with app.app_context():
            count = LifestyleLog.query.filter_by(goal_id=goal.id).count()
            assert count == 1

    def test_today_logged_flag(self, kid_client, goal):
        resp = kid_client.get("/api/lifestyle/goals")
        data = resp.get_json()
        g = next(g for g in data["goals"] if g["id"] == goal.id)
        assert g["today_logged"] is False

        kid_client.post(f"/api/lifestyle/goals/{goal.id}/log")

        resp = kid_client.get("/api/lifestyle/goals")
        data = resp.get_json()
        g = next(g for g in data["goals"] if g["id"] == goal.id)
        assert g["today_logged"] is True

    def test_this_week_count(self, kid_client, app, db, goal, sample_users):
        # Seed logs for today and (if in same week) yesterday
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        days_to_seed = [today]
        if today > monday:  # yesterday is still in the same week
            days_to_seed.append(today - timedelta(days=1))
        with app.app_context():
            g = db.session.get(LifestyleGoal, goal.id)
            uid = g.user_id
            for log_date in days_to_seed:
                if not LifestyleLog.query.filter_by(
                    goal_id=goal.id, log_date=log_date
                ).first():
                    db.session.add(LifestyleLog(
                        goal_id=goal.id, user_id=uid, log_date=log_date
                    ))
            db.session.commit()

        resp = kid_client.get("/api/lifestyle/goals")
        data = resp.get_json()
        g = next(x for x in data["goals"] if x["id"] == goal.id)
        assert g["this_week_count"] == len(days_to_seed)

    def test_on_track_false_when_below_target(self, kid_client, goal):
        resp = kid_client.get("/api/lifestyle/goals")
        data = resp.get_json()
        g = next(x for x in data["goals"] if x["id"] == goal.id)
        assert g["on_track"] is False  # 0 of 3


# ── Weekly Reset awards points ─────────────────────────────────────────

class TestWeeklyLifestyleReset:
    def test_weekly_reset_awards_point_when_all_goals_met(
        self, app, db, sample_users
    ):
        with app.app_context():
            kid = db.session.get(User, sample_users["kid1"].id)
            # Give goal with target=2
            goal = LifestyleGoal(
                user_id=kid.id, name="Exercise",
                weekly_target=2, active=True, created_at=datetime.utcnow()
            )
            db.session.add(goal)
            db.session.flush()
            # Log Monday and Tuesday of current week
            monday = date.today() - timedelta(days=date.today().weekday())
            db.session.add(LifestyleLog(goal_id=goal.id, user_id=kid.id, log_date=monday))
            db.session.add(LifestyleLog(goal_id=goal.id, user_id=kid.id,
                                        log_date=monday + timedelta(days=1)))
            db.session.commit()

            from app.blueprints.chores import _process_lifestyle_points
            _process_lifestyle_points()

            db.session.refresh(kid)
            assert kid.lifestyle_points >= 1

    def test_weekly_reset_no_point_when_goal_not_met(self, app, db, sample_users):
        with app.app_context():
            kid = db.session.get(User, sample_users["kid1"].id)
            original_points = kid.lifestyle_points or 0
            # Goal with target=5 but only 1 log
            goal = LifestyleGoal(
                user_id=kid.id, name="Piano",
                weekly_target=5, active=True, created_at=datetime.utcnow()
            )
            db.session.add(goal)
            db.session.flush()
            monday = date.today() - timedelta(days=date.today().weekday())
            db.session.add(LifestyleLog(goal_id=goal.id, user_id=kid.id, log_date=monday))
            db.session.commit()

            from app.blueprints.chores import _process_lifestyle_points
            _process_lifestyle_points()

            db.session.refresh(kid)
            assert kid.lifestyle_points == original_points

    def test_weekly_reset_no_point_when_no_active_goals(self, app, db, sample_users):
        with app.app_context():
            kid = db.session.get(User, sample_users["kid2"].id)
            original_points = kid.lifestyle_points or 0
            from app.blueprints.chores import _process_lifestyle_points
            _process_lifestyle_points()
            db.session.refresh(kid)
            assert kid.lifestyle_points == original_points


# ── Privileges & Redemptions ───────────────────────────────────────────

class TestPrivileges:
    def test_get_active_privileges(self, kid_client, privilege):
        resp = kid_client.get("/api/lifestyle/privileges")
        assert resp.status_code == 200
        data = resp.get_json()
        assert any(p["id"] == privilege.id for p in data["privileges"])

    def test_redeem_succeeds_with_enough_points(
        self, kid_client, app, db, sample_users, privilege
    ):
        with app.app_context():
            kid = db.session.get(User, sample_users["kid1"].id)
            kid.lifestyle_points = 5
            db.session.commit()

        resp = kid_client.post(
            "/api/lifestyle/redeem",
            json={"privilege_id": privilege.id},
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["status"] == "pending"
        assert data["points_spent"] == privilege.point_cost

    def test_redeem_deducts_points(
        self, kid_client, app, db, sample_users, privilege
    ):
        with app.app_context():
            kid = db.session.get(User, sample_users["kid1"].id)
            kid.lifestyle_points = 5
            db.session.commit()

        kid_client.post("/api/lifestyle/redeem", json={"privilege_id": privilege.id})

        with app.app_context():
            kid = db.session.get(User, sample_users["kid1"].id)
            assert kid.lifestyle_points == 5 - privilege.point_cost

    def test_redeem_fails_with_insufficient_points(
        self, kid_client, app, db, sample_users, privilege
    ):
        with app.app_context():
            kid = db.session.get(User, sample_users["kid1"].id)
            kid.lifestyle_points = 0
            db.session.commit()

        resp = kid_client.post(
            "/api/lifestyle/redeem",
            json={"privilege_id": privilege.id},
        )
        assert resp.status_code == 400

    def test_cancel_pending_redemption_refunds_points(
        self, kid_client, app, db, sample_users, privilege
    ):
        with app.app_context():
            kid = db.session.get(User, sample_users["kid1"].id)
            kid.lifestyle_points = 5
            db.session.commit()

        resp = kid_client.post(
            "/api/lifestyle/redeem", json={"privilege_id": privilege.id}
        )
        redemption_id = resp.get_json()["id"]

        resp = kid_client.post(
            f"/api/lifestyle/redemptions/{redemption_id}/cancel"
        )
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "cancelled"

        with app.app_context():
            kid = db.session.get(User, sample_users["kid1"].id)
            assert kid.lifestyle_points == 5  # refunded

    def test_cancel_non_pending_returns_400(
        self, kid_client, app, db, sample_users, privilege
    ):
        with app.app_context():
            kid = db.session.get(User, sample_users["kid1"].id)
            kid.lifestyle_points = 5
            redemption = LifestyleRedemption(
                user_id=kid.id,
                privilege_id=privilege.id,
                points_spent=privilege.point_cost,
                status=LifestyleRedemption.STATUS_COMPLETED,
                redeemed_at=datetime.utcnow(),
            )
            kid.lifestyle_points = 5
            db.session.add(redemption)
            db.session.commit()
            rid = redemption.id

        resp = kid_client.post(f"/api/lifestyle/redemptions/{rid}/cancel")
        assert resp.status_code == 400

    def test_get_redemptions(self, kid_client, app, db, sample_users, privilege):
        with app.app_context():
            kid = db.session.get(User, sample_users["kid1"].id)
            kid.lifestyle_points = 10
            db.session.commit()

        kid_client.post("/api/lifestyle/redeem", json={"privilege_id": privilege.id})
        resp = kid_client.get("/api/lifestyle/redemptions")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["redemptions"]) == 1


# ── Admin Privilege CRUD ───────────────────────────────────────────────

class TestAdminPrivilegeCRUD:
    def test_admin_create_privilege(self, admin_client):
        resp = admin_client.post(
            "/api/admin/lifestyle/privileges",
            json={"name": "Movie Night", "description": "Pick the movie", "point_cost": 3},
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["name"] == "Movie Night"
        assert data["point_cost"] == 3

    def test_admin_create_requires_name(self, admin_client):
        resp = admin_client.post(
            "/api/admin/lifestyle/privileges",
            json={"point_cost": 2},
        )
        assert resp.status_code == 400

    def test_admin_list_all_privileges(self, admin_client, privilege):
        resp = admin_client.get("/api/admin/lifestyle/privileges")
        assert resp.status_code == 200
        data = resp.get_json()
        assert any(p["id"] == privilege.id for p in data["privileges"])

    def test_admin_update_privilege(self, admin_client, privilege):
        resp = admin_client.put(
            f"/api/admin/lifestyle/privileges/{privilege.id}",
            json={"name": "Updated Name", "point_cost": 5},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["name"] == "Updated Name"
        assert data["point_cost"] == 5

    def test_admin_deactivate_privilege(self, admin_client, app, db, privilege):
        resp = admin_client.delete(
            f"/api/admin/lifestyle/privileges/{privilege.id}"
        )
        assert resp.status_code == 200
        with app.app_context():
            p = db.session.get(LifestylePrivilege, privilege.id)
            assert p.active is False

    def test_non_admin_cannot_create_privilege(self, kid_client):
        resp = kid_client.post(
            "/api/admin/lifestyle/privileges",
            json={"name": "Free candy", "point_cost": 1},
        )
        assert resp.status_code == 403

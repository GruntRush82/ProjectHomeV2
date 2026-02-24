"""Lifestyle Points — goals, logs, privileges, and redemptions."""

from datetime import date, datetime, timedelta

from flask import Blueprint, jsonify, request, session

from app.extensions import db
from app.models.lifestyle import (
    LifestyleGoal,
    LifestyleLog,
    LifestylePrivilege,
    LifestyleRedemption,
)
from app.models.user import User

lifestyle_bp = Blueprint("lifestyle", __name__)


# ── helpers ────────────────────────────────────────────────────────────

def _require_user():
    """Return (user, None) or (None, error_response)."""
    uid = session.get("current_user_id")
    if not uid:
        return None, (jsonify({"error": "Not logged in"}), 401)
    user = db.session.get(User, uid)
    if not user:
        return None, (jsonify({"error": "User not found"}), 404)
    return user, None


def _require_admin():
    user, err = _require_user()
    if err:
        return None, err
    if not user.is_admin:
        return None, (jsonify({"error": "Admin required"}), 403)
    return user, None


def _week_start():
    today = date.today()
    return today - timedelta(days=today.weekday())  # Monday


# ── Goals ──────────────────────────────────────────────────────────────

@lifestyle_bp.route("/api/lifestyle/goals", methods=["GET"])
def get_goals():
    user, err = _require_user()
    if err:
        return err

    ws = _week_start()
    goals = LifestyleGoal.query.filter_by(user_id=user.id, active=True).all()
    on_track_count = sum(1 for g in goals if g.to_dict(week_start=ws)["on_track"])
    return jsonify({
        "goals": [g.to_dict(week_start=ws) for g in goals],
        "on_track_count": on_track_count,
        "total_goals": len(goals),
        "lifestyle_points": user.lifestyle_points or 0,
    })


@lifestyle_bp.route("/api/lifestyle/goals", methods=["POST"])
def create_goal():
    user, err = _require_user()
    if err:
        return err

    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name is required"}), 400
    weekly_target = int(data.get("weekly_target") or 5)
    if weekly_target < 1:
        weekly_target = 1

    goal = LifestyleGoal(
        user_id=user.id,
        name=name,
        weekly_target=weekly_target,
        active=True,
        created_at=datetime.utcnow(),
    )
    db.session.add(goal)
    db.session.commit()

    ws = _week_start()
    return jsonify(goal.to_dict(week_start=ws)), 201


@lifestyle_bp.route("/api/lifestyle/goals/<int:goal_id>", methods=["PUT"])
def update_goal(goal_id):
    user, err = _require_user()
    if err:
        return err

    goal = LifestyleGoal.query.filter_by(id=goal_id, user_id=user.id).first()
    if not goal:
        return jsonify({"error": "Goal not found"}), 404

    data = request.get_json() or {}
    if "name" in data:
        name = (data["name"] or "").strip()
        if not name:
            return jsonify({"error": "name cannot be empty"}), 400
        goal.name = name
    if "weekly_target" in data:
        wt = int(data["weekly_target"] or 1)
        goal.weekly_target = max(1, wt)

    db.session.commit()
    ws = _week_start()
    return jsonify(goal.to_dict(week_start=ws))


@lifestyle_bp.route("/api/lifestyle/goals/<int:goal_id>", methods=["DELETE"])
def deactivate_goal(goal_id):
    user, err = _require_user()
    if err:
        return err

    goal = LifestyleGoal.query.filter_by(id=goal_id, user_id=user.id).first()
    if not goal:
        return jsonify({"error": "Goal not found"}), 404

    goal.active = False
    db.session.commit()
    return jsonify({"ok": True})


@lifestyle_bp.route("/api/lifestyle/goals/<int:goal_id>/log", methods=["POST"])
def log_goal(goal_id):
    user, err = _require_user()
    if err:
        return err

    goal = LifestyleGoal.query.filter_by(
        id=goal_id, user_id=user.id, active=True
    ).first()
    if not goal:
        return jsonify({"error": "Goal not found"}), 404

    today = date.today()
    existing = LifestyleLog.query.filter_by(goal_id=goal_id, log_date=today).first()
    if not existing:
        log = LifestyleLog(goal_id=goal_id, user_id=user.id, log_date=today)
        db.session.add(log)
        db.session.commit()

    ws = _week_start()
    return jsonify(goal.to_dict(week_start=ws))


@lifestyle_bp.route("/api/lifestyle/goals/<int:goal_id>/log", methods=["DELETE"])
def unlog_goal(goal_id):
    user, err = _require_user()
    if err:
        return err

    goal = LifestyleGoal.query.filter_by(
        id=goal_id, user_id=user.id, active=True
    ).first()
    if not goal:
        return jsonify({"error": "Goal not found"}), 404

    today = date.today()
    existing = LifestyleLog.query.filter_by(goal_id=goal_id, log_date=today).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()

    ws = _week_start()
    return jsonify(goal.to_dict(week_start=ws))


# ── Privileges ─────────────────────────────────────────────────────────

@lifestyle_bp.route("/api/lifestyle/privileges", methods=["GET"])
def get_privileges():
    user, err = _require_user()
    if err:
        return err

    privileges = LifestylePrivilege.query.filter_by(active=True).all()
    return jsonify({
        "privileges": [p.to_dict() for p in privileges],
        "lifestyle_points": user.lifestyle_points or 0,
    })


# ── Redemptions ────────────────────────────────────────────────────────

@lifestyle_bp.route("/api/lifestyle/redeem", methods=["POST"])
def redeem_privilege():
    user, err = _require_user()
    if err:
        return err

    data = request.get_json() or {}
    privilege_id = data.get("privilege_id")
    if not privilege_id:
        return jsonify({"error": "privilege_id required"}), 400

    privilege = db.session.get(LifestylePrivilege, int(privilege_id))
    if not privilege or not privilege.active:
        return jsonify({"error": "Privilege not found"}), 404

    points = user.lifestyle_points or 0
    if points < privilege.point_cost:
        return jsonify({"error": "Insufficient points"}), 400

    # Check if this is user's first redemption (before deducting)
    is_first = LifestyleRedemption.query.filter_by(user_id=user.id).count() == 0

    user.lifestyle_points = points - privilege.point_cost
    redemption = LifestyleRedemption(
        user_id=user.id,
        privilege_id=privilege.id,
        points_spent=privilege.point_cost,
        status=LifestyleRedemption.STATUS_PENDING,
        redeemed_at=datetime.utcnow(),
    )
    db.session.add(redemption)
    db.session.commit()

    # Achievement: Privilege Unlocked — fire on first-ever redemption
    if is_first:
        try:
            from app.services.achievements import check_achievements
            check_achievements(user.id, "lifestyle_privilege_unlocked")
            db.session.commit()
        except Exception:
            pass

    return jsonify(redemption.to_dict()), 201


@lifestyle_bp.route("/api/lifestyle/redemptions", methods=["GET"])
def get_redemptions():
    user, err = _require_user()
    if err:
        return err

    redemptions = (
        LifestyleRedemption.query
        .filter_by(user_id=user.id)
        .order_by(LifestyleRedemption.redeemed_at.desc())
        .all()
    )
    return jsonify({
        "redemptions": [r.to_dict() for r in redemptions],
        "lifestyle_points": user.lifestyle_points or 0,
    })


@lifestyle_bp.route(
    "/api/lifestyle/redemptions/<int:redemption_id>/cancel", methods=["POST"]
)
def cancel_redemption(redemption_id):
    user, err = _require_user()
    if err:
        return err

    redemption = LifestyleRedemption.query.filter_by(
        id=redemption_id, user_id=user.id
    ).first()
    if not redemption:
        return jsonify({"error": "Redemption not found"}), 404
    if redemption.status != LifestyleRedemption.STATUS_PENDING:
        return jsonify({"error": "Only pending redemptions can be cancelled"}), 400

    redemption.status = LifestyleRedemption.STATUS_CANCELLED
    redemption.cancelled_at = datetime.utcnow()
    user.lifestyle_points = (user.lifestyle_points or 0) + redemption.points_spent
    db.session.commit()

    return jsonify(redemption.to_dict())


@lifestyle_bp.route(
    "/api/lifestyle/redemptions/<int:redemption_id>/complete", methods=["POST"]
)
def complete_redemption(redemption_id):
    """Kid confirms they received their reward — marks redemption as completed."""
    user, err = _require_user()
    if err:
        return err

    redemption = LifestyleRedemption.query.filter_by(
        id=redemption_id, user_id=user.id
    ).first()
    if not redemption:
        return jsonify({"error": "Redemption not found"}), 404
    if redemption.status != LifestyleRedemption.STATUS_PENDING:
        return jsonify({"error": "Only pending redemptions can be completed"}), 400

    redemption.status = LifestyleRedemption.STATUS_COMPLETED
    redemption.completed_at = datetime.utcnow()
    db.session.commit()

    return jsonify(redemption.to_dict())


# ── Admin Privileges ───────────────────────────────────────────────────

@lifestyle_bp.route("/api/admin/lifestyle/privileges", methods=["GET"])
def admin_get_privileges():
    _, err = _require_admin()
    if err:
        return err

    privileges = LifestylePrivilege.query.order_by(LifestylePrivilege.id).all()
    return jsonify({"privileges": [p.to_dict() for p in privileges]})


@lifestyle_bp.route("/api/admin/lifestyle/privileges", methods=["POST"])
def admin_create_privilege():
    _, err = _require_admin()
    if err:
        return err

    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name required"}), 400
    point_cost = int(data.get("point_cost") or 1)
    if point_cost < 1:
        return jsonify({"error": "point_cost must be >= 1"}), 400

    privilege = LifestylePrivilege(
        name=name,
        description=(data.get("description") or "").strip() or None,
        point_cost=point_cost,
        active=True,
        created_at=datetime.utcnow(),
    )
    db.session.add(privilege)
    db.session.commit()
    return jsonify(privilege.to_dict()), 201


@lifestyle_bp.route(
    "/api/admin/lifestyle/privileges/<int:privilege_id>", methods=["PUT"]
)
def admin_update_privilege(privilege_id):
    _, err = _require_admin()
    if err:
        return err

    privilege = db.session.get(LifestylePrivilege, privilege_id)
    if not privilege:
        return jsonify({"error": "Privilege not found"}), 404

    data = request.get_json() or {}
    if "name" in data:
        name = (data["name"] or "").strip()
        if not name:
            return jsonify({"error": "name cannot be empty"}), 400
        privilege.name = name
    if "description" in data:
        privilege.description = (data["description"] or "").strip() or None
    if "point_cost" in data:
        point_cost = int(data["point_cost"] or 1)
        if point_cost < 1:
            return jsonify({"error": "point_cost must be >= 1"}), 400
        privilege.point_cost = point_cost
    if "active" in data:
        privilege.active = bool(data["active"])

    db.session.commit()
    return jsonify(privilege.to_dict())


@lifestyle_bp.route(
    "/api/admin/lifestyle/privileges/<int:privilege_id>", methods=["DELETE"]
)
def admin_deactivate_privilege(privilege_id):
    _, err = _require_admin()
    if err:
        return err

    privilege = db.session.get(LifestylePrivilege, privilege_id)
    if not privilege:
        return jsonify({"error": "Privilege not found"}), 404

    privilege.active = False
    db.session.commit()
    return jsonify({"ok": True})

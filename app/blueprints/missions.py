"""Missions blueprint — user training/testing + admin assignment/approval."""

from datetime import datetime

from flask import Blueprint, jsonify, render_template, request, session

from app.extensions import db
from app.models.bank import BankAccount, Transaction
from app.models.mission import Mission, MissionAssignment, MissionProgress
from app.models.user import User
from app.services.missions import get_handler

missions_bp = Blueprint("missions", __name__)


# ── helpers ──────────────────────────────────────────────────────────

def _require_login():
    """Return (user_id, user) or abort with 401."""
    user_id = session.get("current_user_id")
    if not user_id:
        return None, None
    user = db.session.get(User, user_id)
    if not user:
        return None, None
    return user_id, user


def _require_admin():
    """Return (user_id, user) if admin, else (None, None)."""
    user_id, user = _require_login()
    if not user or not user.is_admin:
        return None, None
    return user_id, user


def _get_assignment_for_user(assignment_id, user_id):
    """Get assignment if it belongs to the user."""
    assignment = db.session.get(MissionAssignment, assignment_id)
    if not assignment or assignment.user_id != user_id:
        return None
    return assignment


def _grant_mission_reward(assignment):
    """Deposit cash reward to user's bank and auto-equip icon."""
    mission = assignment.mission
    user = assignment.user

    # Deposit cash reward
    if mission.reward_cash > 0:
        account = BankAccount.query.filter_by(user_id=user.id).first()
        if not account:
            account = BankAccount(user_id=user.id)
            db.session.add(account)
            db.session.flush()

        account.cash_balance += mission.reward_cash

        txn = Transaction(
            user_id=user.id,
            type=Transaction.TYPE_MISSION_REWARD,
            amount=mission.reward_cash,
            balance_after=round(account.cash_balance, 2),
            description=f"Mission reward: {mission.title}",
        )
        db.session.add(txn)

    # Auto-equip the mission icon
    if mission.reward_icon:
        user.icon = mission.reward_icon

    db.session.commit()

    # Grant mission completion XP
    from app.services.xp import grant_xp
    grant_xp(user.id, 500, "mission_complete")


# ── page routes ──────────────────────────────────────────────────────

@missions_bp.route("/missions")
def missions_page():
    """Render the missions hub."""
    return render_template("missions.html", active_nav="missions")


@missions_bp.route("/admin/missions")
def admin_missions_page():
    """Render the admin missions page."""
    user_id, user = _require_admin()
    if not user:
        return jsonify({"error": "Admin access required"}), 403
    return render_template("admin_missions.html", active_nav="missions")


# ── user API routes ──────────────────────────────────────────────────

@missions_bp.route("/api/missions")
def list_missions():
    """List current user's mission assignments."""
    user_id, user = _require_login()
    if not user:
        return jsonify({"error": "Not logged in"}), 401

    assignments = MissionAssignment.query.filter_by(user_id=user_id).order_by(
        MissionAssignment.assigned_at.desc()
    ).all()

    active = [a.to_dict() for a in assignments if a.state != MissionAssignment.STATE_COMPLETED]
    completed = [a.to_dict() for a in assignments if a.state == MissionAssignment.STATE_COMPLETED]

    return jsonify({"active": active, "completed": completed})


@missions_bp.route("/api/missions/<int:assignment_id>/progress")
def mission_progress(assignment_id):
    """Get progress summary for a mission assignment."""
    user_id, user = _require_login()
    if not user:
        return jsonify({"error": "Not logged in"}), 401

    assignment = _get_assignment_for_user(assignment_id, user_id)
    if not assignment:
        return jsonify({"error": "Assignment not found"}), 404

    handler = get_handler(assignment.mission.mission_type)
    if not handler:
        return jsonify({"error": "Unknown mission type"}), 500

    summary = handler.get_progress_summary(assignment)
    summary["assignment"] = assignment.to_dict()
    return jsonify(summary)


@missions_bp.route("/missions/<int:assignment_id>/start", methods=["POST"])
def start_mission(assignment_id):
    """Transition from assigned → training."""
    user_id, user = _require_login()
    if not user:
        return jsonify({"error": "Not logged in"}), 401

    assignment = _get_assignment_for_user(assignment_id, user_id)
    if not assignment:
        return jsonify({"error": "Assignment not found"}), 404

    if assignment.state != MissionAssignment.STATE_ASSIGNED:
        return jsonify({"error": "Mission already started"}), 400

    assignment.state = MissionAssignment.STATE_TRAINING
    assignment.started_at = datetime.utcnow()
    db.session.commit()

    return jsonify(assignment.to_dict())


@missions_bp.route("/api/missions/<int:assignment_id>/train")
def get_training(assignment_id):
    """Get a training session."""
    user_id, user = _require_login()
    if not user:
        return jsonify({"error": "Not logged in"}), 401

    assignment = _get_assignment_for_user(assignment_id, user_id)
    if not assignment:
        return jsonify({"error": "Assignment not found"}), 404

    allowed_states = {
        MissionAssignment.STATE_ASSIGNED,
        MissionAssignment.STATE_TRAINING,
        MissionAssignment.STATE_FAILED,
    }
    if assignment.state not in allowed_states:
        return jsonify({"error": "Cannot train in current state"}), 400

    handler = get_handler(assignment.mission.mission_type)
    if not handler:
        return jsonify({"error": "Unknown mission type"}), 500

    session_data = handler.get_training_session(assignment)
    return jsonify(session_data)


@missions_bp.route("/missions/<int:assignment_id>/train", methods=["POST"])
def submit_training(assignment_id):
    """Submit training session results."""
    user_id, user = _require_login()
    if not user:
        return jsonify({"error": "Not logged in"}), 401

    assignment = _get_assignment_for_user(assignment_id, user_id)
    if not assignment:
        return jsonify({"error": "Assignment not found"}), 404

    handler = get_handler(assignment.mission.mission_type)
    if not handler:
        return jsonify({"error": "Unknown mission type"}), 500

    data = request.get_json(silent=True) or {}
    result = handler.evaluate_training(assignment, data)
    return jsonify(result)


@missions_bp.route("/api/missions/<int:assignment_id>/test")
def get_test(assignment_id):
    """Get a test for the next level."""
    user_id, user = _require_login()
    if not user:
        return jsonify({"error": "Not logged in"}), 401

    assignment = _get_assignment_for_user(assignment_id, user_id)
    if not assignment:
        return jsonify({"error": "Assignment not found"}), 404

    allowed_states = {
        MissionAssignment.STATE_TRAINING,
        MissionAssignment.STATE_FAILED,
    }
    if assignment.state not in allowed_states:
        return jsonify({"error": "Cannot test in current state"}), 400

    handler = get_handler(assignment.mission.mission_type)
    if not handler:
        return jsonify({"error": "Unknown mission type"}), 500

    level = request.args.get("level", type=int)
    test_data = handler.get_test(assignment, level=level)

    # Remove server-side answers before sending to client
    test_data.pop("_answers", None)

    return jsonify(test_data)


@missions_bp.route("/missions/<int:assignment_id>/test", methods=["POST"])
def submit_test(assignment_id):
    """Submit test results."""
    user_id, user = _require_login()
    if not user:
        return jsonify({"error": "Not logged in"}), 401

    assignment = _get_assignment_for_user(assignment_id, user_id)
    if not assignment:
        return jsonify({"error": "Assignment not found"}), 404

    handler = get_handler(assignment.mission.mission_type)
    if not handler:
        return jsonify({"error": "Unknown mission type"}), 500

    data = request.get_json(silent=True) or {}
    result = handler.evaluate_test(assignment, data)

    # If mission completed, grant rewards
    if result.get("completed") or result.get("pending_approval"):
        if assignment.state == MissionAssignment.STATE_COMPLETED:
            _grant_mission_reward(assignment)
            result["reward"] = {
                "cash": assignment.mission.reward_cash,
                "icon": assignment.mission.reward_icon,
            }

    return jsonify(result)


# ── notification routes ──────────────────────────────────────────────

@missions_bp.route("/api/missions/notifications")
def get_notifications():
    """Get unnotified mission assignments for the current user."""
    user_id, user = _require_login()
    if not user:
        return jsonify({"error": "Not logged in"}), 401

    unnotified = MissionAssignment.query.filter_by(
        user_id=user_id, notified=False,
    ).all()

    return jsonify({
        "notifications": [a.to_dict() for a in unnotified],
    })


@missions_bp.route("/api/missions/notifications/dismiss", methods=["POST"])
def dismiss_notifications():
    """Mark all notifications as seen."""
    user_id, user = _require_login()
    if not user:
        return jsonify({"error": "Not logged in"}), 401

    unnotified = MissionAssignment.query.filter_by(
        user_id=user_id, notified=False,
    ).all()

    for a in unnotified:
        a.notified = True
    db.session.commit()

    return jsonify({"dismissed": len(unnotified)})


# ── admin API routes ─────────────────────────────────────────────────

@missions_bp.route("/api/admin/missions")
def admin_list_missions():
    """List all missions, assignments, and users for admin."""
    user_id, user = _require_admin()
    if not user:
        return jsonify({"error": "Admin access required"}), 403

    missions = Mission.query.all()
    assignments = MissionAssignment.query.order_by(
        MissionAssignment.assigned_at.desc()
    ).all()
    users = User.query.filter_by(is_admin=False).order_by(User.id).all()

    return jsonify({
        "missions": [m.to_dict() for m in missions],
        "assignments": [a.to_dict() for a in assignments],
        "users": [{"id": u.id, "username": u.username} for u in users],
    })


@missions_bp.route("/api/admin/missions/assign", methods=["POST"])
def admin_assign_mission():
    """Assign a mission to a user."""
    user_id, user = _require_admin()
    if not user:
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json(silent=True) or {}
    mission_id = data.get("mission_id")
    target_user_id = data.get("user_id")

    if not mission_id or not target_user_id:
        return jsonify({"error": "mission_id and user_id required"}), 400

    mission = db.session.get(Mission, mission_id)
    if not mission:
        return jsonify({"error": "Mission not found"}), 404

    target_user = db.session.get(User, target_user_id)
    if not target_user:
        return jsonify({"error": "User not found"}), 404

    assignment = MissionAssignment(
        mission_id=mission_id,
        user_id=target_user_id,
    )
    db.session.add(assignment)
    db.session.commit()

    return jsonify(assignment.to_dict()), 201


@missions_bp.route("/api/admin/missions/<int:assignment_id>/approve", methods=["POST"])
def admin_approve_mission(assignment_id):
    """Approve a pending mission (piano approval)."""
    user_id, user = _require_admin()
    if not user:
        return jsonify({"error": "Admin access required"}), 403

    assignment = db.session.get(MissionAssignment, assignment_id)
    if not assignment:
        return jsonify({"error": "Assignment not found"}), 404

    if assignment.state != MissionAssignment.STATE_PENDING_APPROVAL:
        return jsonify({"error": "Assignment is not pending approval"}), 400

    assignment.state = MissionAssignment.STATE_COMPLETED
    assignment.completed_at = datetime.utcnow()
    db.session.commit()

    _grant_mission_reward(assignment)

    return jsonify({
        "approved": True,
        "assignment": assignment.to_dict(),
        "reward": {
            "cash": assignment.mission.reward_cash,
            "icon": assignment.mission.reward_icon,
        },
    })


@missions_bp.route("/api/admin/missions/<int:assignment_id>/reject", methods=["POST"])
def admin_reject_mission(assignment_id):
    """Reject a pending mission — back to training."""
    user_id, user = _require_admin()
    if not user:
        return jsonify({"error": "Admin access required"}), 403

    assignment = db.session.get(MissionAssignment, assignment_id)
    if not assignment:
        return jsonify({"error": "Assignment not found"}), 404

    if assignment.state != MissionAssignment.STATE_PENDING_APPROVAL:
        return jsonify({"error": "Assignment is not pending approval"}), 400

    assignment.state = MissionAssignment.STATE_TRAINING
    db.session.commit()

    return jsonify({
        "rejected": True,
        "assignment": assignment.to_dict(),
    })

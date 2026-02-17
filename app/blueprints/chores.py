"""Chore routes — CRUD, archive, reset, move."""

from datetime import date, datetime, timedelta

from flask import Blueprint, current_app, jsonify, request

from app.extensions import db
from app.models.chore import Chore, ChoreHistory
from app.models.user import User

chores_bp = Blueprint("chores", __name__)

VALID_DAYS = {
    "Monday", "Tuesday", "Wednesday", "Thursday",
    "Friday", "Saturday", "Sunday",
}


# ── helpers ──────────────────────────────────────────────────────────

def _chore_to_dict(chore):
    return {
        "id": chore.id,
        "description": chore.description,
        "completed": chore.completed,
        "user_id": chore.user_id,
        "username": chore.user.username,
        "day": chore.day,
        "rotation_type": chore.rotation_type,
        "rotation_order": list(chore.rotation_order or []),
    }


def _rotate_chores_once():
    """Advance rotating chores to the next user in rotation_order."""
    rotating = Chore.query.filter_by(rotation_type="rotating").all()
    for chore in rotating:
        order = chore.rotation_order or []
        if not order:
            continue
        anchor_id = chore.base_user_id or chore.user_id
        anchor_user = db.session.get(User, anchor_id)
        if not anchor_user:
            continue
        try:
            nxt = order[(order.index(anchor_user.username) + 1) % len(order)]
        except ValueError:
            continue
        next_user = User.query.filter_by(username=nxt).first()
        if next_user:
            chore.user_id = next_user.id
            chore.base_user_id = next_user.id


def _update_streaks():
    """Update streak counters for all users based on chore completion."""
    users = User.query.all()
    for user in users:
        user_chores = Chore.query.filter_by(user_id=user.id).all()
        if not user_chores:
            continue
        total = len(user_chores)
        done = sum(1 for c in user_chores if c.completed)
        if done == total:
            user.streak_current = (user.streak_current or 0) + 1
            user.perfect_weeks_total = (user.perfect_weeks_total or 0) + 1
            if user.streak_current > user.streak_best:
                user.streak_best = user.streak_current
            # Fire Mode: activate at 3+ consecutive perfect weeks
            user.fire_mode = user.streak_current >= 3
        else:
            user.streak_current = 0
            user.fire_mode = False


def _process_allowance_and_interest():
    """Deposit allowance + credit interest for all users with bank accounts."""
    from app.models.bank import BankAccount, Transaction
    from app.services.allowance import calculate_allowance
    from app.services.interest import credit_interest
    from app.services.xp import grant_xp
    from app.services.achievements import check_achievements

    now = datetime.utcnow()

    for user in User.query.all():
        user_chores = Chore.query.filter_by(user_id=user.id).all()
        if not user_chores and not user.allowance:
            continue

        # Calculate allowance from the ARCHIVED chore state (history just written)
        today = date.today()
        history = ChoreHistory.query.filter_by(
            username=user.username, date=today
        ).all()
        total = len(history)
        completed = sum(1 for h in history if h.completed)

        earned = calculate_allowance(total, completed, user.allowance or 0)

        # Fire Mode: 50% allowance boost
        if user.fire_mode and earned > 0:
            earned = round(earned * 1.5, 2)

        # Get or create bank account
        account = BankAccount.query.filter_by(user_id=user.id).first()
        if not account:
            account = BankAccount(user_id=user.id, created_at=now)
            db.session.add(account)
            db.session.flush()

        # Deposit allowance
        if earned > 0:
            desc_parts = [
                f"Weekly allowance ({completed}/{total} chores, "
                f"{'full' if completed == total else 'half'})"
            ]
            if user.fire_mode:
                desc_parts.append(" +50% FIRE MODE")
            account.cash_balance += earned
            db.session.add(Transaction(
                user_id=user.id,
                type=Transaction.TYPE_ALLOWANCE,
                amount=earned,
                balance_after=round(account.cash_balance, 2),
                description="".join(desc_parts),
                created_at=now,
            ))

        # Weekly bonus XP: 100% week doubles chore XP
        if total > 0 and completed == total:
            # Calculate what chore XP was earned this week
            bonus_xp = 0
            for h in history:
                bonus_xp += 25 if h.rotation_type == "rotating" else 10
            if bonus_xp > 0:
                grant_xp(user.id, bonus_xp, "weekly_bonus")

        # Credit interest on savings
        credit_interest(user.id)

        # Check interest achievement
        db.session.refresh(account)
        if account.total_interest_earned > 0:
            check_achievements(user.id, "interest_credited")

        # Check weekly reset achievements (streaks, perfect weeks)
        check_achievements(user.id, "weekly_reset")

    db.session.commit()


def _expire_trusted_ips():
    """Remove TrustedIP entries older than TRUSTED_IP_EXPIRY_DAYS."""
    from app.models.security import TrustedIP

    expiry_days = current_app.config.get("TRUSTED_IP_EXPIRY_DAYS", 7)
    cutoff = datetime.utcnow() - timedelta(days=expiry_days)
    TrustedIP.query.filter(TrustedIP.trusted_at < cutoff).delete()
    db.session.commit()


def _weekly_archive(*, send_reports=True):
    """Archive current chores, reset, rotate, and update streaks."""
    today = date.today()
    if ChoreHistory.query.filter_by(date=today).first():
        return

    # Update streaks BEFORE archiving (need current completion state)
    _update_streaks()

    for chore in Chore.query.all():
        db.session.add(
            ChoreHistory(
                chore_id=chore.id,
                username=chore.user.username,
                date=today,
                completed=chore.completed,
                day=chore.day,
                rotation_type=chore.rotation_type,
            )
        )
        chore.completed = False

    _rotate_chores_once()
    db.session.commit()

    # ── Phase 3: Bank integration ────────────────────────────────
    _process_allowance_and_interest()
    _expire_trusted_ips()

    if send_reports:
        try:
            from reporting import generate_weekly_reports

            generate_weekly_reports(db.session)
        except ImportError:
            pass


# ── routes ───────────────────────────────────────────────────────────

@chores_bp.route("/chores-page")
def home():
    from flask import render_template

    return render_template("chore_tracker.html", active_nav="chores")


@chores_bp.route("/chores", methods=["GET"])
def get_chores():
    chores = Chore.query.all()
    return jsonify([_chore_to_dict(c) for c in chores])


@chores_bp.route("/chores/<int:id>", methods=["GET"])
def get_chore(id):
    chore = Chore.query.get_or_404(id)
    return jsonify({
        "id": chore.id,
        "description": chore.description,
        "completed": chore.completed,
    })


@chores_bp.route("/chores", methods=["POST"])
def add_chore():
    data = request.get_json()
    description = data.get("description")
    user_id = data.get("user_id")
    day = data.get("day")
    rotation_type = data.get("rotation_type", "static")
    rotation_order = data.get("rotation_order", [])

    if not description or not user_id:
        return jsonify({"error": "Description and user_id are required"}), 400
    if day not in VALID_DAYS:
        return jsonify({"error": "Invalid day(s) provided"}), 400

    new_chore = Chore(
        description=description,
        user_id=user_id,
        day=day,
        rotation_type=rotation_type.lower(),
        rotation_order=rotation_order,
        base_user_id=user_id if rotation_type.lower() == "rotating" else None,
    )
    db.session.add(new_chore)
    db.session.commit()

    return jsonify(_chore_to_dict(new_chore)), 201


@chores_bp.route("/chores/<int:id>", methods=["PUT"])
def update_chore(id):
    chore = Chore.query.get_or_404(id)
    data = request.get_json()

    description = data.get("description")
    completed = data.get("completed")
    was_completed = chore.completed

    if description is not None:
        chore.description = description
    if completed is not None:
        chore.completed = completed

    db.session.commit()

    response = {
        "id": chore.id,
        "description": chore.description,
        "completed": chore.completed,
    }

    # Grant XP on completion (False→True only, no undo deduction)
    if completed is True and not was_completed and chore.user_id:
        from app.services.xp import grant_xp
        from app.services.achievements import check_achievements

        xp_amount = 25 if chore.rotation_type == "rotating" else 10
        xp_result = grant_xp(chore.user_id, xp_amount, "chore_complete")
        achievements = check_achievements(chore.user_id, "chore_complete")
        response["xp"] = xp_result
        response["achievements"] = achievements

    return jsonify(response), 200


@chores_bp.route("/chores/<int:id>", methods=["DELETE"])
def delete_chore(id):
    chore = Chore.query.get_or_404(id)
    ChoreHistory.query.filter_by(chore_id=chore.id).delete()
    db.session.delete(chore)
    db.session.commit()
    return jsonify({"message": "Chore deleted"}), 200


@chores_bp.route("/chores/<int:id>/move", methods=["PUT"])
def move_chore(id):
    chore = Chore.query.get_or_404(id)
    data = request.get_json()
    new_user_id = data.get("user_id")
    new_day = data.get("day")

    if new_day and new_day not in VALID_DAYS:
        return jsonify({"error": "Invalid day provided"}), 400

    if new_user_id is not None:
        user = db.session.get(User, new_user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        chore.user_id = new_user_id

    if new_day:
        chore.day = new_day

    db.session.commit()
    return jsonify(_chore_to_dict(chore)), 200


@chores_bp.route("/chores/archive", methods=["POST"])
def archive_chores():
    for chore in Chore.query.all():
        db.session.add(
            ChoreHistory(
                chore_id=chore.id,
                username=chore.user.username,
                date=date.today(),
                completed=chore.completed,
                day=chore.day,
                rotation_type=chore.rotation_type,
            )
        )
        chore.completed = False
    db.session.commit()
    return jsonify({"message": "All chores archived and reset"}), 200


@chores_bp.route("/chores/reset", methods=["POST"])
def manual_weekly_reset():
    body = request.get_json(silent=True) or {}
    send_flag = bool(body.get("generate_reports"))

    ChoreHistory.query.filter_by(date=date.today()).delete()
    db.session.commit()

    _weekly_archive(send_reports=send_flag)
    return jsonify({
        "message": "Week archived & rotated",
        "reports_sent": send_flag,
        "date": str(date.today()),
    }), 200


@chores_bp.route("/archive", methods=["GET"])
def get_archive():
    history = ChoreHistory.query.all()
    return jsonify([
        {
            "id": r.id,
            "chore_id": r.chore_id,
            "username": r.username,
            "date": r.date.strftime("%Y-%m-%d"),
            "completed": r.completed,
            "day": r.day,
            "rotation_type": r.rotation_type,
        }
        for r in history
    ])


@chores_bp.route("/chores/clear-archive", methods=["DELETE"])
def clear_archive():
    ChoreHistory.query.delete()
    db.session.commit()
    return jsonify({"message": "Chore history cleared successfully"}), 200

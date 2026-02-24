"""Admin dashboard routes — overview, user management, config, trusted IPs, digest."""

import bcrypt
from flask import Blueprint, jsonify, render_template, request, session

from app.extensions import db
from app.models.security import AppConfig, TrustedIP
from app.models.user import User
from app.services.xp import get_level_info

admin_bp = Blueprint("admin", __name__)

# Config key metadata — order determines display order
CONFIG_META = {
    "interest_rate":       {"default": "0.05",  "label": "Weekly interest rate",  "unit": "%"},
    "savings_max":         {"default": "100.0",  "label": "Savings maximum",       "unit": "$"},
    "savings_deposit_min": {"default": "1.0",    "label": "Minimum deposit",       "unit": "$"},
    "cashout_min":         {"default": "1.0",    "label": "Minimum cashout",       "unit": "$"},
    "savings_lock_days":   {"default": "30",     "label": "Savings lock period",   "unit": "days"},
    "fire_mode_bonus_pct": {"default": "50",     "label": "Fire Mode bonus",       "unit": "%"},
    "idle_timeout_min":    {"default": "5",      "label": "Idle timeout",          "unit": "min"},
}


# ── auth helper ───────────────────────────────────────────────────────

def _require_admin():
    """Return (user_id, user, None) on success or (None, None, status_code) on failure."""
    user_id = session.get("current_user_id")
    if not user_id:
        return None, None, 401
    user = db.session.get(User, user_id)
    if not user or not user.is_admin:
        return None, None, 403
    return user_id, user, None


# ── page route ────────────────────────────────────────────────────────

@admin_bp.route("/admin")
def admin_page():
    """Render admin dashboard."""
    user_id, user, err = _require_admin()
    if err:
        from flask import redirect
        return redirect("/")
    return render_template("admin.html", active_nav="admin")


# ── overview ──────────────────────────────────────────────────────────

@admin_bp.route("/api/admin/overview")
def admin_overview():
    """All users: level, XP, cash, savings, fire mode, streak."""
    user_id, admin_user, err = _require_admin()
    if err:
        msg = "Not logged in" if err == 401 else "Admin access required"
        return jsonify({"error": msg}), err

    from app.models.bank import BankAccount, SavingsDeposit
    from app.blueprints.achievements import ICON_ID_TO_EMOJI, ICON_METADATA

    users = User.query.order_by(User.id).all()
    data = []
    for u in users:
        level_info = get_level_info(u.id)
        account = BankAccount.query.filter_by(user_id=u.id).first()

        cash_balance = round(account.cash_balance, 2) if account else 0.0

        if account:
            active_deposits = SavingsDeposit.query.filter_by(
                user_id=u.id, withdrawn=False
            ).all()
            total_savings = round(sum(d.amount for d in active_deposits), 2)
            unlocked_savings = round(
                sum(d.amount for d in active_deposits if d.is_unlocked), 2
            )
        else:
            total_savings = 0.0
            unlocked_savings = 0.0

        icon_id = u.icon or "star_basic"
        icon_emoji = ICON_ID_TO_EMOJI.get(icon_id, icon_id)
        icon_css = ICON_METADATA.get(icon_id, {}).get("css_class", "")

        data.append({
            "id": u.id,
            "username": u.username,
            "icon": icon_id,
            "icon_emoji": icon_emoji,
            "icon_css": icon_css,
            "level": level_info["level"],
            "level_name": level_info["level_name"],
            "xp": level_info["xp"],
            "next_level_xp": level_info["next_level_xp"],
            "cash_balance": cash_balance,
            "total_savings": total_savings,
            "cashout_available": round(cash_balance + unlocked_savings, 2),
            "fire_mode": u.fire_mode,
            "streak_current": u.streak_current,
            "streak_best": u.streak_best,
            "allowance": u.allowance or 0.0,
            "email": u.email or "",
            "is_admin": u.is_admin,
        })

    return jsonify({"users": data})


# ── user management ───────────────────────────────────────────────────

@admin_bp.route("/api/admin/users", methods=["GET"])
def admin_list_users():
    """Full user list with all editable fields."""
    user_id, admin_user, err = _require_admin()
    if err:
        msg = "Not logged in" if err == 401 else "Admin access required"
        return jsonify({"error": msg}), err

    users = User.query.order_by(User.id).all()
    return jsonify({
        "users": [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email or "",
                "allowance": u.allowance or 0.0,
                "is_admin": u.is_admin,
                "level": u.level,
                "xp": u.xp,
                "fire_mode": u.fire_mode,
                "streak_current": u.streak_current,
            }
            for u in users
        ]
    })


@admin_bp.route("/api/admin/users", methods=["POST"])
def admin_create_user():
    """Create a new user."""
    user_id, admin_user, err = _require_admin()
    if err:
        msg = "Not logged in" if err == 401 else "Admin access required"
        return jsonify({"error": msg}), err

    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    if not username:
        return jsonify({"error": "username is required"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists"}), 400

    new_user = User(
        username=username,
        email=data.get("email") or None,
        allowance=float(data.get("allowance", 0)),
        is_admin=bool(data.get("is_admin", False)),
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"id": new_user.id, "username": new_user.username}), 201


@admin_bp.route("/api/admin/users/<int:target_id>", methods=["PUT"])
def admin_update_user(target_id):
    """Update username, email, allowance, is_admin."""
    user_id, admin_user, err = _require_admin()
    if err:
        msg = "Not logged in" if err == 401 else "Admin access required"
        return jsonify({"error": msg}), err

    user = db.session.get(User, target_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json(silent=True) or {}
    if "username" in data:
        user.username = (data["username"] or "").strip()
    if "email" in data:
        user.email = data["email"] or None
    if "allowance" in data:
        user.allowance = float(data["allowance"])
    if "is_admin" in data:
        user.is_admin = bool(data["is_admin"])

    db.session.commit()
    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email or "",
        "allowance": user.allowance,
        "is_admin": user.is_admin,
    })


@admin_bp.route("/api/admin/users/<int:target_id>", methods=["DELETE"])
def admin_delete_user(target_id):
    """Delete user + cascade chores."""
    user_id, admin_user, err = _require_admin()
    if err:
        msg = "Not logged in" if err == 401 else "Admin access required"
        return jsonify({"error": msg}), err

    user = db.session.get(User, target_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    from app.models.chore import Chore, ChoreHistory
    ChoreHistory.query.filter_by(username=user.username).delete()
    Chore.query.filter_by(user_id=target_id).delete()
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "User deleted"})


# ── config management ─────────────────────────────────────────────────

@admin_bp.route("/api/admin/config", methods=["GET"])
def admin_get_config():
    """All AppConfig values with defaults + metadata."""
    user_id, admin_user, err = _require_admin()
    if err:
        msg = "Not logged in" if err == 401 else "Admin access required"
        return jsonify({"error": msg}), err

    config_data = {}
    for key, meta in CONFIG_META.items():
        config_data[key] = {
            "value": AppConfig.get(key, meta["default"]),
            "default": meta["default"],
            "label": meta["label"],
            "unit": meta["unit"],
        }
    return jsonify(config_data)


@admin_bp.route("/api/admin/config", methods=["POST"])
def admin_update_config():
    """Update one or more AppConfig values (batch)."""
    user_id, admin_user, err = _require_admin()
    if err:
        msg = "Not logged in" if err == 401 else "Admin access required"
        return jsonify({"error": msg}), err

    data = request.get_json(silent=True) or {}
    if not data:
        return jsonify({"error": "No config values provided"}), 400

    updated = {}
    for key, value in data.items():
        if key not in CONFIG_META:
            return jsonify({"error": f"Unknown config key: {key}"}), 400
        try:
            float(value)
        except (ValueError, TypeError):
            return jsonify({"error": f"Invalid value for {key}: must be numeric"}), 400
        AppConfig.set(key, str(value))
        updated[key] = str(value)

    db.session.commit()
    return jsonify({"updated": updated})


@admin_bp.route("/api/admin/config/pin", methods=["POST"])
def admin_change_pin():
    """Change the family PIN (bcrypt-hashed)."""
    user_id, admin_user, err = _require_admin()
    if err:
        msg = "Not logged in" if err == 401 else "Admin access required"
        return jsonify({"error": msg}), err

    data = request.get_json(silent=True) or {}
    new_pin = str(data.get("new_pin", "")).strip()
    if not new_pin:
        return jsonify({"error": "new_pin is required"}), 400

    hashed = bcrypt.hashpw(new_pin.encode(), bcrypt.gensalt()).decode()
    AppConfig.set("pin_hash", hashed)
    db.session.commit()
    return jsonify({"message": "PIN updated"})


# ── trusted IPs ───────────────────────────────────────────────────────

@admin_bp.route("/api/admin/trusted-ips", methods=["GET"])
def admin_list_ips():
    """All TrustedIP records."""
    user_id, admin_user, err = _require_admin()
    if err:
        msg = "Not logged in" if err == 401 else "Admin access required"
        return jsonify({"error": msg}), err

    ips = TrustedIP.query.order_by(TrustedIP.trusted_at.desc()).all()
    return jsonify({
        "trusted_ips": [
            {
                "id": ip.id,
                "ip_address": ip.ip_address,
                "trusted_at": ip.trusted_at.isoformat(),
                "last_seen": ip.last_seen.isoformat(),
            }
            for ip in ips
        ]
    })


@admin_bp.route("/api/admin/trusted-ips/<int:ip_id>", methods=["DELETE"])
def admin_revoke_ip(ip_id):
    """Revoke one trusted IP."""
    user_id, admin_user, err = _require_admin()
    if err:
        msg = "Not logged in" if err == 401 else "Admin access required"
        return jsonify({"error": msg}), err

    ip = db.session.get(TrustedIP, ip_id)
    if not ip:
        return jsonify({"error": "Trusted IP not found"}), 404

    db.session.delete(ip)
    db.session.commit()
    return jsonify({"message": "IP revoked"})


# ── digest ────────────────────────────────────────────────────────────

@admin_bp.route("/api/admin/digest/send", methods=["POST"])
def admin_send_digest():
    """Manually trigger the weekly family digest email."""
    user_id, admin_user, err = _require_admin()
    if err:
        msg = "Not logged in" if err == 401 else "Admin access required"
        return jsonify({"error": msg}), err

    from app.services.digest import send_weekly_digest
    sent_to = send_weekly_digest()
    return jsonify({"sent_to": sent_to, "count": len(sent_to)})

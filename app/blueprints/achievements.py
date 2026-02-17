"""Achievement routes — notifications, catalog, profile."""

from flask import Blueprint, jsonify, render_template, request, session

from app.extensions import db
from app.models.achievement import Achievement, UserAchievement
from app.models.mission import MissionAssignment
from app.models.user import User
from app.services.xp import get_level_info

achievements_bp = Blueprint("achievements", __name__)


# ── helpers ──────────────────────────────────────────────────────────

def _require_login():
    """Return (user_id, user) or (None, None)."""
    user_id = session.get("current_user_id")
    if not user_id:
        return None, None
    user = db.session.get(User, user_id)
    if not user:
        return None, None
    return user_id, user


# ── notification routes ──────────────────────────────────────────────

@achievements_bp.route("/api/achievements/notifications")
def get_notifications():
    """Get unnotified achievements for the current user, sorted gold-first."""
    user_id, user = _require_login()
    if not user:
        return jsonify({"error": "Not logged in"}), 401

    tier_order = {"gold": 0, "silver": 1, "bronze": 2}

    unnotified = UserAchievement.query.filter_by(
        user_id=user_id, notified=False,
    ).all()

    # Sort gold-first
    unnotified.sort(
        key=lambda ua: tier_order.get(ua.achievement.tier, 99)
    )

    return jsonify({
        "notifications": [ua.to_dict() for ua in unnotified],
    })


@achievements_bp.route("/api/achievements/notifications/dismiss", methods=["POST"])
def dismiss_notifications():
    """Mark achievement(s) as notified."""
    user_id, user = _require_login()
    if not user:
        return jsonify({"error": "Not logged in"}), 401

    data = request.get_json(silent=True) or {}
    achievement_ids = data.get("achievement_ids")

    if achievement_ids:
        # Dismiss specific achievements
        for ua in UserAchievement.query.filter(
            UserAchievement.user_id == user_id,
            UserAchievement.achievement_id.in_(achievement_ids),
            UserAchievement.notified == False,  # noqa: E712
        ).all():
            ua.notified = True
    else:
        # Dismiss all
        for ua in UserAchievement.query.filter_by(
            user_id=user_id, notified=False,
        ).all():
            ua.notified = True

    db.session.commit()
    return jsonify({"dismissed": True})


# ── catalog routes ───────────────────────────────────────────────────

@achievements_bp.route("/api/achievements/catalog")
def achievement_catalog():
    """All 14 achievements with locked/unlocked status for current user."""
    user_id, user = _require_login()
    if not user:
        return jsonify({"error": "Not logged in"}), 401

    achievements = Achievement.query.order_by(Achievement.display_order).all()
    unlocked_ids = {
        ua.achievement_id
        for ua in UserAchievement.query.filter_by(user_id=user_id).all()
    }

    catalog = []
    for a in achievements:
        entry = a.to_dict()
        entry["unlocked"] = a.id in unlocked_ids
        catalog.append(entry)

    return jsonify({"achievements": catalog})


@achievements_bp.route("/api/achievements/user")
def user_achievements():
    """Current user's unlocked achievements."""
    user_id, user = _require_login()
    if not user:
        return jsonify({"error": "Not logged in"}), 401

    unlocked = UserAchievement.query.filter_by(user_id=user_id).order_by(
        UserAchievement.unlocked_at.desc()
    ).all()

    return jsonify({
        "achievements": [ua.to_dict() for ua in unlocked],
    })


# ── profile routes ───────────────────────────────────────────────────

# Valid starter emoji icons
STARTER_ICONS = [
    "?", "\U0001f3ae", "\u26a1", "\U0001f680", "\U0001f3af",
    "\U0001f31f", "\U0001f525", "\U0001f48e", "\U0001f98a", "\U0001f409",
    "\U0001f3b8", "\U0001f3c0", "\U0001f3a8", "\U0001f308", "\U0001f981",
    "\U0001f43a", "\U0001f985", "\U0001f3aa", "\U0001f916", "\U0001f6f8",
]

# Level-unlocked icon IDs and their required level
LEVEL_ICONS = {
    "shield": 3, "crown": 3,
    "dragon_face": 5, "phoenix": 5,
    "thunder": 7, "flame": 7,
    "galaxy": 10, "infinity": 10,
}

# Mission-earned icon IDs
MISSION_ICONS = {"lightning_brain", "golden_music_note"}

# Icon ID → emoji mapping (for server-side rendering)
ICON_ID_TO_EMOJI = {
    "shield": "\U0001f6e1\ufe0f",
    "crown": "\U0001f451",
    "dragon_face": "\U0001f432",
    "phoenix": "\U0001f426\u200d\U0001f525",
    "thunder": "\u26a1",
    "flame": "\U0001f525",
    "galaxy": "\U0001f30c",
    "infinity": "\u267e\ufe0f",
    "lightning_brain": "\U0001f9e0\u26a1",
    "golden_music_note": "\U0001f3b5\u2728",
}

# Theme colour unlock levels
THEME_UNLOCK = {
    "cyan": 1, "blue": 1, "purple": 1,
    "lime": 3, "magenta": 3,
    "gold": 5,
    "red": 7,
}


@achievements_bp.route("/profile")
def profile_page():
    """Render the profile page."""
    return render_template("profile.html", active_nav="profile")


@achievements_bp.route("/api/profile")
def get_profile():
    """JSON profile data: user info, level, XP, streaks, icons, themes."""
    user_id, user = _require_login()
    if not user:
        return jsonify({"error": "Not logged in"}), 401

    level_info = get_level_info(user_id)

    # Recent 3 unlocked achievements
    recent_uas = UserAchievement.query.filter_by(user_id=user_id).order_by(
        UserAchievement.unlocked_at.desc()
    ).limit(3).all()
    recent = [ua.achievement.to_dict() for ua in recent_uas]

    total_unlocked = UserAchievement.query.filter_by(user_id=user_id).count()

    # Available icons: starter + level-unlocked + mission-earned
    available = list(STARTER_ICONS)
    for icon_id, req_level in LEVEL_ICONS.items():
        if user.level >= req_level:
            available.append(icon_id)
    # Check completed missions for mission icons
    completed = MissionAssignment.query.filter_by(
        user_id=user_id,
        state=MissionAssignment.STATE_COMPLETED,
    ).all()
    for ma in completed:
        if ma.mission.reward_icon in MISSION_ICONS:
            available.append(ma.mission.reward_icon)

    return jsonify({
        "username": user.username,
        "icon": user.icon,
        "level": level_info["level"],
        "level_name": level_info["level_name"],
        "xp": level_info["xp"],
        "next_level_xp": level_info["next_level_xp"],
        "progress_pct": level_info["progress_pct"],
        "streak_current": user.streak_current,
        "streak_best": user.streak_best,
        "fire_mode": user.fire_mode,
        "theme_color": user.theme_color,
        "achievements_unlocked": total_unlocked,
        "recent_achievements": recent,
        "available_icons": available,
    })


@achievements_bp.route("/api/profile/icon", methods=["POST"])
def update_icon():
    """Update the user's profile icon."""
    user_id, user = _require_login()
    if not user:
        return jsonify({"error": "Not logged in"}), 401

    data = request.get_json(silent=True) or {}
    icon = data.get("icon")
    if not icon:
        return jsonify({"error": "Icon is required"}), 400

    # Validate: starter emoji?
    if icon in STARTER_ICONS:
        user.icon = icon
        db.session.commit()
        return jsonify({"icon": icon})

    # Validate: level-unlocked icon?
    if icon in LEVEL_ICONS:
        if user.level < LEVEL_ICONS[icon]:
            return jsonify({
                "error": f"Requires level {LEVEL_ICONS[icon]}"
            }), 403
        user.icon = icon
        db.session.commit()
        return jsonify({"icon": icon})

    # Validate: mission-earned icon?
    if icon in MISSION_ICONS:
        completed = MissionAssignment.query.filter_by(
            user_id=user_id,
            state=MissionAssignment.STATE_COMPLETED,
        ).all()
        earned = {ma.mission.reward_icon for ma in completed}
        if icon not in earned:
            return jsonify({"error": "Complete the mission to unlock this icon"}), 403
        user.icon = icon
        db.session.commit()
        return jsonify({"icon": icon})

    return jsonify({"error": "Invalid icon"}), 400


@achievements_bp.route("/api/profile/theme", methods=["POST"])
def update_theme():
    """Update the user's theme colour."""
    user_id, user = _require_login()
    if not user:
        return jsonify({"error": "Not logged in"}), 401

    data = request.get_json(silent=True) or {}
    color = data.get("theme_color")
    if not color or color not in THEME_UNLOCK:
        return jsonify({"error": "Invalid theme colour"}), 400

    req_level = THEME_UNLOCK[color]
    if user.level < req_level:
        return jsonify({"error": f"Requires level {req_level}"}), 403

    user.theme_color = color
    db.session.commit()
    return jsonify({"theme_color": color})

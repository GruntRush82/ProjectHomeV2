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


# ── Icon data structures ──────────────────────────────────────────────

# 5 icons per level (levels 1-10)
ICON_LEVEL_GROUPS = {
    1:  ["star_basic", "rocket", "bolt", "controller", "robot"],
    2:  ["wolf", "eagle", "moon", "crystal_ball", "compass"],
    3:  ["shield", "crown", "sword", "tiger", "potion"],
    4:  ["knight", "falcon", "gem", "skull", "bull"],
    5:  ["dragon_face", "phoenix", "wizard", "lightning_charged", "gem_glowing"],
    6:  ["knight_hero", "samurai", "thunder_storm", "fire_hero", "fire_wolf"],
    7:  ["dragon_full", "flame_premium", "constellation", "thunderbolt", "vortex"],
    8:  ["firefly_swarm", "black_hole", "meteor", "phoenix_master", "electric_storm"],
    9:  ["dragon_ember", "spaceship", "cosmic_wolf", "supernova", "ice_titan"],
    10: ["galaxy", "infinity_ultimate", "titan_god", "void_dragon", "omega"],
}

# Flat map: icon_id -> required level (all 50 icons)
LEVEL_ICONS = {
    icon: lvl
    for lvl, icons in ICON_LEVEL_GROUPS.items()
    for icon in icons
}

# Rendering metadata per icon
ICON_METADATA = {
    # L1 — Rookie (no effects)
    "star_basic":        {"emoji": "\u2B50", "css_class": "", "lottie": False},
    "rocket":            {"emoji": "\U0001F680", "css_class": "", "lottie": False},
    "bolt":              {"emoji": "\u26A1", "css_class": "", "lottie": False},
    "controller":        {"emoji": "\U0001F3AE", "css_class": "", "lottie": False},
    "robot":             {"emoji": "\U0001F916", "css_class": "", "lottie": False},
    # L2 — Apprentice (faint glow)
    "wolf":              {"emoji": "\U0001F43A", "css_class": "icon-l2", "lottie": False},
    "eagle":             {"emoji": "\U0001F985", "css_class": "icon-l2", "lottie": False},
    "moon":              {"emoji": "\U0001F319", "css_class": "icon-l2", "lottie": False},
    "crystal_ball":      {"emoji": "\U0001F52E", "css_class": "icon-l2", "lottie": False},
    "compass":           {"emoji": "\U0001F9ED", "css_class": "icon-l2", "lottie": False},
    # L3 — Helper (visible accent ring)
    "shield":            {"emoji": "\U0001F6E1\uFE0F", "css_class": "icon-l3", "lottie": False},
    "crown":             {"emoji": "\U0001F451", "css_class": "icon-l3", "lottie": False},
    "sword":             {"emoji": "\u2694\uFE0F", "css_class": "icon-l3", "lottie": False},
    "tiger":             {"emoji": "\U0001F42F", "css_class": "icon-l3", "lottie": False},
    "potion":            {"emoji": "\U0001F9EA", "css_class": "icon-l3", "lottie": False},
    # L4 — Star (spinning conic-gradient border)
    "knight":            {"emoji": "\u265E", "css_class": "icon-l4", "lottie": False},
    "falcon":            {"emoji": "\U0001F426", "css_class": "icon-l4", "lottie": False},
    "gem":               {"emoji": "\U0001F48E", "css_class": "icon-l4", "lottie": False},
    "skull":             {"emoji": "\U0001F480", "css_class": "icon-l4", "lottie": False},
    "bull":              {"emoji": "\U0001F402", "css_class": "icon-l4", "lottie": False},
    # L5 — Champion (Lottie + pulsing multi-glow)
    "dragon_face":       {"emoji": "\U0001F409", "css_class": "icon-l5", "lottie": True,
                          "lottie_src": "/static/lottie/icon_dragon_face.json"},
    "phoenix":           {"emoji": "\U0001F426\u200D\U0001F525", "css_class": "icon-l5", "lottie": True,
                          "lottie_src": "/static/lottie/icon_phoenix.json"},
    "wizard":            {"emoji": "\U0001F9D9", "css_class": "icon-l5", "lottie": True,
                          "lottie_src": "/static/lottie/icon_wizard.json"},
    "lightning_charged": {"emoji": "\u26A1", "css_class": "icon-l5", "lottie": True,
                          "lottie_src": "/static/lottie/icon_lightning_charged.json"},
    "gem_glowing":       {"emoji": "\U0001F48E", "css_class": "icon-l5", "lottie": True,
                          "lottie_src": "/static/lottie/icon_gem_glowing.json"},
    # L6 — Hero (Lottie + shimmer sweep)
    "knight_hero":       {"emoji": "\u2694\uFE0F", "css_class": "icon-l6", "lottie": True,
                          "lottie_src": "/static/lottie/icon_knight_hero.json"},
    "samurai":           {"emoji": "\U0001F977", "css_class": "icon-l6", "lottie": True,
                          "lottie_src": "/static/lottie/icon_samurai.json"},
    "thunder_storm":     {"emoji": "\u26C8\uFE0F", "css_class": "icon-l6", "lottie": True,
                          "lottie_src": "/static/lottie/icon_thunder_storm.json"},
    "fire_hero":         {"emoji": "\U0001F525", "css_class": "icon-l6", "lottie": True,
                          "lottie_src": "/static/lottie/icon_fire_hero.json"},
    "fire_wolf":         {"emoji": "\U0001F43A", "css_class": "icon-l6", "lottie": True,
                          "lottie_src": "/static/lottie/icon_fire_wolf.json"},
    # L7 — Legend (Lottie + 3 orbiting CSS dots)
    "dragon_full":       {"emoji": "\U0001F432", "css_class": "icon-l7", "lottie": True,
                          "lottie_src": "/static/lottie/icon_dragon_full.json"},
    "flame_premium":     {"emoji": "\U0001F525", "css_class": "icon-l7", "lottie": True,
                          "lottie_src": "/static/lottie/icon_flame_premium.json"},
    "constellation":     {"emoji": "\u2728", "css_class": "icon-l7", "lottie": True,
                          "lottie_src": "/static/lottie/icon_constellation.json"},
    "thunderbolt":       {"emoji": "\u26A1", "css_class": "icon-l7", "lottie": True,
                          "lottie_src": "/static/lottie/icon_thunderbolt.json"},
    "vortex":            {"emoji": "\U0001F300", "css_class": "icon-l7", "lottie": True,
                          "lottie_src": "/static/lottie/icon_vortex.json"},
    # L8 — Master (Lottie + tsParticles)
    "firefly_swarm":     {"emoji": "\U0001FAB2", "css_class": "icon-l8", "lottie": True,
                          "lottie_src": "/static/lottie/icon_firefly_swarm.json",
                          "particle_config": "firefly_swarm"},
    "black_hole":        {"emoji": "\U0001F573\uFE0F", "css_class": "icon-l8", "lottie": True,
                          "lottie_src": "/static/lottie/icon_black_hole.json",
                          "particle_config": "black_hole"},
    "meteor":            {"emoji": "\u2604\uFE0F", "css_class": "icon-l8", "lottie": True,
                          "lottie_src": "/static/lottie/icon_meteor.json",
                          "particle_config": "meteor"},
    "phoenix_master":    {"emoji": "\U0001F426\u200D\U0001F525", "css_class": "icon-l8", "lottie": True,
                          "lottie_src": "/static/lottie/icon_phoenix_master.json",
                          "particle_config": "phoenix_master"},
    "electric_storm":    {"emoji": "\u26C8\uFE0F", "css_class": "icon-l8", "lottie": True,
                          "lottie_src": "/static/lottie/icon_electric_storm.json",
                          "particle_config": "electric_storm"},
    # L9 — Titan (Lottie + stronger particles + card halo)
    "dragon_ember":      {"emoji": "\U0001F409", "css_class": "icon-l9", "lottie": True,
                          "lottie_src": "/static/lottie/icon_dragon_ember.json",
                          "particle_config": "dragon_ember"},
    "spaceship":         {"emoji": "\U0001F680", "css_class": "icon-l9", "lottie": True,
                          "lottie_src": "/static/lottie/icon_spaceship.json",
                          "particle_config": "spaceship"},
    "cosmic_wolf":       {"emoji": "\U0001F43A", "css_class": "icon-l9", "lottie": True,
                          "lottie_src": "/static/lottie/icon_cosmic_wolf.json",
                          "particle_config": "cosmic_wolf"},
    "supernova":         {"emoji": "\U0001F4AB", "css_class": "icon-l9", "lottie": True,
                          "lottie_src": "/static/lottie/icon_supernova.json",
                          "particle_config": "supernova"},
    "ice_titan":         {"emoji": "\u2744\uFE0F", "css_class": "icon-l9", "lottie": True,
                          "lottie_src": "/static/lottie/icon_ice_titan.json",
                          "particle_config": "ice_titan"},
    # L10 — Ultimate (Lottie + full cinematic + particles)
    "galaxy":            {"emoji": "\U0001F30C", "css_class": "icon-l10", "lottie": True,
                          "lottie_src": "/static/lottie/icon_galaxy.json",
                          "particle_config": "galaxy"},
    "infinity_ultimate": {"emoji": "\u267E\uFE0F", "css_class": "icon-l10", "lottie": True,
                          "lottie_src": "/static/lottie/icon_infinity_ultimate.json",
                          "particle_config": "infinity_ultimate"},
    "titan_god":         {"emoji": "\u26A1", "css_class": "icon-l10", "lottie": True,
                          "lottie_src": "/static/lottie/icon_titan_god.json",
                          "particle_config": "titan_god"},
    "void_dragon":       {"emoji": "\U0001F409", "css_class": "icon-l10", "lottie": True,
                          "lottie_src": "/static/lottie/icon_void_dragon.json",
                          "particle_config": "void_dragon"},
    "omega":             {"emoji": "\U0001F52E", "css_class": "icon-l10", "lottie": True,
                          "lottie_src": "/static/lottie/icon_omega.json",
                          "particle_config": "omega"},
    # Mission icons (preserved)
    "lightning_brain":   {"emoji": "\U0001F9E0\u26A1", "css_class": "icon-mission-lightning", "lottie": False},
    "golden_music_note": {"emoji": "\U0001F3B5\u2728", "css_class": "icon-mission-music", "lottie": False},
}

# Backward-compat dicts consumed by __init__.py template filters
ICON_ID_TO_EMOJI = {k: v["emoji"] for k, v in ICON_METADATA.items()}
ICON_ID_TO_CSS   = {k: v["css_class"] for k, v in ICON_METADATA.items()}

# L1 icons are the starter set
STARTER_ICONS = ICON_LEVEL_GROUPS[1]

# Mission-earned icon IDs
MISSION_ICONS = {"lightning_brain", "golden_music_note"}


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

    # Build available_icons as list of dicts with full metadata
    user_level = user.level
    available = []
    for icon_id, req_level in sorted(LEVEL_ICONS.items(), key=lambda x: x[1]):
        meta = ICON_METADATA.get(icon_id, {})
        available.append({
            "id": icon_id,
            "emoji": meta.get("emoji", icon_id),
            "css_class": meta.get("css_class", ""),
            "lottie": meta.get("lottie", False),
            "lottie_src": meta.get("lottie_src", ""),
            "min_level": req_level,
            "locked": user_level < req_level,
        })
    # Check completed missions for mission icons
    completed = MissionAssignment.query.filter_by(
        user_id=user_id,
        state=MissionAssignment.STATE_COMPLETED,
    ).all()
    for ma in completed:
        if ma.mission.reward_icon in MISSION_ICONS:
            meta = ICON_METADATA.get(ma.mission.reward_icon, {})
            available.append({
                "id": ma.mission.reward_icon,
                "emoji": meta.get("emoji", ma.mission.reward_icon),
                "css_class": meta.get("css_class", ""),
                "lottie": False,
                "lottie_src": "",
                "min_level": 0,
                "locked": False,
            })

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

    # Validate: level-gated icon (L1-L10, all 50 icons)?
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

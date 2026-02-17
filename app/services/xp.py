"""XP grant and level-up logic.

Level thresholds (2x original spec) make max level ~5 months for a top
performer. XP only goes up — no take-backs on undo.
"""

from app.extensions import db
from app.models.user import User

# (level, cumulative_xp_required, name)
LEVEL_THRESHOLDS = [
    (1, 0, "Rookie"),
    (2, 200, "Apprentice"),
    (3, 500, "Helper"),
    (4, 1000, "Star"),
    (5, 1700, "Champion"),
    (6, 2600, "Hero"),
    (7, 3800, "Legend"),
    (8, 5400, "Master"),
    (9, 7400, "Titan"),
    (10, 10000, "Ultimate"),
]

MAX_LEVEL = LEVEL_THRESHOLDS[-1][0]


def get_level_for_xp(total_xp: int) -> tuple[int, str]:
    """Return (level, name) for the given total XP."""
    level, name = 1, "Rookie"
    for lvl, threshold, lvl_name in LEVEL_THRESHOLDS:
        if total_xp >= threshold:
            level, name = lvl, lvl_name
        else:
            break
    return level, name


def get_xp_for_next_level(current_level: int) -> int | None:
    """Return total XP needed for the next level, or None at max."""
    if current_level >= MAX_LEVEL:
        return None
    for lvl, threshold, _ in LEVEL_THRESHOLDS:
        if lvl == current_level + 1:
            return threshold
    return None


def grant_xp(user_id: int, amount: int, source: str) -> dict:
    """Grant XP to a user. XP only goes up. Commits to DB.

    Returns dict with xp_granted, total_xp, level, level_name,
    leveled_up, old_level, new_level.
    """
    user = db.session.get(User, user_id)
    if not user:
        return {"error": "User not found"}

    old_level = user.level
    old_xp = user.xp

    user.xp = old_xp + amount

    new_level, new_name = get_level_for_xp(user.xp)
    user.level = new_level

    db.session.commit()

    return {
        "xp_granted": amount,
        "total_xp": user.xp,
        "level": new_level,
        "level_name": new_name,
        "leveled_up": new_level > old_level,
        "old_level": old_level,
        "new_level": new_level,
    }


def get_level_info(user_id: int) -> dict:
    """Return level info for a user: level, name, xp, progress to next."""
    user = db.session.get(User, user_id)
    if not user:
        return {"error": "User not found"}

    level, name = get_level_for_xp(user.xp)
    next_threshold = get_xp_for_next_level(level)

    # Calculate progress percentage to next level
    if next_threshold is None:
        progress_pct = 100.0
        xp_into_level = 0
        xp_needed = 0
    else:
        # Find current level's threshold
        current_threshold = 0
        for lvl, thresh, _ in LEVEL_THRESHOLDS:
            if lvl == level:
                current_threshold = thresh
                break
        xp_into_level = user.xp - current_threshold
        xp_needed = next_threshold - current_threshold
        progress_pct = round((xp_into_level / xp_needed) * 100, 1) if xp_needed > 0 else 100.0

    return {
        "level": level,
        "level_name": name,
        "xp": user.xp,
        "xp_into_level": xp_into_level,
        "xp_needed": xp_needed,
        "next_level_xp": next_threshold,
        "progress_pct": progress_pct,
    }

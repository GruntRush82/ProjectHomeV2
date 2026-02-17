"""Tests for the XP service — level thresholds, granting, level-up."""

from app.services.xp import (
    LEVEL_THRESHOLDS,
    get_level_for_xp,
    get_xp_for_next_level,
    grant_xp,
    get_level_info,
)


class TestGetLevelForXP:
    def test_zero_xp_is_rookie(self):
        assert get_level_for_xp(0) == (1, "Rookie")

    def test_exact_threshold(self):
        assert get_level_for_xp(200) == (2, "Apprentice")
        assert get_level_for_xp(500) == (3, "Helper")
        assert get_level_for_xp(10000) == (10, "Ultimate")

    def test_between_thresholds(self):
        assert get_level_for_xp(199) == (1, "Rookie")
        assert get_level_for_xp(201) == (2, "Apprentice")
        assert get_level_for_xp(999) == (3, "Helper")

    def test_above_max(self):
        assert get_level_for_xp(99999) == (10, "Ultimate")


class TestGetXPForNextLevel:
    def test_level_1_next(self):
        assert get_xp_for_next_level(1) == 200

    def test_level_9_next(self):
        assert get_xp_for_next_level(9) == 10000

    def test_max_level_returns_none(self):
        assert get_xp_for_next_level(10) is None


class TestGrantXP:
    def test_grant_xp_basic(self, app, db, sample_users):
        kid = sample_users["kid1"]
        result = grant_xp(kid.id, 50, "test")
        assert result["xp_granted"] == 50
        assert result["total_xp"] == 50
        assert result["level"] == 1
        assert result["leveled_up"] is False

    def test_grant_xp_level_up(self, app, db, sample_users):
        kid = sample_users["kid1"]
        result = grant_xp(kid.id, 200, "test")
        assert result["leveled_up"] is True
        assert result["old_level"] == 1
        assert result["new_level"] == 2
        assert result["level_name"] == "Apprentice"

    def test_grant_xp_accumulates(self, app, db, sample_users):
        kid = sample_users["kid1"]
        grant_xp(kid.id, 100, "test1")
        result = grant_xp(kid.id, 150, "test2")
        assert result["total_xp"] == 250
        assert result["level"] == 2

    def test_grant_xp_invalid_user(self, app, db):
        result = grant_xp(9999, 50, "test")
        assert "error" in result


class TestGetLevelInfo:
    def test_level_info_new_user(self, app, db, sample_users):
        kid = sample_users["kid1"]
        info = get_level_info(kid.id)
        assert info["level"] == 1
        assert info["level_name"] == "Rookie"
        assert info["xp"] == 0
        assert info["next_level_xp"] == 200
        assert info["progress_pct"] == 0.0

    def test_level_info_mid_level(self, app, db, sample_users):
        kid = sample_users["kid1"]
        kid.xp = 100
        db.session.commit()
        info = get_level_info(kid.id)
        assert info["level"] == 1
        assert info["progress_pct"] == 50.0
        assert info["xp_into_level"] == 100
        assert info["xp_needed"] == 200

    def test_level_info_max_level(self, app, db, sample_users):
        kid = sample_users["kid1"]
        kid.xp = 10000
        kid.level = 10
        db.session.commit()
        info = get_level_info(kid.id)
        assert info["level"] == 10
        assert info["level_name"] == "Ultimate"
        assert info["progress_pct"] == 100.0
        assert info["next_level_xp"] is None

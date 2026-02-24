"""Tests for the weekly calendar API and page — Feature 1."""
from datetime import date, timedelta

import pytest


class TestWeeklyCalendarPage:
    def test_weekly_calendar_page_logged_out_returns_200(self, auth_client):
        resp = auth_client.get("/calendar")
        assert resp.status_code == 200
        assert b"calendarWeekApp" in resp.data

    def test_weekly_calendar_page_logged_in_returns_200(
        self, logged_in_client, sample_users
    ):
        client = logged_in_client(user_id=sample_users["kid1"].id)
        resp = client.get("/calendar")
        assert resp.status_code == 200
        assert b"calendarWeekApp" in resp.data

    def test_today_page_logged_in_returns_200(self, logged_in_client, sample_users):
        client = logged_in_client(user_id=sample_users["kid1"].id)
        resp = client.get("/today")
        assert resp.status_code == 200
        assert b"calendarApp" in resp.data


class TestWeekAPI:
    def _login(self, logged_in_client, sample_users):
        return logged_in_client(user_id=sample_users["kid1"].id)

    def test_week_api_returns_200(self, logged_in_client, sample_users):
        client = self._login(logged_in_client, sample_users)
        resp = client.get("/api/calendar/week")
        assert resp.status_code == 200

    def test_week_api_shape(self, logged_in_client, sample_users):
        client = self._login(logged_in_client, sample_users)
        resp = client.get("/api/calendar/week")
        data = resp.get_json()
        assert "week_start" in data
        assert "week_end" in data
        assert "days" in data
        assert len(data["days"]) == 7

    def test_week_api_day_fields(self, logged_in_client, sample_users):
        client = self._login(logged_in_client, sample_users)
        resp = client.get("/api/calendar/week")
        data = resp.get_json()
        for day in data["days"]:
            assert "date" in day
            assert "day_name" in day
            assert "is_today" in day
            assert "events" in day

    def test_week_api_starts_on_monday(self, logged_in_client, sample_users):
        client = self._login(logged_in_client, sample_users)
        resp = client.get("/api/calendar/week")
        data = resp.get_json()
        first_day = date.fromisoformat(data["days"][0]["date"])
        assert first_day.weekday() == 0  # Monday

    def test_week_api_with_explicit_start(self, logged_in_client, sample_users):
        client = self._login(logged_in_client, sample_users)
        monday = date(2025, 1, 6)  # A known Monday
        resp = client.get(f"/api/calendar/week?start={monday.isoformat()}")
        data = resp.get_json()
        assert data["week_start"] == monday.isoformat()
        assert date.fromisoformat(data["week_end"]) == monday + timedelta(days=6)

    def test_week_api_invalid_start_falls_back_to_current_week(
        self, logged_in_client, sample_users
    ):
        client = self._login(logged_in_client, sample_users)
        resp = client.get("/api/calendar/week?start=not-a-date")
        assert resp.status_code == 200
        data = resp.get_json()
        first_day = date.fromisoformat(data["days"][0]["date"])
        assert first_day.weekday() == 0

    def test_week_api_exactly_7_days(self, logged_in_client, sample_users):
        client = self._login(logged_in_client, sample_users)
        resp = client.get("/api/calendar/week")
        data = resp.get_json()
        dates = [d["date"] for d in data["days"]]
        parsed = [date.fromisoformat(d) for d in dates]
        assert len(parsed) == 7
        for i in range(1, 7):
            assert parsed[i] - parsed[i - 1] == timedelta(days=1)

    def test_week_api_is_today_flag(self, logged_in_client, sample_users):
        client = self._login(logged_in_client, sample_users)
        resp = client.get("/api/calendar/week")
        data = resp.get_json()
        today_str = date.today().isoformat()
        today_days = [d for d in data["days"] if d["date"] == today_str]
        if today_days:  # today is in current week
            assert today_days[0]["is_today"] is True
        other_days = [d for d in data["days"] if d["date"] != today_str]
        for d in other_days:
            assert d["is_today"] is False

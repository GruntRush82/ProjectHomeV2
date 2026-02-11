"""Smoke test to verify the test infrastructure works.

Run with: pytest tests/test_smoke.py -v
"""
import pytest


def test_pytest_runs():
    """Verify pytest itself is working."""
    assert True


def test_app_fixture_creates_app(app):
    """Verify the Flask app fixture works."""
    assert app is not None
    assert app.config["TESTING"] is True


def test_client_fixture_works(client):
    """Verify the test client can make requests."""
    response = client.get("/")
    # V2 login page returns 200
    assert response.status_code == 200


def test_sample_users_created(app, sample_users):
    """Verify sample users are created in the test DB."""
    assert sample_users["admin"].username == "TestDad"
    assert sample_users["kid1"].username == "TestKid1"
    assert sample_users["kid2"].username == "TestKid2"


def test_sample_chores_created(app, sample_chores, sample_users):
    """Verify sample chores are created and linked to users."""
    assert len(sample_chores) == 7  # 3 per kid + 1 rotating
    rotating = [c for c in sample_chores if c.rotation_type == "rotating"]
    assert len(rotating) == 1
    assert rotating[0].rotation_order == [
        sample_users["kid1"].username,
        sample_users["kid2"].username,
    ]

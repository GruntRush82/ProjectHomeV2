"""Shared test fixtures for Felker Family Hub V2.

Provides core fixtures used across all test layers (unit, api, e2e).
Each test gets a fresh in-memory SQLite database for isolation.
"""
import pytest

from app import create_app
from app.extensions import db as _db
from app.models.user import User
from app.models.chore import Chore


@pytest.fixture
def app():
    """Create a test Flask application with in-memory SQLite."""
    app = create_app(testing=True)
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def db(app):
    """Provide the SQLAlchemy database instance."""
    yield _db


@pytest.fixture
def client(app):
    """Flask test client — no auth, no session."""
    return app.test_client()


@pytest.fixture
def auth_client(client):
    """Test client that bypasses IP trust (simulates trusted IP).

    Phase 1+: This will set a trusted IP in the DB so the auth
    middleware lets requests through without a PIN.
    """
    # TODO Phase 1.4: Insert a TrustedIP row for 127.0.0.1
    return client


@pytest.fixture
def logged_in_client(app, auth_client):
    """Factory fixture: returns a client logged in as a specific user.

    Usage:
        def test_something(logged_in_client):
            client = logged_in_client(user_id=1)
            resp = client.get("/calendar")
            assert resp.status_code == 200
    """

    def _login(user_id):
        with auth_client.session_transaction() as sess:
            sess["current_user_id"] = user_id
        return auth_client

    return _login


@pytest.fixture
def admin_client(logged_in_client, sample_users):
    """Test client logged in as the admin user."""
    admin = sample_users["admin"]
    return logged_in_client(user_id=admin.id)


@pytest.fixture
def sample_users(app, db):
    """Create the standard test users.

    Returns a dict with keys: 'admin', 'kid1', 'kid2'
    """
    with app.app_context():
        admin = User(username="TestDad", is_admin=True)
        kid1 = User(username="TestKid1", allowance=15.0)
        kid2 = User(username="TestKid2", allowance=15.0)

        db.session.add_all([admin, kid1, kid2])
        db.session.commit()

        yield {"admin": admin, "kid1": kid1, "kid2": kid2}


@pytest.fixture
def sample_chores(app, db, sample_users):
    """Create standard test chores for the test kids.

    3 static chores per kid across Mon/Wed/Fri,
    plus 1 rotating chore shared between them.
    """
    with app.app_context():
        chores = []
        for kid_key in ["kid1", "kid2"]:
            kid = sample_users[kid_key]
            for day, desc in [
                ("Monday", f"{kid.username} - Monday chore"),
                ("Wednesday", f"{kid.username} - Wednesday chore"),
                ("Friday", f"{kid.username} - Friday chore"),
            ]:
                c = Chore(
                    description=desc,
                    user_id=kid.id,
                    day=day,
                    rotation_type="static",
                )
                chores.append(c)

        rotating = Chore(
            description="Rotating chore",
            user_id=sample_users["kid1"].id,
            day="Saturday",
            rotation_type="rotating",
            rotation_order=[
                sample_users["kid1"].username,
                sample_users["kid2"].username,
            ],
            base_user_id=sample_users["kid1"].id,
        )
        chores.append(rotating)

        db.session.add_all(chores)
        db.session.commit()

        yield chores

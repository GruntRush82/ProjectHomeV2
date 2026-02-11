"""API tests for session management — login, logout, switch user."""


class TestLogin:
    def test_login_page_shows_all_users(self, client, sample_users):
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"TestDad" in resp.data
        assert b"TestKid1" in resp.data
        assert b"TestKid2" in resp.data

    def test_login_page_shows_brand(self, client, sample_users):
        resp = client.get("/")
        assert b"Felker Family Hub" in resp.data

    def test_login_sets_session_user(self, client, sample_users):
        kid = sample_users["kid1"]
        resp = client.post("/session", data={"user_id": kid.id})
        assert resp.status_code == 302
        # Should redirect to chores home
        with client.session_transaction() as sess:
            assert sess["current_user_id"] == kid.id

    def test_login_with_invalid_user_redirects_to_login(self, client, sample_users):
        resp = client.post("/session", data={"user_id": 9999})
        assert resp.status_code == 302
        assert "/" in resp.headers["Location"]

    def test_login_shows_level_badges(self, client, sample_users):
        resp = client.get("/")
        assert b"Lv1" in resp.data
        assert b"Rookie" in resp.data


class TestLogout:
    def test_logout_clears_session(self, client, sample_users):
        kid = sample_users["kid1"]
        # Log in first
        client.post("/session", data={"user_id": kid.id})
        with client.session_transaction() as sess:
            assert "current_user_id" in sess

        # Log out
        resp = client.get("/session/logout")
        assert resp.status_code == 302
        with client.session_transaction() as sess:
            assert "current_user_id" not in sess


class TestSwitchUser:
    def test_switch_user_changes_session(self, client, sample_users):
        kid1 = sample_users["kid1"]
        kid2 = sample_users["kid2"]

        # Log in as kid1
        client.post("/session", data={"user_id": kid1.id})
        with client.session_transaction() as sess:
            assert sess["current_user_id"] == kid1.id

        # Log out then log in as kid2
        client.get("/session/logout")
        client.post("/session", data={"user_id": kid2.id})
        with client.session_transaction() as sess:
            assert sess["current_user_id"] == kid2.id


class TestSessionRedirect:
    def test_logged_in_user_redirected_from_login(self, client, sample_users):
        """If already logged in, visiting / redirects to chores."""
        kid = sample_users["kid1"]
        client.post("/session", data={"user_id": kid.id})
        resp = client.get("/")
        assert resp.status_code == 302

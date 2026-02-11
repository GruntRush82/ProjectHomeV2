"""API tests for user routes — V1 parity."""


class TestGetUsers:
    def test_empty_users(self, client):
        resp = client.get("/users")
        assert resp.status_code == 200
        assert resp.get_json() == []

    def test_returns_all_users(self, client, sample_users):
        resp = client.get("/users")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) == 3
        usernames = {u["username"] for u in data}
        assert usernames == {"TestDad", "TestKid1", "TestKid2"}


class TestCreateUser:
    def test_create_user(self, client):
        resp = client.post("/users", json={"username": "NewKid"})
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["username"] == "NewKid"
        assert "id" in data

    def test_missing_username_returns_400(self, client):
        resp = client.post("/users", json={})
        assert resp.status_code == 400

    def test_duplicate_username_returns_400(self, client, sample_users):
        resp = client.post("/users", json={"username": "TestDad"})
        assert resp.status_code == 400


class TestDeleteUser:
    def test_delete_user_and_chores(self, client, sample_users, sample_chores):
        kid1 = sample_users["kid1"]
        resp = client.delete(f"/users/{kid1.id}")
        assert resp.status_code == 200

        # User should be gone
        users = client.get("/users").get_json()
        ids = [u["id"] for u in users]
        assert kid1.id not in ids

        # Kid1's chores should be gone too
        chores = client.get("/chores").get_json()
        kid1_chores = [c for c in chores if c["user_id"] == kid1.id]
        assert len(kid1_chores) == 0

    def test_delete_nonexistent_returns_404(self, client):
        resp = client.delete("/users/9999")
        assert resp.status_code == 404

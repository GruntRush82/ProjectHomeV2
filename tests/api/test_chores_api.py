"""API tests for chore routes — V1 parity."""
import json
import pytest


class TestGetChores:
    def test_empty_chores(self, client):
        resp = client.get("/chores")
        assert resp.status_code == 200
        assert resp.get_json() == []

    def test_returns_all_chores(self, client, sample_chores):
        resp = client.get("/chores")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) == 7  # 3 per kid + 1 rotating

    def test_chore_has_expected_fields(self, client, sample_chores):
        resp = client.get("/chores")
        chore = resp.get_json()[0]
        expected_keys = {
            "id", "description", "completed", "user_id",
            "username", "day", "rotation_type", "rotation_order",
        }
        assert set(chore.keys()) == expected_keys


class TestAddChore:
    def test_create_static_chore(self, client, sample_users):
        kid = sample_users["kid1"]
        resp = client.post("/chores", json={
            "description": "Wash dishes",
            "user_id": kid.id,
            "day": "Monday",
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["description"] == "Wash dishes"
        assert data["username"] == kid.username
        assert data["rotation_type"] == "static"

    def test_create_rotating_chore(self, client, sample_users):
        k1, k2 = sample_users["kid1"], sample_users["kid2"]
        resp = client.post("/chores", json={
            "description": "Take out trash",
            "user_id": k1.id,
            "day": "Tuesday",
            "rotation_type": "rotating",
            "rotation_order": [k1.username, k2.username],
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["rotation_type"] == "rotating"
        assert data["rotation_order"] == [k1.username, k2.username]

    def test_missing_description_returns_400(self, client, sample_users):
        resp = client.post("/chores", json={
            "user_id": sample_users["kid1"].id,
            "day": "Monday",
        })
        assert resp.status_code == 400

    def test_invalid_day_returns_400(self, client, sample_users):
        resp = client.post("/chores", json={
            "description": "Bad day",
            "user_id": sample_users["kid1"].id,
            "day": "Funday",
        })
        assert resp.status_code == 400


class TestUpdateChore:
    def test_toggle_completed(self, client, sample_chores):
        chore_id = sample_chores[0].id
        resp = client.put(f"/chores/{chore_id}", json={"completed": True})
        assert resp.status_code == 200
        assert resp.get_json()["completed"] is True

    def test_update_description(self, client, sample_chores):
        chore_id = sample_chores[0].id
        resp = client.put(f"/chores/{chore_id}", json={
            "description": "Updated chore",
        })
        assert resp.status_code == 200
        assert resp.get_json()["description"] == "Updated chore"

    def test_update_nonexistent_returns_404(self, client):
        resp = client.put("/chores/9999", json={"completed": True})
        assert resp.status_code == 404


class TestDeleteChore:
    def test_delete_chore(self, client, sample_chores):
        chore_id = sample_chores[0].id
        resp = client.delete(f"/chores/{chore_id}")
        assert resp.status_code == 200

        # Confirm it's gone
        resp2 = client.get("/chores")
        ids = [c["id"] for c in resp2.get_json()]
        assert chore_id not in ids

    def test_delete_nonexistent_returns_404(self, client):
        resp = client.delete("/chores/9999")
        assert resp.status_code == 404


class TestMoveChore:
    def test_move_to_new_day(self, client, sample_chores):
        chore_id = sample_chores[0].id
        resp = client.put(f"/chores/{chore_id}/move", json={
            "day": "Sunday",
        })
        assert resp.status_code == 200
        assert resp.get_json()["day"] == "Sunday"

    def test_move_to_new_user(self, client, sample_chores, sample_users):
        chore_id = sample_chores[0].id
        new_user = sample_users["kid2"]
        resp = client.put(f"/chores/{chore_id}/move", json={
            "user_id": new_user.id,
        })
        assert resp.status_code == 200
        assert resp.get_json()["user_id"] == new_user.id

    def test_move_invalid_day_returns_400(self, client, sample_chores):
        chore_id = sample_chores[0].id
        resp = client.put(f"/chores/{chore_id}/move", json={
            "day": "Notaday",
        })
        assert resp.status_code == 400


class TestArchiveAndReset:
    def test_archive_creates_history(self, client, sample_chores):
        resp = client.post("/chores/archive")
        assert resp.status_code == 200

        archive = client.get("/archive").get_json()
        assert len(archive) == 7

    def test_archive_resets_completed(self, client, sample_chores):
        # Complete a chore first
        client.put(f"/chores/{sample_chores[0].id}", json={"completed": True})
        client.post("/chores/archive")

        chores = client.get("/chores").get_json()
        for c in chores:
            assert c["completed"] is False

    def test_clear_archive(self, client, sample_chores):
        client.post("/chores/archive")
        resp = client.delete("/chores/clear-archive")
        assert resp.status_code == 200

        archive = client.get("/archive").get_json()
        assert len(archive) == 0

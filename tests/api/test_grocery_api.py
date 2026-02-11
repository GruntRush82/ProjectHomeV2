"""API tests for grocery routes — V1 parity."""


class TestGetGrocery:
    def test_empty_list(self, client):
        resp = client.get("/grocery")
        assert resp.status_code == 200
        assert resp.get_json() == []


class TestAddGrocery:
    def test_add_item(self, client):
        resp = client.post("/grocery", json={
            "item_name": "Milk",
            "added_by": "TestKid1",
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["item_name"] == "Milk"
        assert data["added_by"] == "TestKid1"

    def test_missing_item_name_returns_400(self, client):
        resp = client.post("/grocery", json={"added_by": "TestKid1"})
        assert resp.status_code == 400

    def test_missing_added_by_returns_400(self, client):
        resp = client.post("/grocery", json={"item_name": "Eggs"})
        assert resp.status_code == 400


class TestDeleteGrocery:
    def test_delete_item(self, client):
        add_resp = client.post("/grocery", json={
            "item_name": "Bread",
            "added_by": "TestKid1",
        })
        item_id = add_resp.get_json()["id"]
        resp = client.delete(f"/grocery/{item_id}")
        assert resp.status_code == 200

        items = client.get("/grocery").get_json()
        assert len(items) == 0

    def test_delete_nonexistent_returns_404(self, client):
        resp = client.delete("/grocery/9999")
        assert resp.status_code == 404


class TestClearGrocery:
    def test_clear_all(self, client):
        client.post("/grocery", json={
            "item_name": "Apples",
            "added_by": "TestKid1",
        })
        client.post("/grocery", json={
            "item_name": "Bananas",
            "added_by": "TestKid2",
        })
        resp = client.delete("/grocery/clear")
        assert resp.status_code == 200

        items = client.get("/grocery").get_json()
        assert len(items) == 0

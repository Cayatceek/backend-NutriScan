from tests.conftest import auth_headers, internal_headers


def test_history_crud_and_favorites_filter(client):
    register_response = client.post(
        "/api/v1/auth/register",
        json={"email": "history@nutriscan.dev", "password": "supersecret123"},
    )
    access_token = register_response.json()["access_token"]

    product_response = client.post(
        "/api/v1/internal/products/upsert",
        headers=internal_headers(),
        json={
            "name": "History Product",
            "brand": "NutriScan",
            "barcode": "H-001",
            "ingredients_text": "milk",
            "ingredients": [{"id": "en:milk", "text": "milk"}],
        },
    )
    product_id = product_response.json()["id"]

    client.put(f"/api/v1/products/{product_id}/favorite", headers=auth_headers(access_token))

    create_history_response = client.post(
        "/api/v1/history/",
        headers=auth_headers(access_token),
        json={"product_id": product_id, "notes": "Scanned at home"},
    )
    assert create_history_response.status_code == 201
    history_item = create_history_response.json()
    assert history_item["product"]["is_favorite"] is True

    list_history_response = client.get("/api/v1/history/", headers=auth_headers(access_token))
    assert list_history_response.status_code == 200
    assert list_history_response.json()["total"] == 1

    favorites_history_response = client.get(
        "/api/v1/history/",
        headers=auth_headers(access_token),
        params={"filter": "favorites"},
    )
    assert favorites_history_response.status_code == 200
    assert favorites_history_response.json()["total"] == 1

    delete_history_response = client.delete(
        f"/api/v1/history/{history_item['id']}",
        headers=auth_headers(access_token),
    )
    assert delete_history_response.status_code == 200

    clear_history_response = client.delete("/api/v1/history/", headers=auth_headers(access_token))
    assert clear_history_response.status_code == 200


def test_history_requires_auth(client):
    response = client.get("/api/v1/history/")
    assert response.status_code == 401

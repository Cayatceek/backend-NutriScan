from tests.conftest import auth_headers, internal_headers


def test_public_products_are_read_only_and_internal_upsert_works(client):
    create_response = client.post(
        "/api/v1/products/",
        json={"name": "Should Not Work"},
    )
    assert create_response.status_code == 405

    internal_create_response = client.post(
        "/api/v1/internal/products/upsert",
        headers=internal_headers(),
        json={
            "name": "Greek Yogurt",
            "brand": "NutriScan",
            "barcode": "1234567890",
            "image_url": "https://example.com/product.png",
            "nutriscore_grade": "a",
            "ingredients_text": "milk, cultures",
            "ingredients": [{"id": "en:milk", "text": "milk"}],
            "additives_tags": ["en:e100"],
            "allergens": "milk",
            "nutriments": {
                "energy-kcal_100g": 120,
                "proteins_100g": 10,
                "fat_100g": 4,
                "carbohydrates_100g": 8,
            },
        },
    )
    assert internal_create_response.status_code == 200
    product = internal_create_response.json()
    assert product["barcode"] == "1234567890"
    assert product["nutriments"]["proteins_100g"] == 10

    get_response = client.get(f"/api/v1/products/{product['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["ingredients"][0]["text"] == "milk"

    barcode_response = client.get("/api/v1/products/barcode/1234567890")
    assert barcode_response.status_code == 200
    assert barcode_response.json()["product"]["product_name"] == "Greek Yogurt"


def test_product_list_and_favorites_flow(client):
    register_response = client.post(
        "/api/v1/auth/register",
        json={"email": "products@nutriscan.dev", "password": "supersecret123"},
    )
    access_token = register_response.json()["access_token"]

    for payload in [
        {"name": "Protein Yogurt", "brand": "NutriScan", "barcode": "P-001"},
        {"name": "Protein Shake", "brand": "NutriScan", "barcode": "P-002"},
        {"name": "Fruit Juice", "brand": "NutriScan", "barcode": "J-001"},
    ]:
        response = client.post(
            "/api/v1/internal/products/upsert",
            headers=internal_headers(),
            json=payload,
        )
        assert response.status_code == 200

    search_response = client.get("/api/v1/products/", params={"query": "Protein", "page": 1, "page_size": 2})
    assert search_response.status_code == 200
    payload = search_response.json()
    assert payload["total"] == 2
    assert len(payload["items"]) == 2

    first_product_id = payload["items"][0]["id"]
    favorite_response = client.put(
        f"/api/v1/products/{first_product_id}/favorite",
        headers=auth_headers(access_token),
    )
    assert favorite_response.status_code == 200

    favorites_response = client.get("/api/v1/products/favorites", headers=auth_headers(access_token))
    assert favorites_response.status_code == 200
    favorites_payload = favorites_response.json()
    assert favorites_payload["total"] == 1
    assert favorites_payload["items"][0]["is_favorite"] is True

    delete_favorite_response = client.delete(
        f"/api/v1/products/{first_product_id}/favorite",
        headers=auth_headers(access_token),
    )
    assert delete_favorite_response.status_code == 200

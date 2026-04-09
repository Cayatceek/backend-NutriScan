import httpx

from app.service import open_food_facts_service

from tests.conftest import internal_headers


def test_barcode_lookup_matches_expected_contract(client, monkeypatch):
    def fake_fetch_json(path, *, params=None, user_agent=None):
        if path.startswith("/api/v0/product/"):
            return {
                "code": "1234567890",
                "status": 1,
                "status_verbose": "product found",
                "product": {
                    "code": "1234567890",
                    "product_name": "Remote Yogurt",
                    "brands": "Remote Brand",
                    "ingredients_text": "milk",
                    "ingredients": [{"id": "en:milk", "text": "milk"}],
                    "nutriscore_grade": "b",
                    "nutriments": {"proteins_100g": 12.5},
                    "image_url": "https://example.com/image.png",
                    "image_front_url": "https://example.com/front.png",
                    "categories": "dairy",
                    "labels": "organic",
                    "additives_tags": ["en:e100"],
                    "allergens": "milk",
                },
            }
        raise AssertionError(f"Unexpected path: {path}")

    monkeypatch.setattr(open_food_facts_service, "_fetch_json", fake_fetch_json)

    response = client.get("/api/v0/product/1234567890.json")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == 1
    assert payload["product"]["product_name"] == "Remote Yogurt"
    assert payload["product"]["ingredients"][0]["text"] == "milk"


def test_search_falls_back_to_local_products_when_upstream_unavailable(client, monkeypatch):
    create_response = client.post(
        "/api/v1/internal/products/upsert",
        headers=internal_headers(),
        json={
            "name": "Local Protein Bar",
            "brand": "NutriScan",
            "barcode": "LOCAL-001",
            "ingredients_text": "protein blend, cocoa",
            "ingredients": [{"id": "en:protein", "text": "protein blend"}],
            "nutriscore_grade": "c",
            "nutriments": {"proteins_100g": 20.0},
        },
    )
    assert create_response.status_code == 200

    def failing_fetch_json(path, *, params=None, user_agent=None):
        raise httpx.ConnectError("offline")

    monkeypatch.setattr(open_food_facts_service, "_fetch_json", failing_fetch_json)

    response = client.get(
        "/cgi/search.pl",
        params={"search_terms": "Protein", "page": 1, "page_size": 20, "json": 1},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    assert payload["products"][0]["product_name"] == "Local Protein Bar"
    assert payload["products"][0]["nutriments"]["proteins_100g"] == 20.0

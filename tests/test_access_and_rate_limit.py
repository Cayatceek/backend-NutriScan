from app.core.rate_limit import rate_limit_storage

from tests.conftest import internal_headers


def test_internal_route_requires_api_key(client):
    response = client.post("/api/v1/internal/products/upsert", json={"name": "Blocked"})
    assert response.status_code == 401

    ok_response = client.post(
        "/api/v1/internal/products/upsert",
        headers=internal_headers(),
        json={"name": "Allowed", "barcode": "I-001"},
    )
    assert ok_response.status_code == 200


def test_auth_rate_limit_returns_429(client):
    if hasattr(rate_limit_storage, "reset"):
        rate_limit_storage.reset()

    responses = []
    for _ in range(10):
        responses.append(
            client.post(
                "/api/v1/auth/password-reset/request",
                json={"email": "rate-limit@nutriscan.dev"},
            )
        )
    overflow = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": "rate-limit@nutriscan.dev"},
    )

    if hasattr(rate_limit_storage, "reset"):
        rate_limit_storage.reset()

    for response in responses:
        assert response.status_code == 202
    assert overflow.status_code == 429

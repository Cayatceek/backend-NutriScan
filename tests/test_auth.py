from app.service import auth_service

from tests.conftest import auth_headers


def test_register_refresh_logout_and_me(client):
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "auth@nutriscan.dev",
            "password": "supersecret123",
            "full_name": "Auth Tester",
        },
    )

    assert register_response.status_code == 201
    payload = register_response.json()
    assert payload["token_type"] == "bearer"
    assert payload["user"]["email"] == "auth@nutriscan.dev"
    assert "refresh_token" in payload
    assert "access_expires_at" in payload
    assert "refresh_expires_at" in payload

    me_response = client.get("/api/v1/auth/me", headers=auth_headers(payload["access_token"]))
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "auth@nutriscan.dev"

    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": payload["refresh_token"]},
    )
    assert refresh_response.status_code == 200
    refreshed_payload = refresh_response.json()
    assert refreshed_payload["access_token"] != payload["access_token"]
    assert refreshed_payload["refresh_token"] != payload["refresh_token"]

    logout_response = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refreshed_payload["refresh_token"]},
    )
    assert logout_response.status_code == 200

    stale_me_response = client.get(
        "/api/v1/auth/me",
        headers=auth_headers(refreshed_payload["access_token"]),
    )
    assert stale_me_response.status_code == 401


def test_password_reset_flow_no_token_leakage(client, db_session):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "reset@nutriscan.dev",
            "password": "oldpassword123",
        },
    )

    existing_response = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": "reset@nutriscan.dev"},
    )
    missing_response = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": "missing@nutriscan.dev"},
    )

    assert existing_response.status_code == 202
    assert missing_response.status_code == 202
    assert existing_response.json() == missing_response.json()
    assert "reset_token" not in existing_response.json()

    raw_token = auth_service.create_password_reset_request(db_session, "reset@nutriscan.dev")
    assert raw_token is not None

    confirm_response = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": raw_token, "new_password": "newpassword123"},
    )
    assert confirm_response.status_code == 200

    old_login = client.post(
        "/api/v1/auth/login",
        json={"email": "reset@nutriscan.dev", "password": "oldpassword123"},
    )
    assert old_login.status_code == 401

    new_login = client.post(
        "/api/v1/auth/login",
        json={"email": "reset@nutriscan.dev", "password": "newpassword123"},
    )
    assert new_login.status_code == 200

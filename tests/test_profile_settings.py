from tests.conftest import auth_headers


def test_profile_and_settings_roundtrip(client):
    register_response = client.post(
        "/api/v1/auth/register",
        json={"email": "profile@nutriscan.dev", "password": "supersecret123"},
    )
    access_token = register_response.json()["access_token"]

    profile_response = client.get("/api/v1/profile", headers=auth_headers(access_token))
    assert profile_response.status_code == 200
    assert profile_response.json()["email"] == "profile@nutriscan.dev"

    patch_profile_response = client.patch(
        "/api/v1/profile",
        headers=auth_headers(access_token),
        json={"full_name": "Nutri Profile"},
    )
    assert patch_profile_response.status_code == 200
    assert patch_profile_response.json()["full_name"] == "Nutri Profile"

    settings_response = client.get("/api/v1/settings", headers=auth_headers(access_token))
    assert settings_response.status_code == 200
    assert settings_response.json()["language"] == "uz"

    update_settings_response = client.put(
        "/api/v1/settings",
        headers=auth_headers(access_token),
        json={
            "language": "ru",
            "is_language_manually_selected": True,
            "theme": "dark",
            "halal_mode_enabled": True,
            "healthy_mode_enabled": True,
            "vegan_mode_enabled": False,
            "notifications_enabled": False,
            "selected_allergens": ["MILK", "GLUTEN"],
            "onboarding_completed": True,
            "onboarding_shown": True,
        },
    )
    assert update_settings_response.status_code == 200
    payload = update_settings_response.json()
    assert payload["language"] == "ru"
    assert payload["selected_allergens"] == ["MILK", "GLUTEN"]

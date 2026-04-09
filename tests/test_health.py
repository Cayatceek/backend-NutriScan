def test_health_routes_are_available(client):
    live_response = client.get("/api/v1/health/live")
    ready_response = client.get("/api/v1/health/ready")
    alias_response = client.get("/api/v1/health")

    assert live_response.status_code == 200
    assert ready_response.status_code == 200
    assert alias_response.status_code == 200
    assert ready_response.json()["status"] == "ok"

def test_health_returns_200(client):
    """GET /health responds with HTTP 200."""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_status_ok(client):
    """Response body contains status: ok."""
    response = client.get("/health")
    assert response.json()["status"] == "ok"


def test_health_python_version_present(client):
    """Response body contains a non-empty python_version string."""
    response = client.get("/health")
    data = response.json()
    assert "python_version" in data
    assert isinstance(data["python_version"], str)
    assert len(data["python_version"]) > 0


def test_health_log_level_matches_config(client, settings_override):
    """Response log_level matches the configured value."""
    response = client.get("/health")
    data = response.json()
    assert "log_level" in data
    assert data["log_level"] == settings_override["LOG_LEVEL"]


def test_health_heartbeat_timeout_is_integer(client, settings_override):
    """Response heartbeat_timeout_seconds is an integer matching configured value."""
    response = client.get("/health")
    data = response.json()
    assert "heartbeat_timeout_seconds" in data
    assert isinstance(data["heartbeat_timeout_seconds"], int)
    assert data["heartbeat_timeout_seconds"] == int(settings_override["HEARTBEAT_TIMEOUT_SECONDS"])

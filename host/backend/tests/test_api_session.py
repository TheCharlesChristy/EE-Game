"""
Integration tests for the session lifecycle REST API (EP-02).
SRS reference: FR-001–FR-010, EP-02-US-01, EP-02-US-02.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    import ee_game_backend.config as cfg

    cfg._settings = None
    from ee_game_backend.main import create_app

    app = create_app()
    with TestClient(app) as c:
        yield c
    cfg._settings = None


# ---------------------------------------------------------------------------
# POST /api/sessions — create
# ---------------------------------------------------------------------------


def test_create_session_returns_201(client):
    response = client.post("/api/sessions")
    assert response.status_code == 201
    body = response.json()
    assert "session_id" in body
    assert body["status"] == "active"
    assert "created_at" in body


def test_create_session_conflict_when_already_exists(client):
    client.post("/api/sessions")
    response = client.post("/api/sessions")
    assert response.status_code == 409


# ---------------------------------------------------------------------------
# GET /api/sessions/current
# ---------------------------------------------------------------------------


def test_get_current_returns_empty_when_no_session(client):
    response = client.get("/api/sessions/current")
    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] is None
    assert body["status"] is None
    assert body["player_list"] == []
    assert body["standings"] == []


def test_get_current_returns_session_after_create(client):
    create_resp = client.post("/api/sessions")
    session_id = create_resp.json()["session_id"]

    response = client.get("/api/sessions/current")
    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] == session_id
    assert body["status"] == "active"
    assert body["player_list"] == []
    assert body["standings"] == []


# ---------------------------------------------------------------------------
# POST /api/sessions/current/save
# ---------------------------------------------------------------------------


def test_save_session_returns_200_with_unchanged_status(client):
    client.post("/api/sessions")
    response = client.post("/api/sessions/current/save")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "active"
    assert "session_id" in body


def test_save_session_returns_409_when_no_session(client):
    response = client.post("/api/sessions/current/save")
    assert response.status_code == 409


# ---------------------------------------------------------------------------
# POST /api/sessions/current/pause
# ---------------------------------------------------------------------------


def test_pause_session_returns_200_with_status_paused(client):
    client.post("/api/sessions")
    response = client.post("/api/sessions/current/pause")
    assert response.status_code == 200
    assert response.json()["status"] == "paused"


def test_pause_session_returns_409_when_not_active(client):
    # No session — not active
    response = client.post("/api/sessions/current/pause")
    assert response.status_code == 409


def test_pause_session_returns_409_when_already_paused(client):
    client.post("/api/sessions")
    client.post("/api/sessions/current/pause")
    response = client.post("/api/sessions/current/pause")
    assert response.status_code == 409


# ---------------------------------------------------------------------------
# POST /api/sessions/resume
# ---------------------------------------------------------------------------


def test_resume_session_returns_200_after_pause(client):
    client.post("/api/sessions")
    client.post("/api/sessions/current/pause")
    response = client.post("/api/sessions/resume")
    assert response.status_code == 200
    assert response.json()["status"] == "active"


def test_resume_session_returns_409_when_already_active(client):
    client.post("/api/sessions")
    response = client.post("/api/sessions/resume")
    assert response.status_code == 409


def test_resume_session_returns_404_when_no_resumable_session(client):
    response = client.post("/api/sessions/resume")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/sessions/current/finish
# ---------------------------------------------------------------------------


def test_finish_session_returns_400_when_body_absent(client):
    client.post("/api/sessions")
    response = client.post("/api/sessions/current/finish", json={})
    assert response.status_code == 400


def test_finish_session_returns_400_when_confirmed_false(client):
    client.post("/api/sessions")
    response = client.post("/api/sessions/current/finish", json={"confirmed": False})
    assert response.status_code == 400


def test_finish_session_returns_200_with_archive_id_when_confirmed(client):
    create_resp = client.post("/api/sessions")
    session_id = create_resp.json()["session_id"]

    response = client.post("/api/sessions/current/finish", json={"confirmed": True})
    assert response.status_code == 200
    body = response.json()
    assert "archive_id" in body
    assert body["session_id"] == session_id
    assert "finished_at" in body
    assert body["message"] == "Session finished and archived successfully."


def test_finish_session_returns_409_when_no_session_and_confirmed(client):
    response = client.post("/api/sessions/current/finish", json={"confirmed": True})
    assert response.status_code == 409


# ---------------------------------------------------------------------------
# Immutability: save after finish returns 409
# ---------------------------------------------------------------------------


def test_save_after_finish_returns_409(client):
    client.post("/api/sessions")
    client.post("/api/sessions/current/finish", json={"confirmed": True})
    response = client.post("/api/sessions/current/save")
    assert response.status_code == 409

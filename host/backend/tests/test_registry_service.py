"""
Unit tests for registry.service — PlayerRegistryService.
EP-03, US-01 and US-02 acceptance criteria.
"""

import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from ee_game_backend.registry.exceptions import (
    CapacityError,
    NoActiveSessionError,
    PlayerNotFoundError,
    ValidationError,
)
from ee_game_backend.registry.models import Player
from ee_game_backend.registry.service import PlayerRegistryService
from ee_game_backend.session.models import Session, SessionStatus


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_session(
    status: SessionStatus = SessionStatus.ACTIVE,
    players: list[dict] | None = None,
) -> Session:
    """Create a minimal Session for testing."""
    session = Session.new()
    session.status = status
    if players is not None:
        session.players = players
    return session


def _make_player_dict(
    player_id: str = "pid-001",
    device_id: str = "dev-001",
    username: str = "BraveFox",
    colour: str = "#E6194B",
    connection_state: str = "connected",
) -> dict:
    now = datetime.datetime.utcnow().isoformat()
    return {
        "player_id": player_id,
        "device_id": device_id,
        "username": username,
        "colour": colour,
        "connection_state": connection_state,
        "last_seen_at": now,
        "registered_at": now,
        "firmware_version": "1.0.0",
        "board_target": "esp32c3",
    }


def _make_service(
    session: Session | None = None,
) -> tuple[PlayerRegistryService, MagicMock, AsyncMock, AsyncMock]:
    """
    Build a PlayerRegistryService with mocked collaborators.

    Returns (service, session_service_mock, repo_mock, manager_mock).
    """
    session_service = MagicMock()
    session_service.current_session = session

    repo = AsyncMock()
    repo.upsert_session = AsyncMock(return_value=None)
    repo.insert_audit_event = AsyncMock(return_value=None)

    manager = AsyncMock()
    manager.broadcast_to_frontends = AsyncMock(return_value=None)

    service = PlayerRegistryService(
        session_service=session_service,
        repo=repo,
        manager=manager,
    )
    return service, session_service, repo, manager


# ---------------------------------------------------------------------------
# register_device
# ---------------------------------------------------------------------------


class TestRegisterDeviceNewDevice:
    async def test_creates_player_with_username_and_colour(self):
        session = _make_session()
        service, _, repo, manager = _make_service(session)

        player = await service.register_device("dev-001", "1.0.0", "esp32c3")

        assert isinstance(player, Player)
        assert player.device_id == "dev-001"
        assert player.firmware_version == "1.0.0"
        assert player.board_target == "esp32c3"
        assert player.connection_state == "connected"
        assert len(player.username) > 0
        assert player.colour.startswith("#")

    async def test_persists_and_broadcasts(self):
        session = _make_session()
        service, _, repo, manager = _make_service(session)

        await service.register_device("dev-001", "1.0.0", "esp32c3")

        repo.upsert_session.assert_called()
        manager.broadcast_to_frontends.assert_called()

    async def test_emits_audit_event(self):
        session = _make_session()
        service, _, repo, _ = _make_service(session)

        await service.register_device("dev-001", "1.0.0", "esp32c3")

        repo.insert_audit_event.assert_called()
        event = repo.insert_audit_event.call_args[0][0]
        assert event.action_type == "device_registered"

    async def test_player_appended_to_session_players(self):
        session = _make_session()
        service, _, _, _ = _make_service(session)

        await service.register_device("dev-001", "1.0.0", "esp32c3")

        assert len(session.players) == 1
        assert session.players[0]["device_id"] == "dev-001"

    async def test_multiple_devices_get_unique_colours_and_usernames(self):
        session = _make_session()
        service, _, _, _ = _make_service(session)

        p1 = await service.register_device("dev-001", "1.0.0", "esp32c3")
        p2 = await service.register_device("dev-002", "1.0.0", "esp32c3")

        assert p1.colour != p2.colour
        assert p1.username != p2.username


class TestRegisterDeviceReconnect:
    async def test_restores_mapping_for_known_device(self):
        existing = _make_player_dict(connection_state="disconnected")
        session = _make_session(players=[existing])
        service, _, _, _ = _make_service(session)

        player = await service.register_device("dev-001", "2.0.0", "esp32c3")

        assert player.player_id == "pid-001"
        assert player.connection_state == "connected"

    async def test_updates_firmware_on_reconnect(self):
        existing = _make_player_dict(connection_state="disconnected")
        session = _make_session(players=[existing])
        service, _, _, _ = _make_service(session)

        player = await service.register_device("dev-001", "9.9.9", "new-board")

        assert player.firmware_version == "9.9.9"
        assert player.board_target == "new-board"

    async def test_emits_reconnected_audit_event(self):
        existing = _make_player_dict(connection_state="disconnected")
        session = _make_session(players=[existing])
        service, _, repo, _ = _make_service(session)

        await service.register_device("dev-001", "1.0.0", "esp32c3")

        event = repo.insert_audit_event.call_args[0][0]
        assert event.action_type == "device_reconnected"

    async def test_warns_on_conflict_still_connected(self, caplog):
        existing = _make_player_dict(connection_state="connected")
        session = _make_session(players=[existing])
        service, _, _, _ = _make_service(session)

        import logging

        with caplog.at_level(logging.WARNING, logger="ee_game_backend.registry.service"):
            await service.register_device("dev-001", "1.0.0", "esp32c3")

        assert any("RECONNECT_CONFLICT" in r.message for r in caplog.records)

    async def test_does_not_create_duplicate_player(self):
        existing = _make_player_dict(connection_state="disconnected")
        session = _make_session(players=[existing])
        service, _, _, _ = _make_service(session)

        await service.register_device("dev-001", "1.0.0", "esp32c3")

        assert len(session.players) == 1


class TestRegisterDeviceErrors:
    async def test_raises_no_active_session_when_none(self):
        service, _, _, _ = _make_service(session=None)

        with pytest.raises(NoActiveSessionError):
            await service.register_device("dev-001", "1.0.0", "esp32c3")

    async def test_raises_no_active_session_when_finished(self):
        session = _make_session(status=SessionStatus.FINISHED)
        service, _, _, _ = _make_service(session)

        with pytest.raises(NoActiveSessionError):
            await service.register_device("dev-001", "1.0.0", "esp32c3")

    async def test_raises_capacity_error_at_20_players(self):
        players = [
            _make_player_dict(
                player_id=f"pid-{i:03d}",
                device_id=f"dev-{i:03d}",
                username=f"Player{i}",
                colour=f"#{'%06X' % i}",
            )
            for i in range(20)
        ]
        session = _make_session(players=players)
        service, _, _, _ = _make_service(session)

        with pytest.raises(CapacityError):
            await service.register_device("dev-999", "1.0.0", "esp32c3")


# ---------------------------------------------------------------------------
# handle_heartbeat
# ---------------------------------------------------------------------------


class TestHandleHeartbeat:
    async def test_updates_last_seen_at_for_known_device(self):
        existing = _make_player_dict(connection_state="stale")
        session = _make_session(players=[existing])
        service, ss, repo, _ = _make_service(session)
        ss.current_session = session

        before = datetime.datetime.utcnow()
        await service.handle_heartbeat("dev-001")

        repo.upsert_session.assert_called()
        updated = Player.from_dict(session.players[0])
        assert updated.connection_state == "connected"
        assert updated.last_seen_at >= before

    async def test_noop_for_unknown_device(self):
        session = _make_session()
        service, ss, repo, manager = _make_service(session)
        ss.current_session = session

        await service.handle_heartbeat("dev-unknown")

        repo.upsert_session.assert_not_called()
        manager.broadcast_to_frontends.assert_not_called()

    async def test_noop_when_no_active_session(self):
        service, ss, repo, _ = _make_service(session=None)
        ss.current_session = None

        await service.handle_heartbeat("dev-001")

        repo.upsert_session.assert_not_called()

    async def test_never_raises(self):
        service, ss, _, _ = _make_service(session=None)
        ss.current_session = MagicMock(side_effect=RuntimeError("boom"))

        # Must not propagate.
        await service.handle_heartbeat("dev-001")


# ---------------------------------------------------------------------------
# handle_disconnect
# ---------------------------------------------------------------------------


class TestHandleDisconnect:
    async def test_sets_state_disconnected(self):
        existing = _make_player_dict(connection_state="connected")
        session = _make_session(players=[existing])
        service, ss, repo, _ = _make_service(session)
        ss.current_session = session

        await service.handle_disconnect("dev-001")

        updated = Player.from_dict(session.players[0])
        assert updated.connection_state == "disconnected"

    async def test_persists_and_broadcasts(self):
        existing = _make_player_dict(connection_state="connected")
        session = _make_session(players=[existing])
        service, ss, repo, manager = _make_service(session)
        ss.current_session = session

        await service.handle_disconnect("dev-001")

        repo.upsert_session.assert_called()
        manager.broadcast_to_frontends.assert_called()

    async def test_emits_disconnected_audit_event(self):
        existing = _make_player_dict(connection_state="connected")
        session = _make_session(players=[existing])
        service, ss, repo, _ = _make_service(session)
        ss.current_session = session

        await service.handle_disconnect("dev-001")

        event = repo.insert_audit_event.call_args[0][0]
        assert event.action_type == "device_disconnected"

    async def test_noop_for_unknown_device(self):
        session = _make_session()
        service, ss, repo, _ = _make_service(session)
        ss.current_session = session

        await service.handle_disconnect("dev-unknown")

        repo.upsert_session.assert_not_called()


# ---------------------------------------------------------------------------
# handle_stale
# ---------------------------------------------------------------------------


class TestHandleStale:
    async def test_sets_state_stale_for_listed_devices(self):
        p1 = _make_player_dict(
            player_id="pid-001", device_id="dev-001", connection_state="connected"
        )
        p2 = _make_player_dict(
            player_id="pid-002", device_id="dev-002", connection_state="connected"
        )
        session = _make_session(players=[p1, p2])
        service, ss, repo, _ = _make_service(session)
        ss.current_session = session

        await service.handle_stale(["dev-001"])

        updated1 = Player.from_dict(session.players[0])
        updated2 = Player.from_dict(session.players[1])
        assert updated1.connection_state == "stale"
        assert updated2.connection_state == "connected"

    async def test_persists_and_broadcasts_affected_devices(self):
        p1 = _make_player_dict(connection_state="connected")
        session = _make_session(players=[p1])
        service, ss, repo, manager = _make_service(session)
        ss.current_session = session

        await service.handle_stale(["dev-001"])

        repo.upsert_session.assert_called()
        manager.broadcast_to_frontends.assert_called()

    async def test_emits_stale_audit_event(self):
        p1 = _make_player_dict(connection_state="connected")
        session = _make_session(players=[p1])
        service, ss, repo, _ = _make_service(session)
        ss.current_session = session

        await service.handle_stale(["dev-001"])

        event = repo.insert_audit_event.call_args[0][0]
        assert event.action_type == "devices_stale"

    async def test_noop_when_no_affected_players(self):
        session = _make_session()
        service, ss, repo, _ = _make_service(session)
        ss.current_session = session

        await service.handle_stale(["dev-unknown"])

        repo.upsert_session.assert_not_called()


# ---------------------------------------------------------------------------
# update_player_username
# ---------------------------------------------------------------------------


class TestUpdatePlayerUsername:
    async def test_updates_username_and_persists(self):
        existing = _make_player_dict()
        session = _make_session(players=[existing])
        service, _, repo, _ = _make_service(session)

        player = await service.update_player_username("pid-001", "CoolOwl")

        assert player.username == "CoolOwl"
        repo.upsert_session.assert_called()

    async def test_broadcasts_after_update(self):
        existing = _make_player_dict()
        session = _make_session(players=[existing])
        service, _, _, manager = _make_service(session)

        await service.update_player_username("pid-001", "NewName")

        manager.broadcast_to_frontends.assert_called()

    async def test_emits_username_changed_audit_event(self):
        existing = _make_player_dict()
        session = _make_session(players=[existing])
        service, _, repo, _ = _make_service(session)

        await service.update_player_username("pid-001", "NewName")

        event = repo.insert_audit_event.call_args[0][0]
        assert event.action_type == "player_username_changed"
        assert event.actor_type == "host"

    async def test_raises_player_not_found(self):
        session = _make_session()
        service, _, _, _ = _make_service(session)

        with pytest.raises(PlayerNotFoundError):
            await service.update_player_username("no-such-id", "NewName")

    async def test_raises_no_active_session(self):
        service, _, _, _ = _make_service(session=None)

        with pytest.raises(NoActiveSessionError):
            await service.update_player_username("pid-001", "NewName")

    async def test_rejects_empty_username(self):
        existing = _make_player_dict()
        session = _make_session(players=[existing])
        service, _, _, _ = _make_service(session)

        with pytest.raises(ValidationError):
            await service.update_player_username("pid-001", "")

    async def test_rejects_whitespace_only_username(self):
        existing = _make_player_dict()
        session = _make_session(players=[existing])
        service, _, _, _ = _make_service(session)

        with pytest.raises(ValidationError):
            await service.update_player_username("pid-001", "   ")

    async def test_rejects_too_long_username(self):
        existing = _make_player_dict()
        session = _make_session(players=[existing])
        service, _, _, _ = _make_service(session)

        with pytest.raises(ValidationError):
            await service.update_player_username("pid-001", "A" * 21)

    async def test_accepts_max_length_username(self):
        existing = _make_player_dict()
        session = _make_session(players=[existing])
        service, _, _, _ = _make_service(session)

        player = await service.update_player_username("pid-001", "A" * 20)
        assert len(player.username) == 20

    async def test_rejects_invalid_characters(self):
        existing = _make_player_dict()
        session = _make_session(players=[existing])
        service, _, _, _ = _make_service(session)

        with pytest.raises(ValidationError):
            await service.update_player_username("pid-001", "Name@!")

    async def test_accepts_allowed_special_chars(self):
        existing = _make_player_dict()
        session = _make_session(players=[existing])
        service, _, _, _ = _make_service(session)

        # Underscores, spaces, and hyphens are allowed.
        player = await service.update_player_username("pid-001", "Cool_Name-1")
        assert player.username == "Cool_Name-1"


# ---------------------------------------------------------------------------
# update_player_colour
# ---------------------------------------------------------------------------


class TestUpdatePlayerColour:
    async def test_updates_colour_and_persists(self):
        existing = _make_player_dict(colour="#E6194B")
        session = _make_session(players=[existing])
        service, _, repo, _ = _make_service(session)

        player = await service.update_player_colour("pid-001", "#3CB44B")

        assert player.colour == "#3CB44B"
        repo.upsert_session.assert_called()

    async def test_broadcasts_after_update(self):
        existing = _make_player_dict(colour="#E6194B")
        session = _make_session(players=[existing])
        service, _, _, manager = _make_service(session)

        await service.update_player_colour("pid-001", "#3CB44B")

        manager.broadcast_to_frontends.assert_called()

    async def test_emits_colour_changed_audit_event(self):
        existing = _make_player_dict(colour="#E6194B")
        session = _make_session(players=[existing])
        service, _, repo, _ = _make_service(session)

        await service.update_player_colour("pid-001", "#3CB44B")

        event = repo.insert_audit_event.call_args[0][0]
        assert event.action_type == "player_colour_changed"
        assert event.actor_type == "host"

    async def test_normalizes_colour_to_uppercase(self):
        existing = _make_player_dict(colour="#E6194B")
        session = _make_session(players=[existing])
        service, _, _, _ = _make_service(session)

        player = await service.update_player_colour("pid-001", "#3cb44b")

        assert player.colour == "#3CB44B"

    async def test_raises_no_active_session(self):
        service, _, _, _ = _make_service(session=None)

        with pytest.raises(NoActiveSessionError):
            await service.update_player_colour("pid-001", "#3CB44B")

    async def test_raises_player_not_found(self):
        session = _make_session()
        service, _, _, _ = _make_service(session)

        with pytest.raises(PlayerNotFoundError):
            await service.update_player_colour("no-such-id", "#3CB44B")

    async def test_rejects_colour_not_in_palette(self):
        existing = _make_player_dict()
        session = _make_session(players=[existing])
        service, _, _, _ = _make_service(session)

        with pytest.raises(ValidationError):
            await service.update_player_colour("pid-001", "#FFFFFF")

    async def test_rejects_colour_already_used_by_another_player(self):
        p1 = _make_player_dict(player_id="pid-001", device_id="dev-001", colour="#E6194B")
        p2 = _make_player_dict(player_id="pid-002", device_id="dev-002", colour="#3CB44B")
        session = _make_session(players=[p1, p2])
        service, _, _, _ = _make_service(session)

        # pid-001 tries to steal pid-002's colour.
        with pytest.raises(ValidationError):
            await service.update_player_colour("pid-001", "#3CB44B")

    async def test_allows_same_player_to_keep_own_colour(self):
        existing = _make_player_dict(colour="#E6194B")
        session = _make_session(players=[existing])
        service, _, _, _ = _make_service(session)

        # Assigning the same colour to the same player must succeed.
        player = await service.update_player_colour("pid-001", "#E6194B")
        assert player.colour == "#E6194B"


# ---------------------------------------------------------------------------
# get_all_players / get_player_by_device_id
# ---------------------------------------------------------------------------


class TestGetPlayers:
    async def test_get_all_players_returns_list(self):
        p1 = _make_player_dict()
        session = _make_session(players=[p1])
        service, ss, _, _ = _make_service(session)
        ss.current_session = session

        players = await service.get_all_players()

        assert len(players) == 1
        assert players[0].device_id == "dev-001"

    async def test_get_all_players_returns_empty_when_no_session(self):
        service, ss, _, _ = _make_service(session=None)
        ss.current_session = None

        players = await service.get_all_players()

        assert players == []

    async def test_get_player_by_device_id_found(self):
        p1 = _make_player_dict()
        session = _make_session(players=[p1])
        service, ss, _, _ = _make_service(session)
        ss.current_session = session

        player = await service.get_player_by_device_id("dev-001")

        assert player is not None
        assert player.device_id == "dev-001"

    async def test_get_player_by_device_id_not_found(self):
        session = _make_session()
        service, ss, _, _ = _make_service(session)
        ss.current_session = session

        player = await service.get_player_by_device_id("dev-unknown")

        assert player is None

    async def test_get_player_by_device_id_returns_none_when_no_session(self):
        service, ss, _, _ = _make_service(session=None)
        ss.current_session = None

        player = await service.get_player_by_device_id("dev-001")

        assert player is None

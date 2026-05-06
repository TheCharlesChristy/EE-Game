"""
Unit tests for registry.models — Player dataclass.
EP-03, US-01 AC-1, AC-2.
"""

import datetime


from ee_game_backend.registry.models import Player


def _make_player(**overrides) -> Player:
    now = datetime.datetime(2026, 1, 1, 12, 0, 0)
    defaults = dict(
        player_id="pid-001",
        device_id="dev-001",
        username="BraveFox",
        colour="#E6194B",
        connection_state="connected",
        last_seen_at=now,
        registered_at=now,
        firmware_version="1.0.0",
        board_target="esp32c3",
    )
    defaults.update(overrides)
    return Player(**defaults)


class TestPlayerToDict:
    def test_round_trip(self):
        player = _make_player()
        d = player.to_dict()
        restored = Player.from_dict(d)
        assert restored.player_id == player.player_id
        assert restored.device_id == player.device_id
        assert restored.username == player.username
        assert restored.colour == player.colour
        assert restored.connection_state == player.connection_state
        assert restored.last_seen_at == player.last_seen_at
        assert restored.registered_at == player.registered_at
        assert restored.firmware_version == player.firmware_version
        assert restored.board_target == player.board_target

    def test_to_dict_contains_iso_timestamps(self):
        now = datetime.datetime(2026, 3, 28, 10, 0, 0)
        player = _make_player(last_seen_at=now, registered_at=now)
        d = player.to_dict()
        assert d["last_seen_at"] == now.isoformat()
        assert d["registered_at"] == now.isoformat()

    def test_to_dict_all_keys_present(self):
        player = _make_player()
        d = player.to_dict()
        expected_keys = {
            "player_id",
            "device_id",
            "username",
            "colour",
            "connection_state",
            "last_seen_at",
            "registered_at",
            "firmware_version",
            "board_target",
        }
        assert set(d.keys()) == expected_keys


class TestPlayerFromDict:
    def test_from_dict_handles_missing_optional_keys(self):
        """from_dict should not raise when optional fields are absent."""
        minimal = {
            "player_id": "pid-999",
            "device_id": "dev-999",
        }
        player = Player.from_dict(minimal)
        assert player.player_id == "pid-999"
        assert player.device_id == "dev-999"
        # Optional fields receive safe defaults.
        assert player.username == "Unknown"
        assert player.colour == "#808080"
        assert player.connection_state == "disconnected"
        assert player.firmware_version == "unknown"
        assert player.board_target == "unknown"

    def test_from_dict_preserves_connection_state(self):
        player = _make_player(connection_state="stale")
        restored = Player.from_dict(player.to_dict())
        assert restored.connection_state == "stale"

    def test_round_trip_with_disconnected_state(self):
        player = _make_player(connection_state="disconnected")
        restored = Player.from_dict(player.to_dict())
        assert restored.connection_state == "disconnected"

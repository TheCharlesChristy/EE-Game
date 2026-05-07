"""
Unit tests for EP-02 session domain models.
SRS reference: FR-001–FR-010, Section 9.2, Section 9.3, Section 9.4.
"""

import datetime
import uuid


from ee_game_backend.session.models import (
    AuditEvent,
    Session,
    SessionArchive,
    SessionStatus,
    compute_checksum,
)


class TestSessionNew:
    def test_creates_active_session(self):
        session = Session.new()
        assert session.status == SessionStatus.ACTIVE

    def test_creates_uuid_id(self):
        session = Session.new()
        # Must be parseable as a UUID.
        parsed = uuid.UUID(session.id)
        assert str(parsed) == session.id

    def test_unique_ids_across_calls(self):
        s1 = Session.new()
        s2 = Session.new()
        assert s1.id != s2.id

    def test_created_at_and_updated_at_are_set(self):
        before = datetime.datetime.now(datetime.UTC)
        session = Session.new()
        after = datetime.datetime.now(datetime.UTC)
        assert before <= session.created_at <= after
        assert before <= session.updated_at <= after

    def test_optional_fields_are_none_or_empty(self):
        session = Session.new()
        assert session.current_round_id is None
        assert session.players == []
        assert session.standings == []
        assert session.active_game is None


class TestSessionRoundTrip:
    def test_to_payload_dict_then_from_payload_dict_is_lossless(self):
        session = Session.new()
        session.players = [{"name": "Alice", "cumulative_score": 42}]
        session.standings = [{"rank": 1, "player_id": "abc"}]
        session.active_game = "resistor_colour_code"
        session.current_round_id = str(uuid.uuid4())
        session.status = SessionStatus.PAUSED

        payload = session.to_payload_dict()
        restored = Session.from_payload_dict(payload)

        assert restored.id == session.id
        assert restored.status == session.status
        assert restored.created_at == session.created_at
        assert restored.updated_at == session.updated_at
        assert restored.current_round_id == session.current_round_id
        assert restored.players == session.players
        assert restored.standings == session.standings
        assert restored.active_game == session.active_game

    def test_finished_status_survives_round_trip(self):
        session = Session.new()
        session.status = SessionStatus.FINISHED
        restored = Session.from_payload_dict(session.to_payload_dict())
        assert restored.status == SessionStatus.FINISHED

    def test_none_optional_fields_survive_round_trip(self):
        session = Session.new()
        payload = session.to_payload_dict()
        restored = Session.from_payload_dict(payload)
        assert restored.current_round_id is None
        assert restored.active_game is None


class TestComputeChecksum:
    def test_returns_64_char_hex_string(self):
        result = compute_checksum('{"key": "value"}')
        assert isinstance(result, str)
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

    def test_is_deterministic(self):
        payload = '{"id": "abc", "status": "active"}'
        assert compute_checksum(payload) == compute_checksum(payload)

    def test_different_payloads_produce_different_checksums(self):
        c1 = compute_checksum('{"value": 1}')
        c2 = compute_checksum('{"value": 2}')
        assert c1 != c2

    def test_mutating_payload_changes_checksum(self):
        original = '{"status": "active"}'
        mutated = '{"status": "paused"}'
        assert compute_checksum(original) != compute_checksum(mutated)


class TestSessionArchiveFromSession:
    def _make_session_with_players(self) -> Session:
        session = Session.new()
        session.players = [
            {"name": "Alice", "username": "alice123", "colour": "red", "cumulative_score": 10},
            {"name": "Bob", "username": "bob456", "colour": "blue", "cumulative_score": 5},
        ]
        session.standings = [{"rank": 1}, {"rank": 2}]
        session.active_game = "ohms_law"
        return session

    def test_archive_has_correct_session_id(self):
        session = self._make_session_with_players()
        archive = SessionArchive.from_session(session)
        assert archive.session_id == session.id

    def test_archive_id_is_uuid(self):
        session = self._make_session_with_players()
        archive = SessionArchive.from_session(session)
        uuid.UUID(archive.id)  # Raises ValueError if not valid UUID.

    def test_player_usernames_not_in_payload(self):
        session = self._make_session_with_players()
        archive = SessionArchive.from_session(session)
        payload_str = str(archive.anonymised_payload)
        assert "alice123" not in payload_str
        assert "bob456" not in payload_str
        assert "Alice" not in payload_str
        assert "Bob" not in payload_str

    def test_players_use_positional_labels(self):
        session = self._make_session_with_players()
        archive = SessionArchive.from_session(session)
        labels = [p["archive_label"] for p in archive.anonymised_payload["players"]]
        assert labels == ["Player_1", "Player_2"]

    def test_player_scores_and_colours_are_preserved(self):
        session = self._make_session_with_players()
        archive = SessionArchive.from_session(session)
        players = archive.anonymised_payload["players"]
        assert players[0]["cumulative_score"] == 10
        assert players[0]["colour"] == "red"
        assert players[1]["cumulative_score"] == 5
        assert players[1]["colour"] == "blue"

    def test_standings_are_preserved(self):
        session = self._make_session_with_players()
        archive = SessionArchive.from_session(session)
        assert archive.anonymised_payload["standings"] == session.standings

    def test_retention_state_defaults_to_retained(self):
        session = self._make_session_with_players()
        archive = SessionArchive.from_session(session)
        assert archive.retention_state == "retained"

    def test_empty_players_produces_empty_anon_list(self):
        session = Session.new()
        archive = SessionArchive.from_session(session)
        assert archive.anonymised_payload["players"] == []


class TestAuditEventNew:
    def test_assigns_uuid_id(self):
        event = AuditEvent.new(session_id=None, action_type="session_created")
        uuid.UUID(event.id)  # Raises if not valid.

    def test_correct_action_type(self):
        event = AuditEvent.new(session_id="sess-1", action_type="session_paused")
        assert event.action_type == "session_paused"

    def test_correct_session_id(self):
        event = AuditEvent.new(session_id="sess-1", action_type="session_paused")
        assert event.session_id == "sess-1"

    def test_none_session_id_is_allowed(self):
        event = AuditEvent.new(session_id=None, action_type="system_restart")
        assert event.session_id is None

    def test_default_actor_type_is_host(self):
        event = AuditEvent.new(session_id=None, action_type="test")
        assert event.actor_type == "host"

    def test_custom_actor_type(self):
        event = AuditEvent.new(session_id=None, action_type="test", actor_type="admin")
        assert event.actor_type == "admin"

    def test_payload_summary_defaults_to_empty_string(self):
        event = AuditEvent.new(session_id=None, action_type="test")
        assert event.payload_summary == ""

    def test_created_at_is_recent(self):
        before = datetime.datetime.now(datetime.UTC)
        event = AuditEvent.new(session_id=None, action_type="test")
        after = datetime.datetime.now(datetime.UTC)
        assert before <= event.created_at <= after

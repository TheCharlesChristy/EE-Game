from ee_game_backend.games.common.simple import SimpleEventGame

from .metadata import METADATA


class GameImpl(SimpleEventGame):
    metadata = METADATA
    valid_event_types = {"analog", "answer", "estimate"}
    scoring_events = {"answer", "estimate"}
    base_points = 12
    correct_bonus = 10

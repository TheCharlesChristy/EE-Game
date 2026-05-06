from ee_game_backend.games.common.simple import SimpleEventGame

from .metadata import METADATA


class GameImpl(SimpleEventGame):
    metadata = METADATA
    valid_event_types = {"buzz", "answer", "button"}
    scoring_events = {"answer", "buzz"}
    base_points = 5
    correct_bonus = 20

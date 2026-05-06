from ee_game_backend.games.common.simple import SimpleEventGame

from .metadata import METADATA


class GameImpl(SimpleEventGame):
    metadata = METADATA
    valid_event_types = {"answer", "buzz", "button"}
    scoring_events = {"answer"}
    base_points = 10
    correct_bonus = 20

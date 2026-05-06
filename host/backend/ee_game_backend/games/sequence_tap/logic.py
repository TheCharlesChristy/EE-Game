from ee_game_backend.games.common.simple import SimpleEventGame

from .metadata import METADATA


class GameImpl(SimpleEventGame):
    metadata = METADATA
    valid_event_types = {"sequence", "tap", "button"}
    scoring_events = {"sequence", "tap"}
    base_points = 10
    correct_bonus = 15

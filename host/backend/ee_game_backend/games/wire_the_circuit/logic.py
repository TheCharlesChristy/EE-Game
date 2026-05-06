from ee_game_backend.games.common.simple import SimpleEventGame

from .metadata import METADATA


class GameImpl(SimpleEventGame):
    metadata = METADATA
    valid_event_types = {"continuity", "analog", "input"}
    scoring_events = {"continuity", "analog"}
    base_points = 20
    correct_bonus = 15

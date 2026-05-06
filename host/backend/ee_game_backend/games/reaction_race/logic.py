from ee_game_backend.games.common.simple import SimpleEventGame

from .metadata import METADATA


class GameImpl(SimpleEventGame):
    metadata = METADATA
    valid_event_types = {"button", "input"}
    scoring_events = {"button", "input"}
    base_points = 10
    speed_bonus_under_ms = 800
    speed_bonus_points = 15

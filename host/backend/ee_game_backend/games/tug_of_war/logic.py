from ee_game_backend.games.common.simple import SimpleEventGame

from .metadata import METADATA


class GameImpl(SimpleEventGame):
    metadata = METADATA
    valid_event_types = {"button", "tap", "input"}
    scoring_events = {"button", "tap", "input"}
    base_points = 4
    correct_bonus = 0
    speed_bonus_points = 0

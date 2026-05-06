from ee_game_backend.games.common.simple import SimpleEventGame

from .metadata import METADATA


class GameImpl(SimpleEventGame):
    metadata = METADATA
    valid_event_types = {"analog", "dial"}
    scoring_events = {"analog", "dial"}
    base_points = 8
    correct_bonus = 12

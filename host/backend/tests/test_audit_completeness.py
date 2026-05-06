from ee_game_backend.round.state_machine import ALLOWED_TRANSITIONS


def test_round_state_machine_has_explicit_exits_for_all_non_terminal_phases():
    assert all(targets for targets in ALLOWED_TRANSITIONS.values())

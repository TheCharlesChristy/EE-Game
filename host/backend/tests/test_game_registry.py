from ee_game_backend.games.registry import GameRegistry


def test_builtin_registry_loads_ten_games():
    registry = GameRegistry.load_builtin()
    games = registry.all()
    assert len(games) == 10
    assert {game.metadata.id for game in games} >= {
        "reaction_race",
        "quick_quiz_buzzer",
        "tug_of_war",
    }


def test_registry_filters_team_capable_games():
    registry = GameRegistry.load_builtin()
    team_games = registry.all(team_capable=True)
    assert len(team_games) >= 3
    assert all(game.metadata.team_capable for game in team_games)

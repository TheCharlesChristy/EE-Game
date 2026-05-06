from ee_game_backend.scoring.team_allocator import allocate_teams


def test_allocate_teams_is_deterministic_with_seed():
    players = [{"player_id": f"p{i}"} for i in range(7)]
    first = allocate_teams(players, team_size=3, seed=42)
    second = allocate_teams(players, team_size=3, seed=42)
    assert [team.to_dict() for team in first] == [team.to_dict() for team in second]


def test_allocate_teams_balances_sizes_within_one():
    players = [{"player_id": f"p{i}"} for i in range(10)]
    teams = allocate_teams(players, team_size=4, seed=1)
    sizes = [len(team.player_ids) for team in teams]
    assert max(sizes) - min(sizes) <= 1

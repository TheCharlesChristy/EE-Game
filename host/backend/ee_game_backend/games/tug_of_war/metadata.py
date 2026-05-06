from ee_game_backend.games.contract import GameMetadata

METADATA = GameMetadata(
    id="tug_of_war",
    title="Tug-of-War",
    category="team",
    summary="Teams repeatedly trigger valid inputs to pull the shared meter.",
    min_players=4,
    max_players=20,
    estimated_seconds=60,
    input_modes=["button"],
    materials=["ESP32 device", "momentary button"],
    build_instructions=[
        "Wire one rapid input button per device.",
        "Test for clean debounced presses.",
        "Coordinate with your allocated team when live starts.",
    ],
    team_capable=True,
    team_size=4,
    scoring_mode="team-meter",
)

from ee_game_backend.games.contract import GameMetadata

METADATA = GameMetadata(
    id="pattern_memory",
    title="Pattern Memory",
    category="memory",
    summary="Players repeat LED or input patterns with increasing length.",
    min_players=1,
    max_players=20,
    estimated_seconds=120,
    input_modes=["button", "sequence"],
    materials=["ESP32 device", "two momentary buttons", "status LED"],
    build_instructions=[
        "Wire two input buttons to the configured pins.",
        "Verify both button presses are detected during test.",
        "Follow the public display pattern when live starts.",
    ],
    team_capable=True,
    team_size=2,
    scoring_mode="streak",
)

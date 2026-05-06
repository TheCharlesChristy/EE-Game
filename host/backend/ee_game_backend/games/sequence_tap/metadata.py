from ee_game_backend.games.contract import GameMetadata

METADATA = GameMetadata(
    id="sequence_tap",
    title="Sequence Tap",
    category="logic",
    summary="Players tap the displayed binary or colour sequence in order.",
    min_players=1,
    max_players=20,
    estimated_seconds=100,
    input_modes=["sequence", "button"],
    materials=["ESP32 device", "two momentary buttons"],
    build_instructions=[
        "Wire two buttons to represent the two sequence choices.",
        "Test each button individually.",
        "Submit the displayed sequence as accurately as possible.",
    ],
    scoring_mode="ordered-input",
)

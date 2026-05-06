from ee_game_backend.games.contract import GameMetadata

METADATA = GameMetadata(
    id="analog_dial_match",
    title="Analog Dial Match",
    category="analog",
    summary="Players tune a potentiometer to match a target reading.",
    min_players=1,
    max_players=20,
    estimated_seconds=75,
    input_modes=["analog"],
    materials=["ESP32 device", "10k potentiometer", "breadboard jumpers"],
    build_instructions=[
        "Wire the potentiometer outer legs to 3V3 and ground.",
        "Wire the wiper to the configured analog input.",
        "Turn the dial through its full range during test.",
    ],
    scoring_mode="accuracy",
)

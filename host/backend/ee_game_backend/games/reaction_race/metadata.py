from ee_game_backend.games.contract import GameMetadata

METADATA = GameMetadata(
    id="reaction_race",
    title="Reaction Race",
    category="timing",
    summary="Players press their input as soon as the live signal appears.",
    min_players=2,
    max_players=20,
    estimated_seconds=45,
    input_modes=["button"],
    materials=["ESP32 device", "momentary button", "breadboard jumpers"],
    build_instructions=[
        "Wire the button between the configured input pin and ground.",
        "Confirm the status LED is connected and visible.",
        "Run one test press before the live countdown.",
    ],
    scoring_mode="fastest-correct",
)

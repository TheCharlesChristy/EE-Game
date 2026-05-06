from ee_game_backend.games.contract import GameMetadata

METADATA = GameMetadata(
    id="morse_decode",
    title="Morse Decode",
    category="communication",
    summary="Players decode timed pulses and submit the matching symbol.",
    min_players=1,
    max_players=20,
    estimated_seconds=120,
    input_modes=["button", "answer"],
    materials=["ESP32 device", "momentary button", "status LED"],
    build_instructions=[
        "Wire one input button.",
        "Confirm short and long presses register during test.",
        "Watch the public display signal before answering.",
    ],
    scoring_mode="decode",
)

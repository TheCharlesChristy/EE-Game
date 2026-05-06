from ee_game_backend.games.contract import GameMetadata

METADATA = GameMetadata(
    id="quick_quiz_buzzer",
    title="Quick Quiz Buzzer",
    category="knowledge",
    summary="Players buzz in and answer electronics questions under time pressure.",
    min_players=2,
    max_players=20,
    estimated_seconds=90,
    input_modes=["button", "answer"],
    materials=["ESP32 device", "momentary button"],
    build_instructions=[
        "Connect a single buzzer button to the input pin.",
        "Keep the device visible to the facilitator for answer adjudication.",
    ],
    scoring_mode="first-correct",
)

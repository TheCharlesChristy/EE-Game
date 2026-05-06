from ee_game_backend.games.contract import GameMetadata

METADATA = GameMetadata(
    id="color_code_speed_round",
    title="Color Code Speed Round",
    category="components",
    summary="Players identify resistor colour code values as quickly as possible.",
    min_players=1,
    max_players=20,
    estimated_seconds=90,
    input_modes=["answer", "button"],
    materials=["ESP32 device", "momentary button", "resistor reference card"],
    build_instructions=[
        "Wire one confirmation button.",
        "Keep the resistor colour reference card nearby during build only.",
        "Buzz and answer when the value appears.",
    ],
    scoring_mode="component-knowledge",
)

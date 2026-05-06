from ee_game_backend.games.contract import GameMetadata

METADATA = GameMetadata(
    id="voltage_estimate",
    title="Voltage Estimate",
    category="estimation",
    summary="Players estimate a target voltage and submit the nearest value.",
    min_players=1,
    max_players=20,
    estimated_seconds=90,
    input_modes=["analog", "answer"],
    materials=["ESP32 device", "potentiometer", "breadboard jumpers"],
    build_instructions=[
        "Wire a potentiometer to the analog input.",
        "Sweep the input during test.",
        "Dial in the estimate before submitting.",
    ],
    scoring_mode="closest-value",
)

from ee_game_backend.games.contract import GameMetadata

METADATA = GameMetadata(
    id="wire_the_circuit",
    title="Wire-the-Circuit",
    category="circuit",
    summary="Players assemble a simple circuit and prove the expected signal path.",
    min_players=1,
    max_players=20,
    estimated_seconds=180,
    input_modes=["continuity", "analog"],
    materials=["ESP32 device", "resistor", "LED", "breadboard jumpers"],
    build_instructions=[
        "Build the displayed resistor and LED circuit.",
        "Connect the sense wire to the configured input.",
        "Press test once the LED path is complete.",
    ],
    team_capable=True,
    team_size=2,
    scoring_mode="build-and-test",
)

# Multi-Team Gaming System MVP Requirements

## System Overview
A Raspberry Pi-based competitive gaming system supporting up to 8 teams with custom circuitry integration. Each team has a button/latch circuit with LED feedback connected to dedicated GPIO pins.

## Hardware Interface Specifications

### Per-Team Circuit Connections
- **Latch Pin**: Input pin to read button press state (stays HIGH until reset)
- **Reset Latch Pin**: Output pin to reset the latch back to LOW
- **LED Pin**: Output pin to control team's LED indicator
- **GND**: Ground connection (shared)

### Pin Mapping
- Support for 8 teams maximum
- Configurable pin assignment through team registration interface

## Technical Architecture

### Backend (Python)
- **Framework**: Flask with Flask-SocketIO for WebSocket support
- **GPIO Library**: RPi.GPIO
- **Threading**: 
  - Main thread: Flask web server
  - Background thread: Continuous GPIO monitoring with message queue
- **Templating**: Jinja2 for dynamic HTML generation
- **Data Storage**: JSON files for configuration and quiz questions

### Frontend
- **Technologies**: HTML5, CSS3, JavaScript
- **Architecture**: Component-based structure (`app/components/componentName/`)
- **Communication**: WebSocket connections for real-time updates
- **Responsive Design**: Optimized for HDMI display output

### Component Structure
```
app/
├── components/
│   ├── main_menu/
│   ├── team_registration/
│   ├── circuit_test/
│   ├── reaction_timer/
│   ├── wheel_game/
│   ├── quiz_game/
│   └── shared/
├── static/
├── templates/
├── config/
└── main.py
```

## Core System Features

### Team Registration & Setup
**User Story**: As a game operator, I want to register teams to specific GPIO pins so I can identify which team is which during gameplay.

**Requirements**:
- Web interface to assign team names to GPIO pin numbers
- Support for 1-8 teams
- Easily accessible during session for troubleshooting
- Persistent storage of team configurations
- Clear visual indication of registered teams

### Circuit Testing
**User Story**: As a game operator, I want to test each team's circuit before starting games to ensure all hardware is working correctly.

**Requirements**:
- Manual test interface for each registered team
- "Test Button" functionality that lights up LED when pressed
- Real-time feedback showing button press detection
- Visual confirmation of latch/reset functionality
- LED control testing (manual on/off)

## Game 1: Reaction Timer

### Game Description
Teams compete in a fast-paced reaction game where they must press their button when the screen turns green. Teams are eliminated after 3 failed attempts, with timing windows decreasing each round.

### User Stories
- **As a player**, I want clear visual feedback when the screen changes color so I know when to react
- **As a player**, I want to see my team's remaining lives so I know my current status
- **As a game operator**, I want the game to automatically speed up to maintain excitement

### Game Requirements

#### Visual Interface
- Full-screen color display (RED = wait, GREEN = go)
- Team status panel showing:
  - Team names
  - Lives remaining (3 max)
  - Elimination status
- Round counter
- Current time allowance display

#### Game Mechanics
- **Starting Parameters**:
  - Time allowance: 200ms
  - Lives per team: 3
  - Time reduction: 10% per round
- **Round Flow**:
  1. Display RED screen for random duration (2-8 seconds)
  2. Switch to GREEN screen
  3. Accept button presses for the time allowance window
  4. Show results (who succeeded/failed)
  5. Update lives and eliminate teams with 0 lives
  6. Reduce time allowance by 10%
  7. Continue until 1 team remains

#### LED Feedback
- **Solid ON**: Button press registered within time window
- **Flashing**: Button press registered but outside time window (penalty)
- **OFF**: No press registered or team eliminated

#### Win Conditions
- Last team standing wins
- If all teams eliminated simultaneously, declare draw

## Game 2: Wheel Game

### Game Description
A tournament-style game with 10 rounds featuring three different game modes. Teams earn points based on performance, with a final tiebreaker if needed.

### User Stories
- **As a player**, I want to see which game mode is active so I know what to expect
- **As a player**, I want clear visual indication when I'm selected for a 1v1 or assigned to a team color
- **As a game operator**, I want automatic scoring and leaderboard updates

### Game Requirements

#### Visual Interface
- **Wheel Display**: Circular interface with equal segments for each team
- **Game Mode Indicator**: Clear display of current mode
- **Scoreboard**: Points for each team
- **Round Counter**: Current round (1-10)
- **Team Selection Visual**:
  - 1v1: Enlarge selected team segments
  - Red vs Blue: Color segments red/blue
  - Free-for-all: All segments highlighted

#### Game Modes

##### Mode 1: One vs One (1v1)
- Randomly select 2 teams who haven't competed this round
- Standard reaction test (GREEN screen trigger)
- Winner gets 100 points
- Continue until all teams have competed once
- If odd number of teams, one team gets a bye

##### Mode 2: Free For All
- All active teams participate
- Standard reaction test (GREEN screen trigger)
- Fastest reaction gets 200 points
- Single elimination per round

##### Mode 3: Red vs Blue
- Randomly split teams into two groups
- Teams assigned red or blue colors on wheel
- Standard reaction test (GREEN screen trigger)
- Calculate average reaction time per team
- All members of winning team get 100 points each

#### Game Flow
1. Display wheel with team segments
2. Randomly select game mode for round
3. Execute game mode mechanics
4. Update scores and display leaderboard
5. Repeat for 10 rounds total
6. Declare winner(s)

#### Tiebreaker System
- If multiple teams tied for highest score after 10 rounds
- Conduct 1v1 elimination tournament between tied teams
- Continue until single winner emerges

#### LED Feedback
- **Solid ON**: Successful button press registered
- **Rapid Flash**: Selected for 1v1 mode
- **Color-coded Flash**: Red team (fast flash) vs Blue team (slow flash)
- **OFF**: Not participating in current round

## Game 3: Quiz Game

### Game Description
A buzzer-based quiz game where teams compete to answer questions first. Wrong answers lock teams out of the current question round.

### User Stories
- **As a player**, I want immediate feedback when I buzz in first
- **As a game operator**, I want easy controls to mark answers correct/incorrect
- **As a game operator**, I want questions loaded from a configurable file

### Game Requirements

#### Visual Interface
- **Question Display**: Large, readable text
- **Team Status Panel**: 
  - Team names
  - Current scores
  - Lock-out status (grayed out when locked)
- **Buzzer Indicator**: Show which team buzzed in first
- **Admin Controls**: Correct/Incorrect buttons for game operators
- **Next Question Button**: Progress to next question

#### Question Management
- **Question File**: JSON format with structure:
  ```json
  {
    "questions": [
      {
        "id": 1,
        "question": "What is the capital of France?",
        "difficulty": "easy",
        "points": 10
      }
    ]
  }
  ```
- **Point Values**: Configurable per question based on difficulty
- **Question Selection**: Random selection from available questions

#### Game Mechanics
1. Display question to all teams
2. Enable buzzer functionality
3. First team to buzz in gets to answer
4. Game operator marks answer as correct/incorrect
5. **If Correct**: Award points, proceed to next question
6. **If Incorrect**: Lock team out, continue with remaining teams
7. If no one answers correctly, proceed to next question
8. Reset lock-outs for each new question

#### Scoring System
- Points awarded based on question difficulty (defined in JSON)
- Running score display
- Final leaderboard at game end

#### LED Feedback
- **Solid ON**: Successfully buzzed in first
- **Slow Flash**: Locked out of current question
- **OFF**: Available to buzz in

## System Administration Features

### Main Menu
- Game selection interface
- Quick access to team registration
- Circuit testing shortcut
- Game configuration options

### Error Handling
- **Hardware Failure**: Teams with non-responsive hardware are automatically excluded
- **Game Interruption**: Operators can exit any game by navigating away from the page
- **Connection Issues**: WebSocket reconnection handling

### Configuration Management
- Team registration persistence
- Quiz question file management
- Game parameter adjustment (reaction times, point values)

## Technical Implementation Details

### GPIO Monitoring Thread
```python
# Pseudo-code structure
class GPIOMonitor:
    def __init__(self, message_queue):
        self.message_queue = message_queue
        self.team_pins = {}  # loaded from config
    
    def monitor_loop(self):
        while running:
            for team, pins in self.team_pins.items():
                if GPIO.input(pins['latch']):
                    timestamp = time.time()
                    self.message_queue.put({
                        'team': team,
                        'action': 'button_press',
                        'timestamp': timestamp
                    })
                    # Reset latch
                    GPIO.output(pins['reset'], HIGH)
                    time.sleep(0.01)
                    GPIO.output(pins['reset'], LOW)
```

### WebSocket Events
- `team_registered`: Team assignment updates
- `button_press`: Real-time button press notifications
- `game_state_update`: Game status changes
- `led_control`: LED state changes
- `score_update`: Point changes

### Component Communication
- Each game component has its own WebSocket namespace
- Shared state management through Flask session
- Event-driven architecture for real-time updates

## Success Criteria

### MVP Acceptance Criteria
1. ✅ Support 8 teams with individual GPIO control
2. ✅ Team registration and circuit testing functionality
3. ✅ All three games fully functional with specified rules
4. ✅ Real-time visual feedback and LED control
5. ✅ WebSocket-based live updates
6. ✅ Configurable quiz questions via JSON
7. ✅ Main menu navigation between games
8. ✅ Automatic scoring and winner determination

### Performance Requirements
- Reaction time measurement accurate to ±10ms
- WebSocket latency < 100ms
- GPIO response time < 50ms
- Stable operation for 2+ hour sessions

### Usability Requirements
- Intuitive interface operable by non-technical staff
- Clear visual feedback for all game states
- Minimal setup time between games
- Robust error handling for hardware issues

## Future Enhancement Opportunities
- Sound effects and audio feedback
- Advanced statistics and game history
- Custom game mode creation
- Mobile device integration
- Tournament bracket management
- Data export capabilities
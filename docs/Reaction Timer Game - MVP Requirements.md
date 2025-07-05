# Reaction Timer Game - MVP Requirements

## Template MVP Requirements

### Core Features
- Full-screen color display that transitions from RED (wait) to GREEN (go) for clear visual cues
- Real-time team status tracking with lives remaining (3 max per team) and elimination states
- Round-based progression with automatic time allowance reduction (starts at 200ms, reduces 10% per round)
- Automatic game flow management from start to completion with winner determination
- Live feedback system showing which teams succeeded/failed each round

### User Actions
- Game operators can start/stop/reset the game
- System automatically progresses through rounds without manual intervention
- Operators can view real-time team performance and game statistics
- Emergency exit/abort functionality for unexpected situations

### Data Flow
- **Input**: Team registration data, hardware button press events, game configuration
- **Output**: LED control signals, team elimination events, winner determination, game statistics
- **Real-time**: WebSocket events for button presses, status updates, round progression

---

## Components Required

### ReactionScreen
**Purpose**: Provides the full-screen visual stimulus that teams react to during gameplay.

**MVP Requirements**:
- **Function**: Display full-screen RED (wait) and GREEN (go) states with smooth transitions
- **Input**: Game state events (waiting, go, results), round timing configuration
- **Output**: Visual state change events, screen transition confirmations
- **UI**: Full viewport coverage, high-contrast colors (RED #dc2626, GREEN #16a34a), large text display
- **Integration**: Receives timing events from GameController, triggers team response window

**Priority**: Critical | **Complexity**: Simple

---

### TeamStatusDisplay
**Purpose**: Shows real-time status of all participating teams including lives, elimination state, and current round performance.

**MVP Requirements**:
- **Function**: Display team names, lives remaining (visual indicators), elimination status, current round results
- **Input**: Team registration data, button press events, lives updates, elimination events
- **Output**: Team selection events, status change notifications
- **UI**: Grid layout for multiple teams, color-coded status indicators, lives dots (filled/empty), elimination visual state
- **Integration**: Receives updates from GameController and hardware events, displays team-specific LED status

**Priority**: Critical | **Complexity**: Moderate

---

### GameController
**Purpose**: Orchestrates the entire reaction timer game flow, timing, and rule enforcement.

**MVP Requirements**:
- **Function**: Manage round progression, timing windows, lives tracking, elimination logic, winner determination
- **Input**: Game start/stop commands, team button press events with timestamps, team registration data
- **Output**: Round state changes, team elimination events, LED control commands, winner announcements
- **UI**: Game control interface with start/stop buttons, round counter, current time allowance display
- **Integration**: Coordinates between all components, manages WebSocket communication, handles hardware GPIO events

**Priority**: Critical | **Complexity**: Complex

---

### RoundProgressIndicator
**Purpose**: Displays current round information and game progression status.

**MVP Requirements**:
- **Function**: Show current round number, time allowance for current round, game phase indicator
- **Input**: Round progression events, timing configuration updates
- **Output**: Round change notifications
- **UI**: Round counter display, time allowance indicator (e.g., "Time Limit: 180ms"), progress visualization
- **Integration**: Receives updates from GameController, provides visual feedback to operators

**Priority**: High | **Complexity**: Simple

---

### LEDFeedbackController
**Purpose**: Manages LED feedback for each team based on their performance in each round.

**MVP Requirements**:
- **Function**: Control team LEDs for success (solid), failure (flashing), and elimination (off) states
- **Input**: Team performance data, button press timing results, elimination events
- **Output**: GPIO LED control signals, feedback state confirmations
- **UI**: Visual LED status simulation for operator feedback
- **Integration**: Receives performance data from GameController, sends hardware control signals

**Priority**: Critical | **Complexity**: Moderate

---

### ResultsDisplay
**Purpose**: Shows round-by-round results and final game outcome.

**MVP Requirements**:
- **Function**: Display immediate round results, cumulative game statistics, winner announcement
- **Input**: Round completion data, team performance metrics, final game results
- **Output**: Results display events, statistics data
- **UI**: Results overlay/panel, success/failure indicators per team, winner celebration display
- **Integration**: Triggered by GameController round completions, displays team-specific results

**Priority**: High | **Complexity**: Simple

---

### GameTimer
**Purpose**: Manages precise timing for reaction windows and round transitions.

**MVP Requirements**:
- **Function**: Generate random wait periods (2-8 seconds), enforce reaction time windows, trigger round transitions
- **Input**: Round configuration, timing parameters, game state changes
- **Output**: Timing events, window expiration notifications, precision timing data
- **UI**: Timer display for operator reference, timing configuration controls
- **Integration**: Coordinates with GameController and ReactionScreen, provides high-precision timing

**Priority**: Critical | **Complexity**: Moderate

---

### ErrorHandler
**Purpose**: Manages error states, hardware failures, and game interruption scenarios.

**MVP Requirements**:
- **Function**: Detect hardware disconnections, handle team dropouts, manage game state recovery
- **Input**: Hardware status events, connection failures, team availability changes
- **Output**: Error notifications, game state adjustment events, recovery suggestions
- **UI**: Error message display, hardware status indicators, recovery action buttons
- **Integration**: Monitors all hardware components, coordinates with GameController for state management

**Priority**: High | **Complexity**: Moderate

---

### NavigationControls
**Purpose**: Provides navigation and control options for game operators during and after gameplay.

**MVP Requirements**:
- **Function**: Start/pause/stop game controls, return to main menu, restart game functionality
- **Input**: Operator commands, game state information
- **Output**: Navigation events, game control commands
- **UI**: Control button panel, game state indicators, navigation breadcrumbs
- **Integration**: Interfaces with GameController for game state management, provides exit routes

**Priority**: Medium | **Complexity**: Simple

---

## Technical Considerations

### Performance Requirements
- **Timing Precision**: ±10ms accuracy for reaction time measurement
- **Visual Response**: <50ms delay for screen color transitions
- **Hardware Integration**: <50ms GPIO response time for LED feedback
- **Real-time Updates**: <100ms WebSocket latency for multi-component coordination

### Hardware Integration
- **GPIO Monitoring**: Continuous monitoring of team button states with latch/reset functionality
- **LED Control**: Individual team LED control with multiple states (solid, flashing, off)
- **Button Press Detection**: Precise timestamp capture for reaction time calculation
- **Hardware Failure Recovery**: Graceful handling of disconnected or faulty team hardware

### Accessibility Features
- **High Contrast**: RED/GREEN color scheme optimized for color-blind accessibility
- **Visual Feedback**: Multiple visual indicators beyond just color (shapes, text, animations)
- **Large Screen Optimization**: All elements sized for 10+ foot viewing distance
- **Audio Cues**: Optional sound effects for state transitions (if audio system available)

### Error Handling Scenarios
- **Hardware Failures**: Automatic team exclusion for non-responsive hardware
- **Network Issues**: Local state management with WebSocket reconnection
- **Game Interruption**: Clean state preservation and recovery options
- **Invalid States**: Robust validation and correction of game state inconsistencies
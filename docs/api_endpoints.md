# Multi-Team Gaming System API Documentation

This document describes all available API endpoints and WebSocket events for the Multi-Team Gaming System.

## Base URL
All API endpoints are prefixed with the base server URL (e.g., `http://localhost:5000`)

---

## Web Routes

### GET `/`
Serves the home page template with all components assembled.

**Response:** HTML page

### GET `/team-management`
Serves the team management page template.

**Response:** HTML page

### GET `/static/<filename>`
Serves static assets from the app/assets directory.

**Parameters:**
- `filename` (path): Name of the asset file

**Response:** Static file or 404 if not found

---

## System Status API

### GET `/api/system/status`
Get current system status overview.

**Response:**
```json
{
  "status": "operational|error",
  "uptime_seconds": 12345,
  "teams": {
    "count": 4,
    "max": 8
  },
  "hardware": {
    "gpio_status": "connected|error"
  },
  "games": {
    "reaction_timer": "available|unavailable",
    "wheel_game": "available|unavailable",
    "quiz_game": "available|unavailable"
  }
}
```

### GET `/api/system/detailed-status`
Get detailed system status for components.

**Response:**
```json
{
  "system": {
    "status": "operational|error"
  },
  "hardware": {
    "status": "operational|error",
    "gpio": {
      "team_1": {"latch": "unknown", "reset": "unknown", "led": "unknown"},
      "team_2": {"latch": "unknown", "reset": "unknown", "led": "unknown"}
    },
    "gpio_connections": 8
  },
  "teams": {
    "count": 4
  },
  "games": {
    "reaction_timer": "available|unavailable",
    "wheel_game": "available|unavailable",
    "quiz_game": "available|unavailable"
  },
  "connection": "connected"
}
```

---

## Team Management API

### GET `/api/teams`
Get all registered teams with hardware status.

**Response:**
```json
{
  "teams": [
    {
      "id": 1,
      "name": "Team Alpha",
      "pin_set": 1,
      "color": "#e53e3e",
      "status": "connected|disconnected",
      "pins": {
        "latch": 11,
        "reset": 12,
        "led": 13
      }
    }
  ]
}
```

### POST `/api/teams`
Add a new team.

**Request Body:**
```json
{
  "name": "Team Name",
  "pin_set": 1
}
```

**Response:**
```json
{
  "id": 1,
  "name": "Team Name",
  "pin_set": 1,
  "color": "#e53e3e",
  "status": "connected"
}
```

**Status Codes:**
- `201`: Team created successfully
- `400`: Missing required fields or pin set in use/max teams reached

### DELETE `/api/teams/<team_id>`
Remove a team by ID.

**Parameters:**
- `team_id` (int): ID of the team to remove

**Status Codes:**
- `204`: Team removed successfully
- `404`: Team not found

---

## Game Management API

### GET `/api/games/available`
Get list of available games.

**Response:**
```json
{
  "games": [
    {
      "id": "reaction_timer",
      "name": "Reaction Timer",
      "min_teams": 2,
      "status": "available|unavailable"
    },
    {
      "id": "wheel_game",
      "name": "Wheel Game",
      "min_teams": 2,
      "status": "available|unavailable"
    },
    {
      "id": "quiz_game",
      "name": "Quiz Game",
      "min_teams": 2,
      "status": "available|unavailable"
    }
  ]
}
```

### POST `/api/games/<game_id>/validate`
Validate if a game can be started.

**Parameters:**
- `game_id` (string): ID of the game (`reaction_timer`, `wheel_game`, `quiz_game`)

**Request Body:**
```json
{
  "team_count": 4
}
```

**Response:**
```json
{
  "can_start": true,
  "issues": []
}
```

**Possible Issues:**
- "Game already in progress"
- "At least 2 teams required"
- "Game {game_id} is not enabled"
- "No quiz questions available" (for quiz game)

### POST `/api/games/<game_id>/start`
Start a game.

**Parameters:**
- `game_id` (string): ID of the game to start

**Request Body (optional):**
```json
{
  "team_ids": [1, 2, 3, 4]
}
```

**Response:**
```json
{
  "status": "success",
  "game_id": "reaction_timer"
}
```

**Status Codes:**
- `200`: Game started successfully
- `400`: Invalid game ID or game already in progress

### POST `/api/games/stop`
Stop the current game.

**Response:**
```json
{
  "status": "success"
}
```

---

## Hardware Testing API

### POST `/api/hardware/test/<team_id>`
Test hardware for a specific team.

**Parameters:**
- `team_id` (int): ID of the team to test

**Response:**
```json
{
  "team_id": 1,
  "status": "success|error",
  "tests": {
    "led": "pass|fail",
    "button": "pass|fail"
  }
}
```

### GET `/api/hardware/status`
Get hardware status.

**Response:**
```json
{
  "status": "operational|error",
  "gpio": {
    "team_1": {"latch": "unknown", "reset": "unknown", "led": "unknown"},
    "team_2": {"latch": "unknown", "reset": "unknown", "led": "unknown"}
  },
  "hardware_available": true
}
```

---

## Health Check API

### GET `/api/health`
Basic health check.

**Response:**
```json
{
  "status": "healthy"
}
```

### GET `/api/health/detailed`
Detailed health check of all services.

**Response:**
```json
{
  "status": "healthy|unhealthy",
  "checks": {
    "gpio": true,
    "websocket": true,
    "data": true
  }
}
```

---

## WebSocket Events

The system uses WebSocket for real-time communication. Connect to `/socket.io/` endpoint.

### Client to Server Events

#### `connect`
Triggered when client connects. Server responds with initial system status.

#### `disconnect`
Triggered when client disconnects.

#### `ping`
Send a ping to the server.

**Payload:**
```json
{
  "timestamp": 1641234567890
}
```

**Response:** `pong` event

#### `led_test_request`
Request to test an LED for a specific team.

**Payload:**
```json
{
  "team_id": 1,
  "duration_ms": 1000
}
```

**Response:** `led_test_response` event

#### `hardware_test_request`
Request to test hardware for a specific team.

**Payload:**
```json
{
  "team_id": 1
}
```

**Response:** `hardware_test_response` event

### Server to Client Events

#### `pong`
Response to ping request.

**Payload:**
```json
{
  "timestamp": 1641234567890,
  "server_time": 1641234567895
}
```

#### `system_status_update`
Broadcast system status updates.

**Payload:**
```json
{
  "system": {"status": "operational"},
  "hardware": {
    "status": "operational",
    "gpio_connections": 8
  },
  "teams": {"count": 4},
  "connection": "connected",
  "timestamp": 1641234567890
}
```

#### `team_registered`
Broadcast when a new team is registered.

**Payload:**
```json
{
  "team": {
    "id": 1,
    "name": "Team Alpha",
    "pin_set": 1,
    "color": "#e53e3e"
  },
  "team_count": 4
}
```

#### `hardware_status_update`
Broadcast hardware status changes.

**Payload:**
```json
{
  "status": "operational",
  "gpio": {
    "team_1": {"latch": "unknown", "reset": "unknown", "led": "unknown"}
  }
}
```

#### `led_test_response`
Response to LED test request.

**Payload:**
```json
{
  "team_id": 1,
  "status": "success|error",
  "duration_ms": 1000,
  "message": "Error message if failed"
}
```

#### `hardware_test_response`
Response to hardware test request.

**Payload:**
```json
{
  "team_id": 1,
  "status": "success|error",
  "tests": {
    "led": "pass|fail",
    "button": "pass|fail"
  },
  "message": "Error message if failed"
}
```

#### `button_press`
Broadcast when a team button is pressed.

**Payload:**
```json
{
  "team_id": 1,
  "timestamp": 1641234567890,
  "reaction_time_ms": 150,
  "valid": true
}
```

#### `game_started`
Broadcast when a game starts.

**Payload:**
```json
{
  "game_id": "reaction_timer",
  "teams": [1, 2, 3, 4],
  "start_time": 1641234567890
}
```

#### `round_started`
Broadcast when a game round starts.

**Payload:**
```json
{
  "round": 1,
  "time_limit_ms": 200,
  "active_teams": [1, 2, 3, 4]
}
```

#### `game_ended`
Broadcast when a game ends.

**Payload:**
```json
{
  "winner": {
    "team_id": 1,
    "team_name": "Team Alpha"
  },
  "final_standings": [
    {
      "team_id": 1,
      "team_name": "Team Alpha",
      "position": 1,
      "lives_remaining": 2
    }
  ]
}
```

---

## Error Handling

All API endpoints return appropriate HTTP status codes:

- `200`: Success
- `201`: Created
- `204`: No Content (successful deletion)
- `400`: Bad Request (invalid parameters)
- `404`: Not Found
- `500`: Internal Server Error

Error responses include a JSON object with an error message:
```json
{
  "error": "Error description"
}
```

---

## Game Types

### Reaction Timer Game
- Teams compete to press their button fastest when LEDs turn on
- Teams lose lives for not pressing in time
- Time limit decreases each round
- Last team standing wins

### Wheel Game
- Multiple game modes (one vs one, free for all, red vs blue)
- Points-based scoring system
- Fixed number of rounds

### Quiz Game
- Question-based gameplay
- Teams buzz in to answer
- Points awarded for correct answers

---

## Hardware Integration

The system integrates with GPIO hardware for:
- Button input detection (latch pins)
- LED control for visual feedback
- Hardware reset functionality

Each team is assigned a pin set containing:
- Latch pin (button input)
- Reset pin (hardware reset)
- LED pin (visual feedback)

Pin mappings are configurable via the system configuration file.

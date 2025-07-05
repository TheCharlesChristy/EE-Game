# Multi-Team Gaming System - Directory Structure Guide

## Project Overview

The Multi-Team Gaming System follows a **modular, component-based architecture** designed for maintainability, scalability, and clear separation of concerns. The directory structure emphasizes **component reusability**, **template composition**, and **clean server organization**.

## Root Directory Structure

```
EE Game/
├── app/                    # Main application source code
│   ├── assets/            # Static assets (images, audio, video)
│   ├── components/        # Reusable web components
│   ├── server/           # Python server modules
│   ├── templates/        # HTML page templates
│   └── main.py          # Application entry point
└── docs/                 # Project documentation
```

---

## Application Directory (`app/`)

The `app/` directory contains all source code and assets required for the Multi-Team Gaming System to function. This directory represents the complete application package and serves as the root for all runtime operations.

### Key Characteristics
- **Self-contained**: All application dependencies are contained within this directory
- **Modular**: Clear separation between static assets, reusable components, server logic, and page templates
- **Scalable**: Structure supports easy addition of new components and features
- **Framework-agnostic**: Component structure works with any templating system

---

## Assets Directory (`app/assets/`)

The assets directory serves as the **centralized repository for all static media files** used throughout the application. This includes visual, audio, and multimedia content that enhances the user experience.

### Structure and Organization
```
app/assets/
├── images/               # Visual assets
│   ├── icons/           # UI icons and symbols
│   ├── backgrounds/     # Background images
│   ├── logos/          # Team logos and branding
│   └── game-assets/    # Game-specific imagery
├── audio/               # Sound files
│   ├── effects/        # Sound effects (button clicks, alerts)
│   ├── music/          # Background music
│   └── announcements/  # Audio announcements
├── video/               # Video content
│   ├── tutorials/      # How-to videos
│   └── animations/     # Motion graphics
└── fonts/               # Custom typography (if needed)
    └── custom-fonts/   # Web fonts not available via CDN
```

### File Organization Principles
- **Logical Grouping**: Assets are organized by type and purpose
- **Descriptive Naming**: Files use clear, descriptive names indicating their purpose
- **Optimized Formats**: Images use appropriate formats (PNG for transparency, JPG for photos, SVG for icons)
- **Multiple Resolutions**: Critical images may include multiple sizes for different screen densities

### Usage Examples
```html
<!-- In templates or components -->
<img src="/assets/images/logos/team-alpha.png" alt="Team Alpha Logo">
<audio src="/assets/audio/effects/button-press.mp3" preload="none">
<video src="/assets/video/tutorials/setup-guide.mp4" controls>
```

---

## Components Directory (`app/components/`)

The components directory implements a **modular component system** where each component is self-contained within its own subdirectory. This architecture promotes **reusability**, **maintainability**, and **independent development**.

### Component Structure Pattern
```
app/components/
├── ComponentName/           # Individual component directory
│   ├── ComponentName.html  # Component markup/template
│   ├── ComponentName.css   # Component-specific styling
│   └── ComponentName.js    # Component functionality
└── AnotherComponent/
    ├── AnotherComponent.html
    ├── AnotherComponent.css
    └── AnotherComponent.js
```

### Component Architecture Principles

#### 1. Self-Contained Units
Each component directory contains **exactly three files** that define the complete component:
- **HTML**: Structural markup and content
- **CSS**: Visual styling and layout
- **JavaScript**: Interactive behavior and functionality

#### 2. Consistent Naming Convention
- **Directory Name**: PascalCase matching the component name
- **File Names**: Must match the directory name exactly
- **CSS Classes**: Follow BEM methodology with component name as base

#### 3. Independence and Reusability
- Components can function independently without requiring other components
- Components can be included in multiple templates
- Components communicate through well-defined interfaces (events, props, global state)

### Example Component Structure

#### TeamStatusPanel Component
```
app/components/TeamStatusPanel/
├── TeamStatusPanel.html    # Team display template
├── TeamStatusPanel.css     # Team styling and animations
└── TeamStatusPanel.js      # WebSocket handling, state management
```

**TeamStatusPanel.html**
```html
<div class="team-status-panel">
    <div class="team-grid" id="teamGrid">
        <!-- Dynamic team content populated by JavaScript -->
    </div>
</div>
```

**TeamStatusPanel.css**
```css
.team-status-panel {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: var(--space-lg);
    padding: var(--space-lg);
}

.team-card {
    background: var(--background-white);
    border-radius: 12px;
    padding: var(--space-md);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}
```

**TeamStatusPanel.js**
```javascript
class TeamStatusPanel {
    constructor() {
        this.teams = [];
        this.initializeWebSocket();
        this.render();
    }

    initializeWebSocket() {
        // WebSocket event handling
    }

    render() {
        // DOM manipulation and updates
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new TeamStatusPanel();
});
```

### Component Categories

#### Core UI Components
- **NavigationMenu**: Main menu and navigation
- **TeamStatusPanel**: Team information display
- **ScoreBoard**: Score tracking and display
- **GameTimer**: Time-based game controls

#### Game-Specific Components
- **ReactionScreen**: Full-screen color display for reaction games
- **WheelDisplay**: Rotating team selection wheel
- **QuizInterface**: Question display and buzzer system
- **LEDIndicator**: Visual representation of hardware LED states

#### Utility Components
- **WebSocketManager**: Centralized WebSocket communication
- **NotificationBanner**: System alerts and messages
- **LoadingSpinner**: Loading state indicators
- **ErrorHandler**: Error display and recovery

### Component Communication

#### Inbound Communication
- **WebSocket Events**: Real-time updates from Flask backend
- **Custom Events**: Messages from other components
- **Global State**: Shared application state
- **Configuration**: Initialization parameters

#### Outbound Communication
- **WebSocket Messages**: Data sent to Flask backend
- **DOM Events**: Custom events for other components
- **State Updates**: Modifications to shared state
- **Navigation Triggers**: Page routing requests

---

## Server Directory (`app/server/`)

The server directory contains all **Python modules and logic** required for the Flask backend operation. This includes GPIO handling, game logic, WebSocket management, and API endpoints.

### Structure and Organization
```
app/server/
├── __init__.py              # Package initialization
├── routes/                  # Flask route definitions
│   ├── __init__.py
│   ├── main_routes.py      # Main navigation routes
│   ├── game_routes.py      # Game-specific endpoints
│   ├── team_routes.py      # Team management
│   └── api_routes.py       # JSON API endpoints
├── models/                  # Data models and structures
│   ├── __init__.py
│   ├── team.py            # Team data model
│   ├── game.py            # Game state model
│   └── config.py          # Configuration management
├── services/               # Business logic services
│   ├── __init__.py
│   ├── gpio_service.py    # GPIO hardware interface
│   ├── game_service.py    # Game logic implementation
│   ├── team_service.py    # Team management logic
│   └── websocket_service.py # WebSocket event handling
├── utils/                  # Utility functions
│   ├── __init__.py
│   ├── validators.py      # Input validation
│   ├── formatters.py     # Data formatting
│   └── helpers.py        # General helper functions
└── config/                 # Configuration files
    ├── settings.py        # Application settings
    ├── gpio_pins.json    # Pin configuration
    └── questions.json    # Quiz questions
```

### Module Responsibilities

#### Routes (`routes/`)
Handle HTTP requests and define API endpoints:
- **main_routes.py**: Page navigation, template rendering
- **game_routes.py**: Game start/stop, configuration
- **team_routes.py**: Team registration, management
- **api_routes.py**: JSON responses for AJAX requests

#### Models (`models/`)
Define data structures and business entities:
- **team.py**: Team properties, state management
- **game.py**: Game state, scoring, rules
- **config.py**: System configuration, settings

#### Services (`services/`)
Implement core business logic:
- **gpio_service.py**: Raspberry Pi GPIO control
- **game_service.py**: Game mechanics, timing, scoring
- **team_service.py**: Team operations, validation
- **websocket_service.py**: Real-time communication

#### Utilities (`utils/`)
Provide support functions:
- **validators.py**: Input sanitization, validation
- **formatters.py**: Data transformation, formatting
- **helpers.py**: Common operations, utilities

#### Configuration (`config/`)
Store application settings:
- **settings.py**: Flask configuration, constants
- **gpio_pins.json**: Hardware pin assignments
- **questions.json**: Quiz questions database

### Integration Patterns

#### Flask Application Factory
```python
# app/server/__init__.py
from flask import Flask
from flask_socketio import SocketIO

def create_app():
    app = Flask(__name__)
    socketio = SocketIO(app)
    
    # Register blueprints
    from .routes import main_routes, game_routes
    app.register_blueprint(main_routes.bp)
    app.register_blueprint(game_routes.bp)
    
    return app, socketio
```

#### Service Layer Pattern
```python
# app/server/services/team_service.py
class TeamService:
    def __init__(self, gpio_service):
        self.gpio_service = gpio_service
        self.teams = {}
    
    def register_team(self, team_name, pins):
        # Team registration logic
        pass
    
    def test_team_circuit(self, team_id):
        # Circuit testing logic
        pass
```

---

## Templates Directory (`app/templates/`)

The templates directory contains **HTML page templates** that serve as the structural foundation for each page in the application. Templates use **Jinja2 templating engine** and are **composed primarily of web components**.

### Template Architecture

#### Structure Pattern
```
app/templates/
├── base.html               # Base template with common structure
├── main_menu.html         # Main navigation page
├── team_registration.html # Team setup page
├── circuit_test.html      # Hardware testing page
├── reaction_timer.html    # Reaction game page
├── wheel_game.html        # Wheel game page
├── quiz_game.html         # Quiz game page
└── includes/              # Partial templates
    ├── head.html         # Common <head> content
    ├── scripts.html      # Common JavaScript includes
    └── navigation.html   # Shared navigation elements
```

#### Template Composition Philosophy
Templates are **thin orchestration layers** that:
- Define page structure and layout
- Include appropriate web components
- Pass configuration to components
- Handle page-specific routing and parameters

#### Base Template Pattern
```html
<!-- app/templates/base.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    {% include 'includes/head.html' %}
    <title>{% block title %}Multi-Team Gaming System{% endblock %}</title>
    {% block extra_css %}{% endblock %}
</head>
<body>
    <div class="app-container">
        {% include 'includes/navigation.html' %}
        
        <main class="main-content">
            {% block content %}{% endblock %}
        </main>
    </div>
    
    {% include 'includes/scripts.html' %}
    {% block extra_js %}{% endblock %}
</body>
</html>
```

#### Component Integration Example
```html
<!-- app/templates/reaction_timer.html -->
{% extends 'base.html' %}

{% block title %}Reaction Timer Game{% endblock %}

{% block content %}
<div class="game-container">
    <!-- Include game-specific components -->
    {% include 'components/TeamStatusPanel/TeamStatusPanel.html' %}
    {% include 'components/ReactionScreen/ReactionScreen.html' %}
    {% include 'components/GameTimer/GameTimer.html' %}
</div>
{% endblock %}

{% block extra_css %}
<link rel="stylesheet" href="/static/components/TeamStatusPanel/TeamStatusPanel.css">
<link rel="stylesheet" href="/static/components/ReactionScreen/ReactionScreen.css">
<link rel="stylesheet" href="/static/components/GameTimer/GameTimer.css">
{% endblock %}

{% block extra_js %}
<script type="module" src="/static/components/TeamStatusPanel/TeamStatusPanel.js"></script>
<script type="module" src="/static/components/ReactionScreen/ReactionScreen.js"></script>
<script type="module" src="/static/components/GameTimer/GameTimer.js"></script>
{% endblock %}
```

### Template Responsibilities

#### Page Structure
- Define overall page layout
- Establish content hierarchy
- Include necessary stylesheets and scripts
- Handle responsive design framework

#### Component Orchestration
- Include relevant components for page functionality
- Pass configuration parameters to components
- Coordinate component interactions
- Manage component lifecycle

#### Data Binding
- Receive data from Flask routes
- Transform data for component consumption
- Handle template variables and loops
- Implement conditional rendering

### Template Categories

#### Navigation Templates
- **main_menu.html**: Primary navigation interface
- **game_selection.html**: Game mode selection

#### Setup Templates
- **team_registration.html**: Team configuration interface
- **circuit_test.html**: Hardware validation interface

#### Game Templates
- **reaction_timer.html**: Reaction timing game
- **wheel_game.html**: Tournament wheel game
- **quiz_game.html**: Buzzer-based quiz game

#### Utility Templates
- **error.html**: Error handling and display
- **loading.html**: Loading states and progress

---

## Entry Point (`app/main.py`)

The `main.py` file serves as the **single entry point** for the entire Multi-Team Gaming System application. This file bootstraps the Flask application, initializes all services, and starts the server.

### Primary Responsibilities

#### Application Initialization
```python
# app/main.py
from server import create_app
from server.services import GPIOService, GameService, TeamService

def main():
    # Create Flask application
    app, socketio = create_app()
    
    # Initialize services
    gpio_service = GPIOService()
    game_service = GameService(gpio_service)
    team_service = TeamService(gpio_service)
    
    # Start background monitoring
    gpio_service.start_monitoring()
    
    # Run application
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)

if __name__ == '__main__':
    main()
```

#### Service Coordination
- **GPIO Service**: Hardware interface initialization
- **WebSocket Service**: Real-time communication setup
- **Game Service**: Game logic preparation
- **Configuration**: System settings loading

#### Error Handling
- **Graceful Startup**: Handle initialization failures
- **Resource Cleanup**: Proper shutdown procedures
- **Logging Setup**: Application monitoring and debugging

---

## Documentation Directory (`docs/`)

The documentation directory contains all project documentation, specifications, and guides. This provides comprehensive information for developers, operators, and maintainers.

### Documentation Structure
```
docs/
├── requirements/           # System requirements and specifications
├── api/                   # API documentation
├── deployment/            # Setup and deployment guides
├── troubleshooting/       # Common issues and solutions
└── examples/             # Code examples and tutorials
```

---

## Architectural Benefits

### Modular Design
- **Independent Development**: Components can be developed and tested separately
- **Code Reusability**: Components work across multiple templates
- **Easy Maintenance**: Changes isolated to specific components or modules
- **Scalable Growth**: New features added without affecting existing code

### Clear Separation of Concerns
- **Frontend Components**: Handle UI logic and user interactions
- **Backend Services**: Manage business logic and hardware integration
- **Templates**: Orchestrate page composition and routing
- **Assets**: Provide static resources efficiently

### Development Workflow
- **Component-First**: Build reusable components before assembling pages
- **Service-Oriented**: Develop backend services independently
- **Template Composition**: Assemble pages from proven components
- **Asset Organization**: Centralized media management

### Testing Strategy
- **Unit Testing**: Test individual components and services
- **Integration Testing**: Test component interactions
- **System Testing**: Test complete page functionality
- **Hardware Testing**: Validate GPIO and hardware integration

This directory structure provides a solid foundation for building, maintaining, and scaling the Multi-Team Gaming System while promoting best practices in web development and embedded systems integration.
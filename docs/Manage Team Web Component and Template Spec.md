# Team Management Page - Web Component Specifications
## Multi-Team Gaming System

---

## Template MVP Requirements

### Core Features
- Register 1-8 teams with custom names and GPIO pin assignments
- Real-time circuit testing to validate hardware connections before gameplay
- Visual status monitoring showing connection health for each registered team
- Team configuration management with add/edit/remove capabilities
- System readiness validation before proceeding to games

### User Actions
- Add/remove teams with custom names and GPIO pin assignment
- Test individual team circuits with immediate visual feedback
- Modify team configurations (names, pin assignments) after initial setup
- Validate entire system readiness before returning to game selection
- Navigate between team management and game selection safely

### Data Flow
- **Inputs**: Team names, GPIO pin selections, hardware test triggers from user interactions
- **Outputs**: Team registration events, hardware test commands, navigation requests
- **Real-time**: WebSocket events for circuit testing, connection monitoring, status updates
- **Backend Communication**: API calls for team persistence, WebSocket for live hardware status

---

## Web Components Required

#### TeamRegistrationForm
**Purpose**: Handles the registration of individual teams with name input and GPIO pin assignment.

**MVP Requirements**:
- **Function**: Add new teams with validation, suggest available GPIO pins, prevent duplicate assignments
- **Input**: Team names (text input), GPIO pin selections (dropdown/visual selector), team limit validation (1-8 max)
- **Output**: `team_registered` events, `team_removed` events, form validation status changes
- **UI**: Team entry cards with name input fields, pin selectors, team color preview, remove buttons
- **Integration**: Validates against existing teams, updates pin availability across all team forms

**Priority**: Critical | **Complexity**: Moderate

---

#### HardwareTestPanel
**Purpose**: Provides real-time circuit testing capabilities for each registered team's hardware setup.

**MVP Requirements**:
- **Function**: Individual team circuit testing, bulk testing all teams, LED control verification
- **Input**: Test trigger buttons, team selection, GPIO status updates from backend via WebSocket
- **Output**: Test command events to backend, visual test results, hardware status displays
- **UI**: Test buttons per team, status indicators (connected/disconnected/testing), progress feedback, bulk test controls
- **Integration**: WebSocket communication to backend GPIO service, real-time status updates

**Priority**: Critical | **Complexity**: Moderate

---

#### TeamConfigurationList
**Purpose**: Displays overview of all registered teams with their current status and configuration details.

**MVP Requirements**:
- **Function**: Show team summary table, enable quick editing, display hardware status, handle team removal
- **Input**: Registered teams data, hardware connection status, team validation results
- **Output**: Edit mode triggers, team removal confirmations, status change notifications
- **UI**: Scrollable team list/table, status badges, edit/delete action buttons, team color indicators
- **Integration**: Reflects real-time hardware status from HardwareTestPanel, triggers TeamRegistrationForm for editing

**Priority**: High | **Complexity**: Simple

---

#### SystemReadinessIndicator
**Purpose**: Provides overall system health check and readiness validation before proceeding to games.

**MVP Requirements**:
- **Function**: Display minimum team requirements (2+), show hardware connection summary, assess overall system readiness
- **Input**: Team count from other components, hardware status aggregation, system health from backend
- **Output**: System readiness state, blocking issues list, navigation enable/disable decisions
- **UI**: Large status indicator with color coding, readiness checklist, blocking issues display, proceed button state
- **Integration**: Aggregates status from all other components, controls NavigationControls component state

**Priority**: High | **Complexity**: Simple

---

#### GPIOPinSelector
**Purpose**: Intelligent GPIO pin assignment interface that prevents conflicts and suggests optimal configurations.

**MVP Requirements**:
- **Function**: Display available GPIO pins, prevent double assignment, suggest optimal pin layouts for teams
- **Input**: Current pin assignments from all teams, GPIO service pin status from backend, hardware constraints
- **Output**: Pin selection events, pin availability updates, conflict warnings and suggestions
- **UI**: Visual GPIO pin layout diagram, availability indicators (free/used/unavailable), conflict highlighting, auto-suggest features
- **Integration**: Real-time synchronization across all TeamRegistrationForm instances, backend hardware validation

**Priority**: High | **Complexity**: Moderate

---

#### NavigationControls
**Purpose**: Provides navigation flow control with proper validation before allowing users to proceed or return.

**MVP Requirements**:
- **Function**: Enable return to main menu, proceed to games with validation, handle unsaved changes detection
- **Input**: System readiness state from SystemReadinessIndicator, unsaved changes detection, user navigation requests
- **Output**: Navigation events, confirmation dialogs for unsaved changes, state preservation requests
- **UI**: Back to main menu button, proceed to games button with readiness indication, unsaved changes warnings/modals
- **Integration**: Validates system readiness before proceeding, coordinates with all components for state preservation

**Priority**: Medium | **Complexity**: Simple

---

## Component Architecture & Integration

### Component Hierarchy
```
TeamManagementPage
├── NavigationControls
├── SystemReadinessIndicator
├── TeamRegistrationForm
│   └── GPIOPinSelector (embedded)
├── HardwareTestPanel
└── TeamConfigurationList
```

### Event Communication Flow
```
TeamRegistrationForm → team_registered → TeamConfigurationList, SystemReadinessIndicator
TeamRegistrationForm → team_removed → TeamConfigurationList, SystemReadinessIndicator
HardwareTestPanel → hardware_status_changed → SystemReadinessIndicator, TeamConfigurationList
GPIOPinSelector → pin_availability_changed → All TeamRegistrationForm instances
SystemReadinessIndicator → system_ready_changed → NavigationControls
NavigationControls → navigation_requested → Page-level routing
```

### WebSocket Events (Backend Communication)
```
// Outbound to Backend
test_team_circuit: { teamId, pinConfig }
register_team: { teamName, pins, teamColor }
remove_team: { teamId }

// Inbound from Backend  
gpio_status_update: { pinId, status, teamId }
circuit_test_result: { teamId, success, details }
hardware_health_changed: { overallStatus, pinStatuses }
```

### Shared State Management
- **Teams Collection**: Managed by TeamConfigurationList, shared with all components
- **GPIO Pin Availability**: Managed by GPIOPinSelector, synchronized across team forms
- **Hardware Status**: Real-time updates from backend, reflected across HardwareTestPanel and SystemReadinessIndicator
- **System Readiness**: Calculated by SystemReadinessIndicator, consumed by NavigationControls

---

## Technical Implementation Requirements

### File Structure
Each component follows the standard 3-file pattern:
```
app/components/ComponentName/
├── ComponentName.html    # Template structure
├── ComponentName.css     # Component-specific styling  
└── ComponentName.js      # Component logic and event handling
```

### Styling Requirements
- Use established CSS custom properties from design system
- Follow team color variables (--team-1-red through --team-8-brown)
- Implement responsive design for different screen sizes
- Ensure high contrast and accessibility compliance

### Event Interface Standards
- Use bubbling custom DOM events for component communication
- Include detailed event.detail objects with relevant data
- Follow consistent event naming convention: `[component]_[action]`
- Implement proper event cleanup in component destruction

### Error Handling Requirements
- Graceful degradation when WebSocket connection is lost
- Clear user feedback for validation errors and system issues
- Recovery mechanisms for failed hardware tests
- Prevent data loss during navigation

### Performance Considerations
- Efficient DOM updates during real-time status changes
- Debounced user input validation to prevent excessive backend calls
- Lazy loading of GPIO status to improve initial page load
- Minimal WebSocket message frequency for status updates

---

## Backend Integration Requirements

### API Endpoints Expected
```
GET  /api/teams              # Get current team configuration
POST /api/teams              # Register new team
PUT  /api/teams/{id}         # Update team configuration  
DELETE /api/teams/{id}       # Remove team
GET  /api/gpio/status        # Get current GPIO pin status
POST /api/gpio/test          # Trigger circuit test
```

### WebSocket Namespace
- Use `/team-management` namespace for page-specific events
- Handle connection/disconnection gracefully
- Implement automatic reconnection with state synchronization

### Data Persistence
- Team configurations should persist across page reloads
- GPIO pin assignments should be validated against hardware constraints
- System should recover gracefully from incomplete team setups

This specification provides the complete requirements for implementing the Team Management page as a collection of reusable, well-integrated web components that handle all UI logic while communicating with backend services for data persistence and hardware control.
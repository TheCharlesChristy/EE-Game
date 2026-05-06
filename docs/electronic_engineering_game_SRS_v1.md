# Electronic Engineering Hands-On Game Platform

## Software Requirements Specification (SRS)

*Production baseline specification*

Version 1.0

Status: Baseline

Date: 27 March 2026

This document specifies the complete software, firmware, UX, persistence, networking, and operational requirements for an offline, Raspberry Pi-hosted multiplayer electronics game platform for ages 14–18, supporting up to 20 concurrent ESP32-based players.

# Document Control

| Field | Value |
| --- | --- |
| Document title | Electronic Engineering Hands-On Game Platform — Software Requirements Specification |
| Version | 1.0 |
| Status | Baseline |
| Date | 27 March 2026 |
| Product intent | Production-quality delivery baseline rather than MVP |
| Primary host platform | Raspberry Pi 4 Model B minimum |
| Default player device target | ESP32-C3 |
| Firmware toolchain | PlatformIO + Arduino framework for ESP32 |
| Persistence | SQLite |

## Revision History

| Version | Change summary |
| --- | --- |
| 1.0 | Initial approved baseline generated from stakeholder decisions and architecture requirements. |

## Intended Audience

- Software engineers implementing the Raspberry Pi host stack.
- Firmware engineers implementing the ESP32 device software.
- Frontend engineers implementing host-control and public-display interfaces.
- QA engineers defining verification and acceptance tests.
- Technical stakeholders approving scope, behaviour, and delivery criteria.

# Contents

- 1. Introduction and Product Overview
- 2. Goals, Non-Goals, and Success Criteria
- 3. Stakeholders, Users, and Operating Context
- 4. Fixed Design Decisions and Constraints
- 5. System Context and Logical Architecture
- 6. Functional Requirements
- 7. Non-Functional Requirements
- 8. Detailed Workflows and State Models
- 9. Data Model and Persistence Requirements
- 10. User Interface Requirements
- 11. Device Firmware and Protocol Requirements
- 12. Game System Requirements and Catalogue Plan
- 13. Deployment, Logging, Operations, and Recovery
- 14. Privacy, Safety, and Governance
- 15. Verification and Acceptance Criteria
- Appendix A. Recommended Repository Structure
- Appendix B. Candidate Built-In Games

# 1. Introduction and Product Overview

## 1.1 Purpose

This SRS defines the complete baseline requirements for a local, in-person, hands-on electronic engineering game platform aimed at young people aged 14–18. The product is intended to make electronic engineering approachable through short, engaging, breadboard-based games in which players build simple circuits that interact with an ESP32 device and report game-relevant events to a Raspberry Pi host.

This document is normative. Where implementation choices are described as mandatory, they shall be treated as binding unless a later approved revision supersedes them.

## 1.2 Product Summary

- Host-led multiplayer game platform for in-person sessions.
- Offline operation on a Raspberry Pi without reliance on external internet or external Wi‑Fi.
- Up to 20 concurrent players, each with one ESP32-based device and one breadboard.
- Public room-facing display plus a separate host-control mode.
- 10–15 built-in games combining fast circuit setup with short, high-energy gameplay.
- Session persistence, pause/resume, save/resume later, and permanent finish/archive.
- Cumulative individual scoring across a session, with team play supported on a per-game basis.
## 1.3 Scope

In scope:

- Raspberry Pi host backend, frontend, local networking, persistence, and orchestration.
- ESP32 firmware for player devices.
- Public and host-control user interfaces.
- Session management, scoring, auditing, game lifecycle control, and archival.
- A curated built-in catalogue of games and the internal game contract used to add more.
Out of scope:

- Player interaction from phones, laptops, or tablets.
- Internet-based multiplayer, cloud hosting, or external account systems.
- No-code game authoring tools.
- Formal automated educational assessment or grading.
- Long-term player profile storage.
## 1.4 Definitions

| Term | Definition |
| --- | --- |
| Host | The Raspberry Pi running the application stack and acting as the central authority for the session. |
| Public display | The room-facing display visible to players and spectators. |
| Host-control mode | Operator interface used by the facilitator to manage the session. |
| Session | A multi-game event with registered players, cumulative scoring, and eventual archival. |
| Round | A single played game instance inside a session. |
| Test phase | The pre-game validation phase used to confirm that each player’s circuit behaves as required. |
| Archive | A finished, immutable, anonymised session record retained in SQLite. |

# 2. Goals, Non-Goals, and Success Criteria

## 2.1 Goals

- Increase interest in electronic engineering through repeated hands-on success.
- Create a format that feels social, lively, and event-ready rather than classroom-only.
- Reward practical skills such as reading a circuit diagram, building quickly, debugging, and responding accurately.
- Maintain strong host control so live sessions can adapt to mixed skill levels and unexpected faults.
- Build a software and firmware foundation that is maintainable and extensible without becoming over-engineered.
## 2.2 Non-Goals

- No requirement for remote access or online services.
- No requirement for player-owned devices.
- No requirement for automated anti-cheat beyond host supervision.
- No requirement for battery telemetry in version 1.0 of this specification.
- No requirement for drag-and-drop game authoring.
## 2.3 Product Success Criteria

- A host can run a one-hour or longer session with up to 20 players without internet access.
- Games are quick to explain, quick to build, and robust enough for repeated use.
- The system remains responsive enough that players perceive their actions as immediate.
- The host can recover from common disruptions such as a miswired circuit or temporary device disconnection.
- Historical results can be preserved without retaining identifying usernames in finished archives.
# 3. Stakeholders, Users, and Operating Context

## 3.1 Stakeholders

| Stakeholder | Interest |
| --- | --- |
| Project owner / organiser | Quality, maintainability, event suitability, long-term extensibility. |
| Host / facilitator | Smooth session control, clarity, fast intervention, confidence in diagnostics. |
| Players (14–18) | Fun, clarity, fairness, fast feedback, visible progress, social energy. |
| Developers | Clear boundaries, reproducible builds, game extensibility, low coupling. |
| Schools / clubs / event staff | Safe operation, reliable offline deployment, reusable equipment. |

## 3.2 User Classes

**Host / facilitator:**

- Creates, resumes, saves, pauses, and finishes sessions.
- Registers players and manages player-visible identity.
- Chooses games, monitors readiness, and controls transitions.
- Applies manual score changes only during intermission.
- Uses diagnostics to spot disconnected or faulty devices.
**Players:**

- Connect using the assigned ESP32 only.
- Build circuits using a breadboard and shared component bucket.
- Follow public instructions and respond through the live circuit/device.
- Participate in solo games and game-local team games.
## 3.3 Operating Context

The product shall be usable in classrooms, STEM clubs, workshops, exhibitions, and outreach events. The system shall assume in-person supervision, variable RF conditions, mixed player ability, and occasional need for host intervention.

## 3.4 Physical Context

- A single room-facing public display is present.
- The host has access to a separate control view or a separate mode switch on the same display system.
- Each player has access to one breadboard and one assigned ESP32 device.
- Additional passive components are shared from a common pool and selected per game.
# 4. Fixed Design Decisions and Constraints

| Decision Area | Locked Baseline |
| --- | --- |
| Minimum host hardware | Raspberry Pi 4 Model B |
| Maximum concurrent players | 20 |
| Player device assignment | One ESP32 per player for the whole session |
| Default ESP target | ESP32-C3 |
| Firmware toolchain | PlatformIO |
| Firmware framework | Arduino framework for ESP32 |
| Frontend | React web application hosted locally by the Pi |
| Backend | Python 3.12+ |
| Persistence | SQLite |
| Player-side connection path | ESP32 only; no direct player phone/laptop access |
| Physical build style | Breadboard only; no soldering |
| Game catalogue size | 10–15 built-in games |
| Session-level winners | Individual players only |
| Team model | Randomly generated per game; not persisted at session level |

## 4.1 Additional Constraints

- Finished sessions shall be retained indefinitely, but archived results shall not keep direct usernames.
- The host shall be able to filter games by difficulty, duration, and component type.
- Manual score changes shall be allowed only during intermissions between games.
- The public home screen shall adapt to fit as many players as possible without unreadable compression.
# 5. System Context and Logical Architecture

## 5.1 Context Overview

The Raspberry Pi is the authoritative host for the whole system. It serves the web UI, manages player sessions, stores data in SQLite, coordinates game state, and receives device events from ESP32 units over a private local network.

| Logical Component | Responsibility |
| --- | --- |
| Session Manager | Create, save, resume, pause, finish, and archive sessions. |
| Player and Device Registry | Map devices to players, track usernames, colours, state, and connectivity. |
| Game Engine | Load game definitions, run phase transitions, process events, and compute results. |
| Scoring Service | Maintain cumulative totals, per-round scores, podiums, and audit trails. |
| Persistence Service | Write live state, resumable state, archives, and audit data to SQLite. |
| Realtime Broadcaster | Push host-state and public-display updates to the frontend. |
| Host-Control UI | Provide operator workflows and intervention controls. |
| Public Display UI | Show player, game, timer, and results information to the room. |
| Firmware | Join the host network, register, report events, and present LED status states. |

## 5.2 Networking Baseline

- The Raspberry Pi shall provide or manage the local network used by the player devices.
- ESP32 devices shall connect only to the local host-managed network.
- The backend shall provide a low-latency, host-authoritative message path for device registration, liveness, and gameplay events.
- The web frontend shall receive live updates through a push-capable channel such as WebSockets.
## 5.3 Concurrency Baseline

The host backend shall use an asynchronous event loop for networking, timers, and orchestration. Thread workers may be used where blocking work or isolated background work is unavoidable, but core correctness shall not depend on a thread-per-device model. Shared state across async tasks and worker threads shall be explicitly controlled.

# 6. Functional Requirements

## 6.1 Session Management

| ID | Requirement |
| --- | --- |
| FR-001 | The system shall allow the host to create a new session. |
| FR-002 | The system shall allow the host to resume a previously saved session. |
| FR-003 | The system shall allow the host to save a session without ending it. |
| FR-004 | The system shall allow the host to pause a session. |
| FR-005 | The system shall allow the host to finish a session permanently. |
| FR-006 | Finishing a session shall make it immutable for gameplay purposes. |
| FR-007 | Finishing a session shall produce an archived record stored in SQLite. |
| FR-008 | The host shall be able to view current session state, including active game, player list, and cumulative standings. |
| FR-009 | The system shall support resuming the latest saved session after an application restart. |
| FR-010 | Only one active gameplay session shall be supported per host instance unless a later specification explicitly extends this. |

## 6.2 Player Registration and Identity

| ID | Requirement |
| --- | --- |
| FR-011 | The system shall detect newly connected player devices. |
| FR-012 | Each newly connected device shall receive a generated random username. |
| FR-013 | Each newly connected device shall receive a player colour assignment. |
| FR-014 | The host shall be able to edit usernames during a session. |
| FR-015 | The host shall be able to edit player colours during a session. |
| FR-016 | The system shall preserve a one-to-one mapping between player and assigned device for the duration of the session. |
| FR-017 | The public display shall show usernames and colours consistently. |
| FR-018 | The host-control view shall display connectivity and readiness state per player. |
| FR-019 | The system shall not maintain reusable long-term player profiles beyond session scope. |
| FR-020 | The public home screen shall adapt to the number of active players without squashing content below a readable threshold. |

## 6.3 Device Management

| ID | Requirement |
| --- | --- |
| FR-021 | The system shall support up to 20 concurrently connected devices. |
| FR-022 | The backend shall maintain device connectivity status. |
| FR-023 | The backend shall maintain a liveness timestamp or heartbeat indicator for each device. |
| FR-024 | The host shall be alerted when a known device disconnects or becomes stale. |
| FR-025 | Each device shall expose a stable device identifier for session mapping. |
| FR-026 | Firmware shall provide a status LED output. |
| FR-027 | The project-standard default status LED pin shall be GPIO4 unless overridden by board configuration. |
| FR-028 | Battery level reporting shall not be required. |
| FR-029 | Reconnect handling shall attempt to restore the existing device-player mapping where the device identity matches. |
| FR-030 | Unknown devices shall not silently overwrite an existing registered device mapping. |

## 6.4 Game Catalogue and Selection

| ID | Requirement |
| --- | --- |
| FR-031 | The system shall include 10–15 built-in games. |
| FR-032 | Each game shall define title, description, mode, difficulty, estimated duration, and required component types. |
| FR-033 | The host shall be able to browse games in any order. |
| FR-034 | The host shall be able to filter games by difficulty. |
| FR-035 | The host shall be able to filter games by duration. |
| FR-036 | The host shall be able to filter games by component type. |
| FR-037 | The system shall support solo games. |
| FR-038 | The system shall support team-based games. |
| FR-039 | Team assignments for team-based games shall be generated randomly. |
| FR-040 | Team assignments shall remain static for the lifetime of the game only. |

## 6.5 Build Instructions and Setup

| ID | Requirement |
| --- | --- |
| FR-041 | Before a game starts, the public display shall show a game overview. |
| FR-042 | The public display shall show the required component list. |
| FR-043 | The public display shall show breadboard guidance appropriate to the game. |
| FR-044 | The public display shall show a circuit diagram. |
| FR-045 | The public display shall show setup/build instructions. |
| FR-046 | The host-control view shall allow the round to enter test mode. |
| FR-047 | The host shall be able to skip directly to the main game when necessary. |
| FR-048 | The host-control view should show the selected game’s metadata before the round begins. |

## 6.6 Test Phase

| ID | Requirement |
| --- | --- |
| FR-049 | Every game shall define a test phase. |
| FR-050 | The test phase shall validate that the player’s circuit and device behaviour match the game’s expectations. |
| FR-051 | No points shall be awarded during the test phase. |
| FR-052 | The host shall be able to see pass/fail/not-tested status for each player. |
| FR-053 | The host shall be able to keep the group in test mode until issues are corrected. |
| FR-054 | The host shall be able to start the game once the host judges the group ready. |
| FR-055 | The test workflow shall be consistent across games even though the validation logic is game-specific. |

## 6.7 Live Game Control

| ID | Requirement |
| --- | --- |
| FR-056 | The host shall be able to start, pause, resume, and end a game. |
| FR-057 | The public display shall show game-state information relevant to the active round. |
| FR-058 | The backend shall process device events in near real time. |
| FR-059 | The system shall support timers and countdowns where the game requires them. |
| FR-060 | If a player’s circuit fails during gameplay, the host shall be able to pause the round to allow repair. |
| FR-061 | Pause/resume shall preserve round state unless the host explicitly restarts or cancels the round. |
| FR-062 | The host-control view shall make the current round state explicit. |
| FR-063 | Illegal round transitions shall be prevented or require explicit host override. |

## 6.8 Scoring and Results

| ID | Requirement |
| --- | --- |
| FR-064 | The system shall maintain cumulative individual session scores. |
| FR-065 | The system shall calculate per-game scores. |
| FR-066 | Games shall be able to reward speed. |
| FR-067 | Games shall be able to reward correctness. |
| FR-068 | Games shall be able to reward consistency. |
| FR-069 | Games may award additional criteria when specifically defined. |
| FR-070 | The end-of-round display shall show per-game winners and a podium. |
| FR-071 | The end-of-round display shall show the cumulative session leaderboard. |
| FR-072 | Overall winners for a session shall be individual players only. |
| FR-073 | Team results shall affect the relevant game only and shall not create a session-level team ranking. |

## 6.9 Host Score Adjustments

| ID | Requirement |
| --- | --- |
| FR-074 | The host shall be able to add points during intermission between games. |
| FR-075 | The host shall be able to remove points during intermission between games. |
| FR-076 | Manual score adjustment shall not be permitted during an active game. |
| FR-077 | Manual score adjustment shall not be permitted during the test phase. |
| FR-078 | Each manual score adjustment shall require a reason entry or reason code. |
| FR-079 | Each manual score adjustment shall be logged with timestamp, target player, delta, and reason. |
| FR-080 | Manual score changes shall affect cumulative totals. |
| FR-081 | The system should indicate in the audit log when rankings include host-applied adjustments. |

## 6.10 Persistence and Archival

| ID | Requirement |
| --- | --- |
| FR-082 | The system shall persist live and resumable session state in SQLite. |
| FR-083 | The system shall persist finished archives in SQLite. |
| FR-084 | Finished archives shall be retained indefinitely. |
| FR-085 | The system shall store session data only and shall not maintain reusable player profiles. |
| FR-086 | Live and resumable sessions may retain usernames while operationally necessary. |
| FR-087 | Finished archives shall remove or irreversibly pseudonymise usernames. |
| FR-088 | Finished archives shall preserve enough information to reconstruct standings, round history, and score events. |
| FR-089 | The system shall support immutable finish semantics distinct from ordinary save semantics. |

## 6.11 Extensibility

| ID | Requirement |
| --- | --- |
| FR-090 | New games shall be added by Python development rather than no-code configuration. |
| FR-091 | The platform shall define a common internal game interface. |
| FR-092 | Each game shall declare metadata, setup content, test logic, runtime handlers, scoring logic, and result formatting. |
| FR-093 | Game implementations shall be isolated so that adding one game does not require rewriting unrelated games. |
| FR-094 | The architecture shall leave a clear path toward a more formal plugin system in future. |

# 7. Non-Functional Requirements

## 7.1 Performance

| ID | Requirement |
| --- | --- |
| NFR-001 | The system shall support 20 concurrently connected player devices. |
| NFR-002 | Normal gameplay interactions shall feel near real time to the host and players. |
| NFR-003 | Host actions shall remain responsive while device events are being processed. |
| NFR-004 | The public display shall update smoothly enough for timed, reactive, and leaderboard-driven games. |
| NFR-005 | Blocking operations shall not freeze the core event loop or user interface. |

## 7.2 Reliability and Fault Tolerance

| ID | Requirement |
| --- | --- |
| NFR-006 | The system shall surface device disconnects and stale connections clearly. |
| NFR-007 | The system shall preserve saved sessions across normal application restarts. |
| NFR-008 | The persistence design shall minimise risk of session corruption. |
| NFR-009 | The system shall degrade gracefully when an individual device misbehaves or sends malformed data. |
| NFR-010 | The host shall be able to recover control after common faults without ending the entire session. |

## 7.3 Usability

| ID | Requirement |
| --- | --- |
| NFR-011 | The public display shall remain legible from a room-facing viewing distance. |
| NFR-012 | The host-control UI shall support efficient operation under live-event pressure. |
| NFR-013 | Instructions shall be clear enough for mixed-skill teenagers to follow with host supervision. |
| NFR-014 | The UI shall remain usable from small to maximum player counts. |
| NFR-015 | The product shall prefer clarity, hierarchy, and fast comprehension over dense screen layouts. |

## 7.4 Maintainability

| ID | Requirement |
| --- | --- |
| NFR-016 | The codebase shall separate host backend, host frontend, firmware, shared protocol, and documentation concerns. |
| NFR-017 | Board-specific firmware configuration shall be isolated from common gameplay logic. |
| NFR-018 | New games shall be addable without modifying core infrastructure beyond defined integration points. |
| NFR-019 | Protocol messages and key domain models shall be documented. |
| NFR-020 | Builds for host software and firmware shall be reproducible. |

## 7.5 Privacy and Governance

| ID | Requirement |
| --- | --- |
| NFR-021 | The system shall minimise stored personal data. |
| NFR-022 | Finished archives shall not retain direct usernames. |
| NFR-023 | Administrative score and session actions shall be auditable. |
| NFR-024 | The platform shall operate without cloud dependence. |
| NFR-025 | The system shall preserve only the data required for session operation and historical result retention. |

# 8. Detailed Workflows and State Models

## 8.1 Session Workflow

- Create or resume session.
- Wait for player devices to register.
- Review generated usernames and colours; edit if required.
- Select a game and show build/setup screen.
- Move to test phase and validate player circuits.
- Start gameplay.
- Show game results and cumulative leaderboard.
- Apply optional manual point changes during intermission.
- Select next game or save/pause/finish session.
## 8.2 Round State Model

| State | Meaning |
| --- | --- |
| Selected | A game has been chosen but setup is not yet being shown. |
| Build | Players are assembling the required circuit. |
| Test | The host is validating that circuits work as required. |
| Ready | The group is ready to start, pending host confirmation. |
| Live | The game is in progress and scoring events may occur. |
| Paused | The round is temporarily halted while preserving state. |
| Completed | The live phase has ended and scores have been finalised. |
| Results | Per-game podium and cumulative leaderboard are being shown. |
| Intermission | The host may prepare for the next game and adjust points if necessary. |

## 8.3 Device Lifecycle

- Boot and join host-managed network.
- Register identity and firmware metadata.
- Receive player assignment context.
- Publish heartbeat/liveness signals.
- Enter idle, test, live, paused, or error state as directed by the host application.
- Reconnect using the same stable identity if the connection is interrupted.
## 8.4 Team Allocation Rules

- Team allocation applies only when the selected game is team-based.
- Teams shall be generated randomly for that round.
- Once generated, the membership shall remain fixed until the round ends.
- At the end of the round, team structure shall be discarded except as historical round data.
# 9. Data Model and Persistence Requirements

## 9.1 Persistence Baseline

SQLite is the authoritative persistence store. It shall hold live session state, resumable sessions, finished archives, score events, audit events, and sufficient round history to reconstruct results.

## 9.2 Core Logical Entities

| Entity | Purpose |
| --- | --- |
| Session | Top-level record for a live or resumable session. |
| PlayerSession | Player identity within a session, including display username and colour. |
| Device | Registered hardware identity and current connection metadata. |
| GameRound | One played instance of a game inside a session. |
| GameTeam | Round-local team allocation and team score summary where relevant. |
| ScoreEvent | System- or host-generated score delta with audit trail. |
| AuditEvent | Administrative and lifecycle actions affecting session history. |
| SessionArchive | Finished immutable historical record in anonymised form. |

## 9.3 Minimum Field Expectations

| Entity | Minimum fields |
| --- | --- |
| Session | id, created_at, updated_at, status, current_round_id |
| PlayerSession | id, session_id, current_username, colour, device_id, cumulative_score, connectivity_state |
| Device | id, stable_device_key, firmware_version, board_target, last_seen_at, connection_state |
| GameRound | id, session_id, game_id, state, started_at, ended_at, results_payload |
| ScoreEvent | id, session_id, round_id, player_id, delta, source_type, reason, created_at |
| AuditEvent | id, session_id, action_type, actor_type, payload_summary, created_at |
| SessionArchive | id, finished_at, anonymised_payload, retention_state |

## 9.4 Archive Anonymisation Rules

- Finished archives shall remove direct usernames from the historical representation.
- Archive player references shall use archive-local anonymous labels or irreversible pseudonyms.
- The archive shall preserve standings, round order, score deltas, and game results.
- No reusable cross-session player identity shall be retained.
# 10. User Interface Requirements

## 10.1 Host-Control Mode

| ID | Requirement |
| --- | --- |
| UI-001 | The host-control UI shall present a dashboard summarising session state, player count, and connectivity. |
| UI-002 | The host-control UI shall provide a player list including username, colour, device state, and test/readiness status. |
| UI-003 | The host-control UI shall allow username and colour editing. |
| UI-004 | The host-control UI shall provide game browsing, filtering, and selection. |
| UI-005 | The host-control UI shall expose controls for test, start, pause, resume, end, save, and finish. |
| UI-006 | The host-control UI shall expose intermission-only score-adjustment controls. |
| UI-007 | Destructive actions such as Finish Session shall require explicit confirmation. |
| UI-008 | The host-control UI shall surface connectivity and fault information without requiring developer tools. |

## 10.2 Public Display Mode

| ID | Requirement |
| --- | --- |
| UI-009 | The public display shall have a lobby/home view showing active players. |
| UI-010 | The home view shall use a dynamic tile layout that fits as many players as possible without becoming unreadable. |
| UI-011 | When all players cannot fit at minimum readable size, the display shall use paging, rotation, or another controlled overflow mechanism. |
| UI-012 | The build view shall show game title, objective, required parts, breadboard guidance, and circuit diagram. |
| UI-013 | The test view shall show status indicators appropriate to the game and player readiness. |
| UI-014 | The live view shall show timers, prompts, or score indicators required by the active game. |
| UI-015 | The results view shall show round podium and cumulative session leaderboard. |
| UI-016 | Player usernames and colours shall remain consistent across screens. |

# 11. Device Firmware and Protocol Requirements

## 11.1 Firmware Stack

- The firmware project shall use PlatformIO as the build system and project manager.
- The firmware shall use the Arduino framework for ESP32.
- The default build target shall be ESP32-C3.
- Alternative supported ESP32-family targets shall be selectable through PlatformIO environments with limited board-specific adaptation.
## 11.2 Firmware Architecture Requirements

| ID | Requirement |
| --- | --- |
| FW-001 | Common application logic shall be separated from board-specific configuration. |
| FW-002 | Pin mappings and target-specific feature switches shall be isolated in target configuration. |
| FW-003 | The firmware shall implement device registration, liveness, state reception, and gameplay event publication. |
| FW-004 | The firmware shall provide LED status indications for boot, connecting, connected, test/fault, and live-state conditions. |
| FW-005 | The firmware shall expose build or version metadata where practical. |
| FW-006 | The firmware shall be structured so that changing target board does not require widespread source rewrites. |

## 11.3 Internal Protocol Requirements

| ID | Requirement |
| --- | --- |
| IF-001 | Protocol messages shall be versioned. |
| IF-002 | The protocol shall support registration, heartbeat, state transition, event reporting, and error signalling. |
| IF-003 | Message validation failures shall be handled gracefully. |
| IF-004 | Malformed device messages shall not destabilise the host session. |
| IF-005 | Shared message schemas shall be documented in the repository. |
| IF-006 | The protocol shall allow the backend to correlate messages with a stable device identity. |

# 12. Game System Requirements and Catalogue Plan

## 12.1 Game Contract

Every game implementation shall declare the following at minimum:

- unique identifier and title;
- description and objective;
- supported mode: solo, team, or both;
- difficulty classification;
- estimated duration classification;
- required component types;
- breadboard guidance;
- setup/build instructions;
- circuit diagram asset references;
- test-phase logic;
- runtime event handling logic;
- scoring logic;
- result transformation for the public and host UIs.
## 12.2 Game Design Requirements

- Games shall be quick to set up relative to a one-hour session format.
- Games shall use cheap and simple components from a shared parts bucket.
- Games shall be understandable by the target age group with host supervision.
- The catalogue shall include a mix of competitive and cooperative/team games.
- The architecture shall simplify game creation for Python developers without becoming a block-based game engine.
## 12.3 Catalogue Planning Categories

| Category | Purpose |
| --- | --- |
| Reaction and timing | Fast-response games with buttons and LEDs. |
| Quiz / buzzer | Speed-to-answer or hosted trivia rounds. |
| Analog control | Value-matching or stability games using potentiometers or sensors. |
| Pattern and memory | Sequence-following or encoding/decoding rounds. |
| Team coordination | Cooperative games with shared objective or relay-style play. |
| Engineering challenge | Build-quality, troubleshooting, or optimisation rounds where host judgement can add bonus points. |

# 13. Deployment, Logging, Operations, and Recovery

## 13.1 Deployment

- The host application shall run locally on Raspberry Pi 4 Model B or better.
- The deployment shall function without internet access.
- Host software installation shall be reproducible.
- Firmware builds shall be reproducible through PlatformIO configuration.
## 13.2 Logging and Diagnostics

| ID | Requirement |
| --- | --- |
| OP-001 | The backend shall log session lifecycle events such as create, save, pause, resume, and finish. |
| OP-002 | The backend shall log connectivity transitions and stale-device events. |
| OP-003 | The backend shall log manual score adjustments and other administrative interventions. |
| OP-004 | Diagnostics visible to the host shall be sufficient for live troubleshooting without requiring terminal access. |
| OP-005 | Logs should be structured enough to support post-session debugging. |

## 13.3 Recovery Expectations

- A saved session shall survive normal restarts.
- A finished archive shall survive normal restarts.
- Recovery workflow shall prioritise restoration of the latest consistent saved session state.
- The host shall be able to distinguish a live resumable session from a permanently finished archive.
# 14. Privacy, Safety, and Governance

## 14.1 Privacy Baseline

- The system shall minimise retained player-identifying data.
- Usernames shall be treated as potentially identifying while live or resumable sessions exist.
- Finished archives shall not retain direct usernames.
- The system shall store session data only and shall not maintain reusable player profiles.
## 14.2 Physical and Electrical Safety

- Games shall be designed for breadboard-only, low-risk electronic activity.
- No game shall require hazardous voltages or unsafe assembly practices.
- The system shall assume host supervision for physical setup, troubleshooting, and safe use of components.
## 14.3 Governance and Auditability

- Manual administrative score changes shall be auditable.
- Finish Session shall create a clearly distinguishable immutable record.
- The persistence design should allow later policy additions without major redesign.
# 15. Verification and Acceptance Criteria

## 15.1 Product Acceptance

| ID | Requirement |
| --- | --- |
| AC-001 | A host can create a session and register up to 20 devices without internet access. |
| AC-002 | Each connected device receives a generated username and colour and appears on the public display. |
| AC-003 | The host can edit usernames and colours. |
| AC-004 | A selected game shows required parts, breadboard guidance, circuit diagram, and setup instructions. |
| AC-005 | The host can run test mode and see pass/fail/readiness status. |
| AC-006 | The host can start, pause, resume, and end a round. |
| AC-007 | End-of-round screens show a podium and cumulative individual leaderboard. |
| AC-008 | The host can apply manual score changes only during intermission. |
| AC-009 | A session can be saved, resumed, and finally finished. |
| AC-010 | A finished session remains archived and anonymised in SQLite. |

## 15.2 Technical Acceptance

| ID | Requirement |
| --- | --- |
| AC-011 | The host software runs on Raspberry Pi 4 Model B or better. |
| AC-012 | Persistence uses SQLite. |
| AC-013 | Firmware builds with PlatformIO using the Arduino framework for ESP32. |
| AC-014 | The default firmware target is ESP32-C3. |
| AC-015 | Retargeting to another supported ESP32-family board can be performed through PlatformIO environment selection and limited board-specific adaptation rather than major source rewrites. |

# Appendix A. Recommended Repository Structure

| Path | Purpose |
| --- | --- |
| host/backend/ | Python API, orchestration, persistence, game engine, device service. |
| host/frontend/ | React host-control and public-display UI code. |
| firmware/ | PlatformIO project for ESP32 device firmware. |
| shared/ | Shared schemas, protocol definitions, constants, and documentation. |
| docs/ | Architecture notes, protocol docs, game specifications, and deployment guidance. |

# Appendix B. Candidate Built-In Games

The final catalogue shall include 10–15 built-in games. The table below is a planning baseline rather than a mandatory exact list; titles may change while preserving category coverage.

| Game | Mode | Core parts | Length | Primary scoring focus |
| --- | --- | --- | --- | --- |
| Reaction Rush | Solo | Button, LED | Very short | Reaction speed |
| Fastest Finger Quiz | Solo | Button | Short | Speed + correctness |
| Lock the Dial | Solo | Potentiometer | Short | Accuracy + stability |
| Hold the Zone | Solo | Potentiometer or LDR | Short | Consistency |
| Signal Match | Solo | Potentiometer, LED | Short | Accuracy + timing |
| Memory Pulse | Solo | Buttons, LEDs | Medium | Memory + correctness |
| Binary Entry | Solo | Switches or buttons | Short | Correctness |
| Beat the Buzz | Solo | Button, buzzer/LED | Very short | Reaction + repeatability |
| Team Average | Team | Potentiometers | Short | Coordination + consistency |
| Relay Build | Team | Mixed simple parts | Medium | Collaboration + speed |
| Sync Strike | Team | Buttons | Very short | Coordination |
| Fault Finder | Solo or Team | Host-selected parts | Medium | Debugging + engineering judgement |

*End of document.*

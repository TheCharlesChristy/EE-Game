"""
Protocol constants shared across backend components.

These constants are the single source of truth for message type names and
protocol versioning. All backend code must import from here rather than
hardcoding strings.
"""

PROTOCOL_VERSION = "1"

# Device -> Backend message types
MSG_REGISTER = "register"
MSG_HEARTBEAT = "heartbeat"
MSG_EVENT = "event"
MSG_TEST_EVENT = "test_event"

# Backend -> Frontend message types
MSG_STATE_UPDATE = "state_update"
MSG_STATE_TRANSITION = "state_transition"
MSG_RESULT = "result"
MSG_DEVICE_LIST = "device_list"
MSG_ERROR = "error"

# Connection state values
CONN_CONNECTED = "connected"
CONN_STALE = "stale"
CONN_DISCONNECTED = "disconnected"

# Device LED state names (mirrors firmware expectations)
LED_BOOT = "boot"
LED_CONNECTING = "connecting"
LED_CONNECTED = "connected"
LED_TEST_FAULT = "test_fault"
LED_LIVE = "live"

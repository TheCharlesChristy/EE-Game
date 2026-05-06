"""
Local mirror of shared/constants/protocol.py.
Values must stay in sync with that file.
SRS reference: IF-001.
"""

PROTOCOL_VERSION = "1"

MSG_REGISTER = "register"
MSG_HEARTBEAT = "heartbeat"
MSG_EVENT = "event"
MSG_TEST_EVENT = "test_event"
MSG_STATE_UPDATE = "state_update"
MSG_STATE_TRANSITION = "state_transition"
MSG_RESULT = "result"
MSG_DEVICE_LIST = "device_list"
MSG_ERROR = "error"

CONN_CONNECTED = "connected"
CONN_STALE = "stale"
CONN_DISCONNECTED = "disconnected"

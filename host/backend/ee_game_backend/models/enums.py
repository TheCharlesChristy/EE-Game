from enum import StrEnum


class ConnectionState(StrEnum):
    CONNECTED = "connected"
    STALE = "stale"
    DISCONNECTED = "disconnected"


class MessageType(StrEnum):
    # Device -> Backend
    REGISTER = "register"
    HEARTBEAT = "heartbeat"
    # Backend -> Frontend
    STATE_UPDATE = "state_update"
    DEVICE_LIST = "device_list"
    ERROR = "error"

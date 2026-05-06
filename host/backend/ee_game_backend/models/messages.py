from pydantic import BaseModel, Field

from .enums import MessageType


class MessageEnvelope(BaseModel):
    """Base envelope for all WebSocket messages."""

    version: str = Field(..., pattern=r"^[0-9]+$")
    type: str
    device_id: str | None = None
    payload: dict = Field(default_factory=dict)


class RegisterPayload(BaseModel):
    firmware_version: str
    board_target: str


class RegisterMessage(BaseModel):
    version: str
    type: MessageType
    device_id: str = Field(..., min_length=1)
    payload: RegisterPayload


class HeartbeatPayload(BaseModel):
    timestamp_ms: int = Field(..., ge=0)


class HeartbeatMessage(BaseModel):
    version: str
    type: MessageType
    device_id: str = Field(..., min_length=1)
    payload: HeartbeatPayload


class ErrorPayload(BaseModel):
    code: str
    message: str


class ErrorMessage(BaseModel):
    version: str = "1"
    type: MessageType = MessageType.ERROR
    payload: ErrorPayload

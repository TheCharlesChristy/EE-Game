/**
 * TypeScript types mirroring the JSON schemas in shared/schemas/v1/.
 * The backend sends these over the WebSocket connection.
 */

export type MessageType =
  | 'register'
  | 'heartbeat'
  | 'event'
  | 'test_event'
  | 'state_transition'
  | 'result'
  | 'state_update'
  | 'device_list'
  | 'error';

export interface MessageEnvelope {
  version: string;
  type: MessageType;
  device_id?: string;
  payload: Record<string, unknown>;
}

export interface StateUpdatePayload {
  event: string;
  data: Record<string, unknown>;
}

export interface DeviceListPayload {
  devices: DeviceInfo[];
}

export interface DeviceInfo {
  device_id: string;
  connection_state: 'connected' | 'stale' | 'disconnected';
  firmware_version?: string;
  board_target?: string;
  last_seen_at?: string;
}

export interface ErrorPayload {
  code: string;
  message: string;
}

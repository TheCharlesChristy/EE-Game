import { useCallback, useEffect, useRef, useState } from 'react';
import { MessageEnvelope } from '../types/messages';

interface UseWebSocketReturn {
  readyState: number;
  lastMessage: MessageEnvelope | null;
  sendMessage: (msg: Record<string, unknown>) => void;
}

const BACKOFF_BASE_MS = 1000;
const BACKOFF_MAX_MS = 30_000;

export function useWebSocket(url: string | null): UseWebSocketReturn {
  const [readyState, setReadyState] = useState<number>(WebSocket.CLOSED);
  const [lastMessage, setLastMessage] = useState<MessageEnvelope | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const attemptRef = useRef<number>(0);
  const unmountedRef = useRef<boolean>(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  // Store connect in a ref so the onclose handler always calls the current version
  const connectRef = useRef<(() => void) | null>(null);

  const connect = useCallback(() => {
    if (unmountedRef.current || url === null) return;

    const ws = new WebSocket(url);
    wsRef.current = ws;
    setReadyState(WebSocket.CONNECTING);

    ws.onopen = () => {
      if (unmountedRef.current) {
        ws.close();
        return;
      }
      console.info(`[useWebSocket] Connection opened: ${url}`);
      attemptRef.current = 0;
      setReadyState(WebSocket.OPEN);
    };

    ws.onmessage = (event: MessageEvent) => {
      if (unmountedRef.current) return;
      const raw: unknown = event.data;
      if (typeof raw !== 'string') {
        console.warn('[useWebSocket] Received non-string message; ignoring.', raw);
        return;
      }
      let parsed: unknown;
      try {
        parsed = JSON.parse(raw);
      } catch {
        console.warn('[useWebSocket] Received non-JSON message; ignoring.', raw);
        return;
      }
      // Narrow to MessageEnvelope shape
      if (
        parsed !== null &&
        typeof parsed === 'object' &&
        'version' in parsed &&
        'type' in parsed &&
        'payload' in parsed
      ) {
        setLastMessage(parsed as MessageEnvelope);
      } else {
        console.warn('[useWebSocket] Received message with unexpected shape; ignoring.', parsed);
      }
    };

    ws.onclose = (event: CloseEvent) => {
      if (unmountedRef.current) return;
      console.info(`[useWebSocket] Connection closed (code=${event.code}): ${url}`);
      setReadyState(WebSocket.CLOSED);
      wsRef.current = null;

      // Exponential backoff reconnect
      const delay = Math.min(
        BACKOFF_BASE_MS * Math.pow(2, attemptRef.current),
        BACKOFF_MAX_MS,
      );
      attemptRef.current += 1;
      timerRef.current = setTimeout(() => {
        if (!unmountedRef.current) {
          connectRef.current?.();
        }
      }, delay);
    };

    ws.onerror = () => {
      console.warn(`[useWebSocket] Connection error: ${url}`);
      // onclose will fire after onerror and handle reconnect
    };
  }, [url]);

  // Keep the ref up to date with the latest connect function
  connectRef.current = connect;

  useEffect(() => {
    unmountedRef.current = false;

    if (url === null) {
      setReadyState(WebSocket.CLOSED);
      return;
    }

    connect();

    return () => {
      unmountedRef.current = true;
      if (timerRef.current !== null) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
      if (wsRef.current !== null) {
        wsRef.current.onclose = null; // prevent reconnect on intentional close
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [url, connect]);

  const sendMessage = useCallback((msg: Record<string, unknown>) => {
    if (wsRef.current !== null && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg));
    } else {
      console.warn('[useWebSocket] Cannot send: WebSocket is not open.', msg);
    }
  }, []);

  return { readyState, lastMessage, sendMessage };
}

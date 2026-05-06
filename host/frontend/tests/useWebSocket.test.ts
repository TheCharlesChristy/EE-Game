import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useWebSocket } from '../src/hooks/useWebSocket';

// ---------------------------------------------------------------------------
// WebSocket mock
// ---------------------------------------------------------------------------

interface MockWebSocketInstance {
  url: string;
  readyState: number;
  onopen: ((event: Event) => void) | null;
  onmessage: ((event: MessageEvent) => void) | null;
  onclose: ((event: CloseEvent) => void) | null;
  onerror: ((event: Event) => void) | null;
  send: ReturnType<typeof vi.fn>;
  close: ReturnType<typeof vi.fn>;
}

let lastMockWs: MockWebSocketInstance | null = null;

const MockWebSocket = vi.fn(function (url: string): MockWebSocketInstance {
  const instance: MockWebSocketInstance = {
    url,
    readyState: 0, // CONNECTING
    onopen: null,
    onmessage: null,
    onclose: null,
    onerror: null,
    send: vi.fn(),
    close: vi.fn(),
  };
  lastMockWs = instance;
  return instance;
}) as unknown as typeof WebSocket;

// Attach static constants
(MockWebSocket as unknown as Record<string, number>).CONNECTING = 0;
(MockWebSocket as unknown as Record<string, number>).OPEN = 1;
(MockWebSocket as unknown as Record<string, number>).CLOSING = 2;
(MockWebSocket as unknown as Record<string, number>).CLOSED = 3;

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('useWebSocket', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    lastMockWs = null;
    vi.stubGlobal('WebSocket', MockWebSocket);
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  it('when url is null, readyState is CLOSED (3) and no WebSocket is created', () => {
    const { result } = renderHook(() => useWebSocket(null));

    expect(result.current.readyState).toBe(3);
    expect(MockWebSocket).not.toHaveBeenCalled();
    expect(lastMockWs).toBeNull();
  });

  it('sendMessage is a stable function reference across re-renders', () => {
    const { result, rerender } = renderHook(() => useWebSocket('ws://localhost:8000/ws/frontend'));

    const firstRef = result.current.sendMessage;
    rerender();
    const secondRef = result.current.sendMessage;

    expect(firstRef).toBe(secondRef);
  });

  it('non-JSON incoming text logs console.warn and does not update lastMessage', () => {
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => undefined);

    const { result } = renderHook(() => useWebSocket('ws://localhost:8000/ws/frontend'));

    // Simulate connection open
    act(() => {
      if (lastMockWs?.onopen) {
        lastMockWs.onopen(new Event('open'));
      }
    });

    expect(result.current.lastMessage).toBeNull();

    // Simulate non-JSON message
    act(() => {
      if (lastMockWs?.onmessage) {
        lastMockWs.onmessage(new MessageEvent('message', { data: 'not valid json {{{}' }));
      }
    });

    expect(warnSpy).toHaveBeenCalled();
    expect(result.current.lastMessage).toBeNull();

    warnSpy.mockRestore();
  });
});

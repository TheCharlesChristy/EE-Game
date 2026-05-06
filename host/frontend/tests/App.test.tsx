import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { App } from '../src/App';

// ---------------------------------------------------------------------------
// Stub WebSocket globally so the hook does not throw in jsdom
// ---------------------------------------------------------------------------

const MockWebSocket = vi.fn(function () {
  return {
    readyState: 0,
    onopen: null,
    onmessage: null,
    onclose: null,
    onerror: null,
    send: vi.fn(),
    close: vi.fn(),
  };
}) as unknown as typeof WebSocket;

(MockWebSocket as unknown as Record<string, number>).CONNECTING = 0;
(MockWebSocket as unknown as Record<string, number>).OPEN = 1;
(MockWebSocket as unknown as Record<string, number>).CLOSING = 2;
(MockWebSocket as unknown as Record<string, number>).CLOSED = 3;

// ---------------------------------------------------------------------------
// Helper: render App with a given URL path
// ---------------------------------------------------------------------------

function renderAtPath(path: string) {
  window.history.pushState({}, '', path);
  return render(<App />);
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('App routing', () => {
  beforeEach(() => {
    vi.stubGlobal('WebSocket', MockWebSocket);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  it('navigating to /display renders an <h1> containing "EE Game"', () => {
    renderAtPath('/display');
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('EE Game');
  });

  it('navigating to /host renders an <h1> containing "Host Control"', () => {
    renderAtPath('/host');
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Host Control');
  });

  it('an unknown path renders the NotFound component with "404" in the heading', () => {
    renderAtPath('/some/unknown/path');
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('404');
  });
});

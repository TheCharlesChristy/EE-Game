interface StatusBadgeProps {
  readyState: number;
}

const STATE_LABELS: Record<number, string> = {
  0: 'Connecting…',
  1: 'Connected',
  2: 'Closing…',
  3: 'Disconnected',
};

const STATE_COLORS: Record<number, string> = {
  0: '#f59e0b',
  1: '#22c55e',
  2: '#f59e0b',
  3: '#ef4444',
};

/**
 * Visual indicator of WebSocket connection state.
 * Accessible: uses role="status" and aria-label.
 */
export function StatusBadge({ readyState }: StatusBadgeProps) {
  const label = STATE_LABELS[readyState] ?? 'Unknown';
  const color = STATE_COLORS[readyState] ?? '#6b7280';
  return (
    <span
      role="status"
      aria-label={`Connection status: ${label}`}
      style={{ color, fontWeight: 'bold' }}
    >
      ● {label}
    </span>
  );
}

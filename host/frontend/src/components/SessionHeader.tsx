import { StatusBadge } from './StatusBadge';
import { SessionSummary } from '../api/client';

interface SessionHeaderProps {
  readyState: number;
  session: SessionSummary | null;
}

export function SessionHeader({ readyState, session }: SessionHeaderProps) {
  return (
    <header className="session-header">
      <div>
        <p className="eyebrow">EE-Game Control</p>
        <h1>Host Control</h1>
      </div>
      <div className="header-metrics" aria-label="Session summary">
        <StatusBadge readyState={readyState} />
        <span>{session?.status ?? 'no session'}</span>
        <span>{session?.active_game ?? 'no game'}</span>
      </div>
    </header>
  );
}

import { CSSProperties } from 'react';

export function TimerRing({ remainingMs, totalMs }: { remainingMs: number; totalMs: number }) {
  const pct = totalMs > 0 ? Math.max(0, Math.min(100, (remainingMs / totalMs) * 100)) : 0;
  const seconds = Math.ceil(remainingMs / 1000);
  return (
    <div className="timer-ring" style={{ '--pct': `${pct}%` } as CSSProperties}>
      <strong>{seconds}</strong>
      <span>sec</span>
    </div>
  );
}

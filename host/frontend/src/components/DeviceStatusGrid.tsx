import { Player } from '../api/client';

export function DeviceStatusGrid({ players }: { players: Player[] }) {
  const connected = players.filter((p) => p.connection_state === 'connected').length;
  const stale = players.filter((p) => p.connection_state === 'stale').length;
  const disconnected = players.filter((p) => p.connection_state === 'disconnected').length;
  return (
    <section className="metric-grid" aria-label="Device status">
      <div><strong>{players.length}</strong><span>registered</span></div>
      <div><strong>{connected}</strong><span>connected</span></div>
      <div><strong>{stale}</strong><span>stale</span></div>
      <div><strong>{disconnected}</strong><span>offline</span></div>
    </section>
  );
}

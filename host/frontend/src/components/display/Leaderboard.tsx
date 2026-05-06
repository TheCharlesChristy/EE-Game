import { Standing } from '../../api/client';

export function Leaderboard({ standings }: { standings: Standing[] }) {
  if (standings.length === 0) return <p className="empty">No scores yet.</p>;
  return (
    <ol className="leaderboard">
      {standings.map((standing) => (
        <li key={standing.player_id}>
          <span className="player-swatch" style={{ backgroundColor: standing.colour }} aria-hidden="true" />
          <span>{standing.username}</span>
          <strong>{standing.score}</strong>
        </li>
      ))}
    </ol>
  );
}

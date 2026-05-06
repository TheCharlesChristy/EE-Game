import { Player } from '../api/client';

interface PlayerCardProps {
  player: Player;
  onRename?: (username: string) => void;
}

export function PlayerCard({ player, onRename }: PlayerCardProps) {
  return (
    <article className="player-card">
      <span className="player-swatch" style={{ backgroundColor: player.colour }} aria-hidden="true" />
      <div>
        <strong>{player.username}</strong>
        <p>{player.device_id}</p>
      </div>
      <span className={`status-pill ${player.connection_state}`}>{player.connection_state}</span>
      {onRename && (
        <button
          type="button"
          className="secondary compact"
          onClick={() => {
            const next = window.prompt('Player name', player.username);
            if (next) onRename(next);
          }}
        >
          Rename
        </button>
      )}
    </article>
  );
}

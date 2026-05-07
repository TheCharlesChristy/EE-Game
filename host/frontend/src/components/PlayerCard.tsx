import { useState } from 'react';
import { Player } from '../api/client';

interface PlayerCardProps {
  player: Player;
  onRename?: (username: string) => void;
}

export function PlayerCard({ player, onRename }: PlayerCardProps) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState('');

  return (
    <article className="player-card">
      <span className="player-swatch" style={{ backgroundColor: player.colour }} aria-hidden="true" />
      <div>
        {editing ? (
          <input
            autoFocus
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                if (draft.trim()) { onRename?.(draft.trim()); }
                setEditing(false);
              } else if (e.key === 'Escape') {
                setEditing(false);
              }
            }}
            onBlur={() => {
              if (draft.trim() && draft.trim() !== player.username) { onRename?.(draft.trim()); }
              setEditing(false);
            }}
          />
        ) : (
          <strong>{player.username}</strong>
        )}
        <p>{player.device_id}</p>
      </div>
      <span className={`status-pill ${player.connection_state}`}>{player.connection_state}</span>
      {onRename && (
        <button
          type="button"
          className="secondary compact"
          onClick={() => {
            setDraft(player.username);
            setEditing(true);
          }}
        >
          Rename
        </button>
      )}
    </article>
  );
}

import { Player } from '../../api/client';

export function PlayerTile({ player }: { player: Player }) {
  return (
    <article className={`player-tile ${player.connection_state}`}>
      <span className="player-swatch" style={{ backgroundColor: player.colour }} aria-hidden="true" />
      <strong>{player.username}</strong>
      <span>{player.connection_state}</span>
    </article>
  );
}

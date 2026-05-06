import { PlayerTile } from '../../components/display/PlayerTile';
import { useAppState } from '../../state/store';

export function DisplayLobby() {
  const { players } = useAppState();
  return (
    <section className="display-stage">
      <h1>Lobby</h1>
      <div className="display-player-grid">
        {players.map((player) => <PlayerTile key={player.player_id} player={player} />)}
      </div>
    </section>
  );
}

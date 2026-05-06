import { DeviceStatusGrid } from '../../components/DeviceStatusGrid';
import { PlayerCard } from '../../components/PlayerCard';
import { useAppState } from '../../state/store';

export function Lobby() {
  const { players, session, actions } = useAppState();
  return (
    <section className="page-band">
      <div className="section-title">
        <h2>Lobby</h2>
        <p>{session?.session_id ? 'Devices join here before round selection.' : 'Create a session to accept devices.'}</p>
      </div>
      <DeviceStatusGrid players={players} />
      <div className="toolbar">
        {!session?.session_id && <button type="button" onClick={actions.createSession}>Create Session</button>}
        {!session?.session_id && <button type="button" className="secondary" onClick={actions.resumeSession}>Resume</button>}
        {session?.session_id && <button type="button" className="secondary" onClick={actions.saveSession}>Save</button>}
        {session?.status === 'active' && <button type="button" className="secondary" onClick={actions.pauseSession}>Pause</button>}
      </div>
      <div className="player-grid">
        {players.map((player) => (
          <PlayerCard
            key={player.player_id}
            player={player}
            onRename={(username) => actions.updatePlayer(player.player_id, { username })}
          />
        ))}
      </div>
    </section>
  );
}

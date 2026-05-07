import { useState } from 'react';
import { useAppState } from '../../state/store';

export function Intermission() {
  const { players, actions } = useAppState();
  const [playerId, setPlayerId] = useState('');
  const [delta, setDelta] = useState(0);
  const [reason, setReason] = useState('');
  return (
    <section className="page-band">
      <div className="section-title">
        <h2>Intermission</h2>
        <p>Manual adjustments are audited and available only in this phase.</p>
      </div>
      <form
        className="adjust-form"
        onSubmit={(event) => {
          event.preventDefault();
          if (playerId && reason && delta !== 0) actions.adjustScore(playerId, delta, reason);
        }}
      >
        <select value={playerId} onChange={(event) => setPlayerId(event.target.value)} aria-label="Player">
          <option value="">Select player</option>
          {players.map((player) => <option key={player.player_id} value={player.player_id}>{player.username}</option>)}
        </select>
        <input type="number" value={delta} onChange={(event) => setDelta(Number(event.target.value))} aria-label="Score delta" />
        <input value={reason} onChange={(event) => setReason(event.target.value)} placeholder="Reason" aria-label="Reason" />
        <button type="submit">Apply</button>
      </form>
    </section>
  );
}

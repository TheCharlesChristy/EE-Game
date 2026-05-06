import { useAppState } from '../../state/store';

export function Test() {
  const { players, round } = useAppState();
  const results = round?.test_results ?? {};
  return (
    <section className="display-stage">
      <h1>Test</h1>
      <div className="display-player-grid">
        {players.map((player) => {
          const result = results[player.player_id];
          return (
            <article key={player.player_id} className={`player-tile ${result?.passed ? 'connected' : ''}`}>
              <span className="player-swatch" style={{ backgroundColor: player.colour }} aria-hidden="true" />
              <strong>{player.username}</strong>
              <span>{result?.passed ? 'passed' : 'waiting'}</span>
            </article>
          );
        })}
      </div>
    </section>
  );
}

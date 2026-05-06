import { useAppState } from '../../state/store';

export function Catalogue() {
  const { games, round, actions } = useAppState();
  return (
    <section className="page-band">
      <div className="section-title">
        <h2>Catalogue</h2>
        <p>{games.length} built-in games available.</p>
      </div>
      <div className="catalogue-grid">
        {games.map((game) => (
          <article key={game.id} className={round?.game_id === game.id ? 'selected-card' : ''}>
            <div className="card-topline">
              <span>{game.category}</span>
              {game.team_capable && <span>team</span>}
            </div>
            <h3>{game.title}</h3>
            <p>{game.summary}</p>
            <dl>
              <div><dt>Players</dt><dd>{game.min_players}-{game.max_players}</dd></div>
              <div><dt>Time</dt><dd>{game.estimated_seconds}s</dd></div>
            </dl>
            <button type="button" onClick={() => actions.selectRound(game.id)}>Select</button>
          </article>
        ))}
      </div>
    </section>
  );
}

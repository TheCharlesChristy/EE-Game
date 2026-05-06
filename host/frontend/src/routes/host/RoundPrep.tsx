import { RoundPhase } from '../../api/client';
import { useAppState } from '../../state/store';

const nextPhase: Record<string, string> = {
  selected: 'build',
  build: 'test',
  test: 'ready',
  ready: 'live',
};

export function RoundPrep() {
  const { games, round, actions } = useAppState();
  const game = games.find((item) => item.id === round?.game_id);
  if (!round || !game) {
    return <section className="page-band"><h2>Round Prep</h2><p className="empty">Select a game first.</p></section>;
  }
  const phase = round.phase;
  const target = nextPhase[phase];
  return (
    <section className="page-band two-column">
      <div>
        <div className="section-title">
          <h2>{game.title}</h2>
          <p>{phase}</p>
        </div>
        <h3>Materials</h3>
        <ul className="check-list">
          {game.materials.map((item) => <li key={item}>{item}</li>)}
        </ul>
      </div>
      <div>
        <h3>Build Steps</h3>
        <ol className="step-list">
          {game.build_instructions.map((step) => <li key={step}>{step}</li>)}
        </ol>
        <div className="toolbar">
          {target && <button type="button" onClick={() => actions.transitionRound(target as RoundPhase)}>Advance</button>}
          {game.team_capable && <button type="button" className="secondary" onClick={() => actions.previewTeams(game.id)}>Preview Teams</button>}
        </div>
      </div>
    </section>
  );
}

import { useAppState } from '../../state/store';

export function Build() {
  const { games, round } = useAppState();
  const game = games.find((item) => item.id === round?.game_id);
  return (
    <section className="display-stage build-stage">
      <h1>{game?.title ?? 'Build'}</h1>
      <div className="two-column">
        <div>
          <h2>Materials</h2>
          <ul className="check-list">{game?.materials.map((item) => <li key={item}>{item}</li>)}</ul>
        </div>
        <div>
          <h2>Steps</h2>
          <ol className="step-list">{game?.build_instructions.map((step) => <li key={step}>{step}</li>)}</ol>
        </div>
      </div>
    </section>
  );
}

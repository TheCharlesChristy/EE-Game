import { Leaderboard } from '../../components/display/Leaderboard';
import { TeamPodium } from '../../components/display/TeamPodium';
import { useAppState } from '../../state/store';

export function Results() {
  const { session, round, teams, actions } = useAppState();
  return (
    <section className="page-band two-column">
      <div>
        <div className="section-title">
          <h2>Results</h2>
          <p>{round?.game_id ?? 'No round'}</p>
        </div>
        <Leaderboard standings={session?.standings ?? []} />
      </div>
      <div>
        <h3>Round Teams</h3>
        <TeamPodium teams={teams} scores={round?.result?.team_scores} />
        <div className="toolbar">
          {round?.phase === 'results' && <button type="button" onClick={actions.enterIntermission}>Intermission</button>}
        </div>
      </div>
    </section>
  );
}

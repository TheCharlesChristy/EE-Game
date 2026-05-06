import { Leaderboard } from '../../components/display/Leaderboard';
import { TeamPodium } from '../../components/display/TeamPodium';
import { useAppState } from '../../state/store';

export function DisplayResults() {
  const { session, round, teams } = useAppState();
  return (
    <section className="display-stage results-display">
      <h1>Results</h1>
      <Leaderboard standings={session?.standings ?? []} />
      <TeamPodium teams={teams} scores={round?.result?.team_scores} />
    </section>
  );
}

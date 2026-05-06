import { TimerRing } from '../../components/display/TimerRing';
import { Leaderboard } from '../../components/display/Leaderboard';
import { useAppState } from '../../state/store';

export function DisplayLive() {
  const { round, session } = useAppState();
  return (
    <section className="display-stage live-display">
      <h1>Live</h1>
      {round && <TimerRing remainingMs={round.timer_remaining_ms} totalMs={round.timer_total_ms} />}
      <Leaderboard standings={session?.standings ?? []} />
    </section>
  );
}

import { TimerRing } from '../../components/display/TimerRing';
import { useAppState } from '../../state/store';

export function Live() {
  const { round, actions } = useAppState();
  if (!round) return <section className="page-band"><h2>Live</h2><p className="empty">No active round.</p></section>;
  return (
    <section className="page-band live-panel">
      <div className="section-title">
        <h2>Live Round</h2>
        <p>{round.phase}</p>
      </div>
      <TimerRing remainingMs={round.timer_remaining_ms} totalMs={round.timer_total_ms} />
      <div className="metric-grid">
        <div><strong>{Number(round.game_state.event_count ?? 0)}</strong><span>events</span></div>
        <div><strong>{Object.keys(round.test_results).length}</strong><span>tests</span></div>
      </div>
      <div className="toolbar">
        {round.phase === 'live' && <button type="button" className="secondary" onClick={() => actions.transitionRound('paused')}>Pause</button>}
        {round.phase === 'paused' && <button type="button" onClick={() => actions.transitionRound('live')}>Resume</button>}
        <button type="button" className="danger" onClick={actions.completeRound}>Complete</button>
      </div>
    </section>
  );
}

import { AppStateProvider, useAppState } from '../state/store';
import { Idle } from './display/Idle';
import { DisplayLobby } from './display/Lobby';
import { Build } from './display/Build';
import { Test } from './display/Test';
import { DisplayLive } from './display/Live';
import { DisplayResults } from './display/Results';

export function PublicDisplay() {
  return (
    <AppStateProvider>
      <DisplayShell />
    </AppStateProvider>
  );
}

function DisplayShell() {
  const { session, round } = useAppState();
  if (!session?.session_id) return <main className="display-shell"><Idle /></main>;
  if (!round) return <main className="display-shell"><DisplayLobby /></main>;
  if (round.phase === 'build' || round.phase === 'selected') return <main className="display-shell"><Build /></main>;
  if (round.phase === 'test' || round.phase === 'ready') return <main className="display-shell"><Test /></main>;
  if (round.phase === 'live' || round.phase === 'paused') {
    return (
      <main className="display-shell">
        <DisplayLive />
        {round.phase === 'paused' && <div className="pause-overlay">Paused</div>}
      </main>
    );
  }
  return (
    <main className="display-shell">
      <DisplayResults />
    </main>
  );
}

import { useState } from 'react';
import { AppStateProvider, useAppState } from '../state/store';
import { ConfirmModal } from '../components/ConfirmModal';
import { SessionHeader } from '../components/SessionHeader';
import { Toast } from '../components/Toast';
import { Lobby } from './host/Lobby';
import { Catalogue } from './host/Catalogue';
import { RoundPrep } from './host/RoundPrep';
import { TeamAllocation } from './host/TeamAllocation';
import { Live } from './host/Live';
import { Results } from './host/Results';
import { Intermission } from './host/Intermission';

type HostTab = 'lobby' | 'catalogue' | 'prep' | 'teams' | 'live' | 'results' | 'intermission' | 'settings';

export function HostControl() {
  return (
    <AppStateProvider>
      <HostShell />
    </AppStateProvider>
  );
}

function HostShell() {
  const { readyState, session, diagnostics, toast, error, clearToast, actions } = useAppState();
  const [tab, setTab] = useState<HostTab>('lobby');
  const [finishOpen, setFinishOpen] = useState(false);
  const tabs: HostTab[] = ['lobby', 'catalogue', 'prep', 'teams', 'live', 'results', 'intermission', 'settings'];

  return (
    <main className="app-shell host-shell">
      <SessionHeader readyState={readyState} session={session} />
      <nav className="tabbar" aria-label="Host sections">
        {tabs.map((item) => (
          <button
            key={item}
            type="button"
            className={item === tab ? 'active' : ''}
            onClick={() => setTab(item)}
          >
            {labelFor(item)}
          </button>
        ))}
      </nav>
      {tab === 'lobby' && <Lobby />}
      {tab === 'catalogue' && <Catalogue />}
      {tab === 'prep' && <RoundPrep />}
      {tab === 'teams' && <TeamAllocation />}
      {tab === 'live' && <Live />}
      {tab === 'results' && <Results />}
      {tab === 'intermission' && <Intermission />}
      {tab === 'settings' && (
        <section className="page-band two-column">
          <div>
            <h2>Settings</h2>
            <div className="toolbar">
              <button type="button" className="secondary" onClick={actions.saveSession}>Save</button>
              <button type="button" className="danger" onClick={() => setFinishOpen(true)}>Finish Session</button>
            </div>
          </div>
          <div>
            <h2>Diagnostics</h2>
            <pre className="diagnostics">{JSON.stringify(diagnostics, null, 2)}</pre>
          </div>
        </section>
      )}
      <ConfirmModal
        open={finishOpen}
        title="Finish session"
        message="This archives the session and clears the mutable classroom state."
        confirmLabel="Finish"
        onCancel={() => setFinishOpen(false)}
        onConfirm={() => {
          setFinishOpen(false);
          actions.finishSession();
        }}
      />
      <Toast message={toast} error={error} onDismiss={clearToast} />
    </main>
  );
}

function labelFor(tab: HostTab) {
  return tab.charAt(0).toUpperCase() + tab.slice(1);
}

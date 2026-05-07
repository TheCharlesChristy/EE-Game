import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

interface ServerInfo {
  ok: boolean;
  wifi_ssid?: string | null;
  backend_ap_host?: string;
}

export function Landing() {
  const navigate = useNavigate();
  const [server, setServer] = useState<ServerInfo | null>(null);

  useEffect(() => {
    fetch('/api/diagnostics')
      .then((r) => r.json())
      .then((d) => setServer({ ok: true, wifi_ssid: d.wifi_ssid, backend_ap_host: d.backend_ap_host }))
      .catch(() => setServer({ ok: false }));
  }, []);

  return (
    <div className="landing-root">
      <div className="landing-orb landing-orb--a" />
      <div className="landing-orb landing-orb--b" />

      <div className="landing-center">
        <header className="landing-header">
          <div className="landing-logo">
            <span className="landing-logo-icon">⚡</span>
            <span className="landing-logo-text">EE-Game</span>
          </div>
          <p className="landing-tagline">Electronics Education Platform</p>
        </header>

        <div className="landing-cards">
          <button
            type="button"
            className="landing-card landing-card--host"
            onClick={() => navigate('/host')}
          >
            <span className="landing-card-icon">🎛️</span>
            <strong className="landing-card-title">Host Control</strong>
            <span className="landing-card-sub">Manage sessions, games &amp; players</span>
          </button>

          <button
            type="button"
            className="landing-card landing-card--display"
            onClick={() => navigate('/display')}
          >
            <span className="landing-card-icon">📺</span>
            <strong className="landing-card-title">Public Display</strong>
            <span className="landing-card-sub">Room-facing leaderboard &amp; scoreboard</span>
          </button>
        </div>

        <footer className="landing-footer">
          {server === null && <span className="landing-status landing-status--checking">Connecting to server…</span>}
          {server?.ok === true && (
            <span className="landing-status landing-status--ok">
              Server online
              {server.wifi_ssid ? ` · WiFi: ${server.wifi_ssid}` : ''}
              {server.backend_ap_host ? ` · ${server.backend_ap_host}` : ''}
            </span>
          )}
          {server?.ok === false && (
            <span className="landing-status landing-status--error">Server unreachable</span>
          )}
        </footer>
      </div>
    </div>
  );
}

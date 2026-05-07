import {
  apiClient,
  Diagnostics,
  GameMetadata,
  Player,
  RoundPhase,
  RoundSummary,
  SessionSummary,
  Team,
} from '../api/client';
import { MessageEnvelope } from '../types/messages';
import { useWebSocket } from '../hooks/useWebSocket';
import {
  createContext,
  ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';

const WS_URL = import.meta.env.VITE_WS_URL ?? buildDefaultWsUrl();

interface AppState {
  readyState: number;
  session: SessionSummary | null;
  players: Player[];
  games: GameMetadata[];
  round: RoundSummary | null;
  teams: Team[];
  diagnostics: Diagnostics | null;
  toast: string | null;
  error: string | null;
  refresh: () => Promise<void>;
  clearToast: () => void;
  actions: {
    createSession: () => Promise<void>;
    resumeSession: () => Promise<void>;
    saveSession: () => Promise<void>;
    pauseSession: () => Promise<void>;
    finishSession: () => Promise<void>;
    updatePlayer: (playerId: string, body: Partial<Pick<Player, 'username' | 'colour'>>) => Promise<void>;
    selectRound: (gameId: string) => Promise<void>;
    transitionRound: (phase: RoundPhase) => Promise<void>;
    completeRound: () => Promise<void>;
    enterIntermission: () => Promise<void>;
    previewTeams: (gameId?: string) => Promise<void>;
    confirmTeams: () => Promise<void>;
    adjustScore: (playerId: string, delta: number, reason: string) => Promise<void>;
  };
}

const StoreContext = createContext<AppState | null>(null);

export function AppStateProvider({ children }: { children: ReactNode }) {
  const { readyState, lastMessage } = useWebSocket(WS_URL);
  const [session, setSession] = useState<SessionSummary | null>(null);
  const [players, setPlayers] = useState<Player[]>([]);
  const [games, setGames] = useState<GameMetadata[]>([]);
  const [round, setRound] = useState<RoundSummary | null>(null);
  const [teams, setTeams] = useState<Team[]>([]);
  const [diagnostics, setDiagnostics] = useState<Diagnostics | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const refreshTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const run = useCallback(async (label: string, fn: () => Promise<unknown>) => {
    setError(null);
    try {
      await fn();
      setToast(label);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Request failed.');
    }
  }, []);

  const refresh = useCallback(async () => {
    const [sessionData, playerData, gameData, roundData, diagnosticsData] = await Promise.all([
      apiClient.getSession(),
      apiClient.listPlayers(),
      apiClient.listGames(),
      apiClient.getCurrentRound(),
      apiClient.diagnostics(),
    ]);
    setSession(sessionData);
    setPlayers(playerData.players);
    setGames(gameData.games);
    setRound(roundData.round);
    setDiagnostics(diagnosticsData);
  }, []);

  useEffect(() => {
    if (import.meta.env.MODE === 'test') return;
    refresh().catch((err) => setError(err instanceof Error ? err.message : 'Initial load failed.'));
  }, [refresh]);

  useEffect(() => {
    if (!lastMessage) return;
    applyMessage(lastMessage, {
      setPlayers,
      setSession,
      setRound,
      setTeams,
    });
    if (lastMessage.type === 'state_update') {
      if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current);
      refreshTimerRef.current = setTimeout(() => {
        refresh().catch(() => undefined);
      }, 300);
    }
    return () => {
      if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current);
    };
  }, [lastMessage, refresh]);

  const actions = useMemo(
    () => ({
      createSession: () => run('Session created', async () => { await apiClient.createSession(); await refresh(); }),
      resumeSession: () => run('Session resumed', async () => { await apiClient.resumeSession(); await refresh(); }),
      saveSession: () => run('Session saved', async () => { await apiClient.saveSession(); await refresh(); }),
      pauseSession: () => run('Session paused', async () => { await apiClient.pauseSession(); await refresh(); }),
      finishSession: () => run('Session finished', async () => { await apiClient.finishSession(); await refresh(); }),
      updatePlayer: (playerId: string, body: Partial<Pick<Player, 'username' | 'colour'>>) =>
        run('Player updated', async () => { await apiClient.updatePlayer(playerId, body); await refresh(); }),
      selectRound: (gameId: string) =>
        run('Round selected', async () => { setRound(await apiClient.selectRound(gameId)); await refresh(); }),
      transitionRound: (phase: RoundPhase) =>
        run(`Phase: ${phase}`, async () => { setRound(await apiClient.transitionRound(phase)); await refresh(); }),
      completeRound: () =>
        run('Round completed', async () => { setRound(await apiClient.completeRound()); await refresh(); }),
      enterIntermission: () =>
        run('Intermission started', async () => { setRound(await apiClient.enterIntermission()); await refresh(); }),
      previewTeams: (gameId?: string) =>
        run('Team preview ready', async () => { const preview = await apiClient.previewTeams(gameId); setTeams(preview.teams); }),
      confirmTeams: () =>
        run('Teams allocated', async () => { const preview = await apiClient.confirmTeams(); setTeams(preview.teams); await refresh(); }),
      adjustScore: (playerId: string, delta: number, reason: string) =>
        run('Score adjusted', async () => { await apiClient.adjustScore(playerId, delta, reason); await refresh(); }),
    }),
    [refresh, run],
  );

  const value = useMemo<AppState>(
    () => ({
      readyState,
      session,
      players,
      games,
      round,
      teams,
      diagnostics,
      toast,
      error,
      refresh,
      clearToast: () => setToast(null),
      actions,
    }),
    [actions, diagnostics, error, games, players, readyState, refresh, round, session, teams, toast],
  );

  return <StoreContext.Provider value={value}>{children}</StoreContext.Provider>;
}

export function useAppState() {
  const value = useContext(StoreContext);
  if (!value) throw new Error('useAppState must be used inside AppStateProvider');
  return value;
}

function applyMessage(
  message: MessageEnvelope,
  setters: {
    setPlayers: (players: Player[]) => void;
    setSession: (fn: (prev: SessionSummary | null) => SessionSummary | null) => void;
    setRound: (fn: (prev: RoundSummary | null) => RoundSummary | null) => void;
    setTeams: (teams: Team[]) => void;
  },
) {
  if (message.type === 'device_list') return;
  if (message.type !== 'state_update') return;
  const payload = message.payload as { event?: string; data?: Record<string, unknown> };
  const data = payload.data ?? {};
  if (Array.isArray(data.players)) setters.setPlayers(data.players as Player[]);
  if (payload.event === 'round_selected' || payload.event === 'round_transitioned' || payload.event === 'round_completed') {
    setters.setRound((prev) => prev ? { ...prev, ...(data as Partial<RoundSummary>) } : (data as unknown as RoundSummary));
  }
  if (payload.event === 'teams_allocated' && Array.isArray(data.teams)) {
    setters.setTeams(data.teams as Team[]);
  }
  if ('session_id' in data) {
    setters.setSession((prev) => {
      const base = prev ?? emptySession();
      const update = data as Record<string, unknown>;
      const merged = { ...base };
      for (const k of Object.keys(update)) {
        if (update[k] !== undefined) {
          (merged as Record<string, unknown>)[k] = update[k];
        }
      }
      return merged as SessionSummary;
    });
  }
}

function emptySession(): SessionSummary {
  return {
    session_id: null,
    status: null,
    created_at: null,
    updated_at: null,
    active_game: null,
    player_list: [],
    standings: [],
  };
}

function buildDefaultWsUrl() {
  if (typeof window === 'undefined') return 'ws://localhost:8000/ws/frontend';
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = window.location.host || 'localhost:8000';
  return `${protocol}//${host}/ws/frontend`;
}

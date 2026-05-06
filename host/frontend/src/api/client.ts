export interface ApiResponse<T> {
  data: T;
  ok: boolean;
}

const API_BASE = import.meta.env.VITE_API_URL ?? '';

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(init.headers ?? {}),
    },
    ...init,
  });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail ?? detail;
    } catch {
      // Ignore non-JSON error bodies.
    }
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}

export const apiClient = {
  getSession: () => request<SessionSummary>('/api/sessions/current'),
  createSession: () => request('/api/sessions', { method: 'POST' }),
  resumeSession: () => request('/api/sessions/resume', { method: 'POST' }),
  saveSession: () => request('/api/sessions/current/save', { method: 'POST' }),
  pauseSession: () => request('/api/sessions/current/pause', { method: 'POST' }),
  finishSession: () =>
    request('/api/sessions/current/finish', {
      method: 'POST',
      body: JSON.stringify({ confirmed: true }),
    }),
  listPlayers: () => request<PlayerListResponse>('/api/sessions/current/players'),
  updatePlayer: (playerId: string, body: Partial<Pick<Player, 'username' | 'colour'>>) =>
    request<Player>(`/api/sessions/current/players/${playerId}`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    }),
  listGames: () => request<GameListResponse>('/api/games'),
  getCurrentRound: () => request<{ round: RoundSummary | null }>('/api/rounds/current'),
  selectRound: (gameId: string, durationMs?: number) =>
    request<RoundSummary>('/api/rounds/select', {
      method: 'POST',
      body: JSON.stringify({ game_id: gameId, duration_ms: durationMs }),
    }),
  transitionRound: (phase: RoundPhase) =>
    request<RoundSummary>('/api/rounds/current/transition', {
      method: 'POST',
      body: JSON.stringify({ phase }),
    }),
  completeRound: () => request<RoundSummary>('/api/rounds/current/complete', { method: 'POST' }),
  enterIntermission: () =>
    request<RoundSummary>('/api/rounds/current/intermission', { method: 'POST' }),
  previewTeams: (gameId?: string) =>
    request<TeamPreview>('/api/teams/preview', {
      method: 'POST',
      body: JSON.stringify({ game_id: gameId }),
    }),
  confirmTeams: () =>
    request<TeamPreview>('/api/teams/confirm', {
      method: 'POST',
      body: JSON.stringify({}),
    }),
  adjustScore: (playerId: string, scoreDelta: number, reason: string) =>
    request('/api/scoring/adjust', {
      method: 'POST',
      body: JSON.stringify({ player_id: playerId, score_delta: scoreDelta, reason }),
    }),
  diagnostics: () => request<Diagnostics>('/api/diagnostics'),
};

export type RoundPhase =
  | 'selected'
  | 'build'
  | 'test'
  | 'ready'
  | 'live'
  | 'paused'
  | 'completed'
  | 'results'
  | 'intermission';

export interface SessionSummary {
  session_id: string | null;
  status: string | null;
  created_at: string | null;
  updated_at: string | null;
  current_round_id?: string | null;
  active_game: string | null;
  player_list: Player[];
  standings: Standing[];
}

export interface Player {
  player_id: string;
  device_id: string;
  username: string;
  colour: string;
  connection_state: 'connected' | 'stale' | 'disconnected';
  last_seen_at: string;
  registered_at: string;
  firmware_version: string;
  board_target: string;
}

export interface Standing {
  player_id: string;
  username: string;
  colour: string;
  score: number;
}

export interface PlayerListResponse {
  players: Player[];
  count: number;
}

export interface GameMetadata {
  id: string;
  title: string;
  category: string;
  summary: string;
  min_players: number;
  max_players: number;
  estimated_seconds: number;
  input_modes: string[];
  materials: string[];
  build_instructions: string[];
  team_capable: boolean;
  team_size: number | null;
  scoring_mode: string;
}

export interface GameListResponse {
  games: GameMetadata[];
  count: number;
}

export interface RoundSummary {
  round_id: string;
  session_id: string;
  game_id: string;
  phase: RoundPhase;
  timer_total_ms: number;
  timer_remaining_ms: number;
  game_state: Record<string, unknown>;
  test_results: Record<string, { passed: boolean; reason: string; device_id: string }>;
  result: RoundResult | null;
}

export interface RoundResult {
  round_id: string;
  game_id: string;
  player_scores: Record<string, number>;
  team_scores?: Record<string, number>;
  highlights?: string[];
}

export interface TeamPreview {
  teams: Team[];
  team_capable: boolean;
}

export interface Team {
  team_id: string;
  team_name: string;
  player_ids: string[];
}

export interface Diagnostics {
  ok: boolean;
  generated_at: string;
  schema_version: number;
  connected_devices: number;
  current_session: Record<string, unknown>;
  table_counts: Record<string, number>;
}

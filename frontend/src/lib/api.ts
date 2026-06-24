const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

// Standard Fetch Wrapper with Timeout and Error Handling
async function fetchAPI<T>(endpoint: string, options: RequestInit = {}): Promise<T | null> {
  const url = `${API_BASE_URL}${endpoint}`;
  try {
    const res = await fetch(url, {
      ...options,
      next: { revalidate: 10 }, // Cache for 10 seconds
    });
    if (!res.ok) {
      console.error(`API Error: ${url} returned status ${res.status}`);
      return null;
    }
    return await res.json() as T;
  } catch (error) {
    console.error(`Fetch failed for URL: ${url}`, error);
    return null;
  }
}

// ──────────────────────────────────────────────
// API Interfaces
// ──────────────────────────────────────────────
export interface SummaryData {
  teams: number;
  players: number;
  games: number;
  completed_games: number;
  batting_records: number;
  pitching_records: number;
  season: number;
}

export interface Team {
  id: number;
  mlb_id: number;
  name: string;
  abbreviation: string;
  league: string;
  division: string;
  venue_name: string;
  logo_url: string;
  wins?: number;
  losses?: number;
  win_pct?: number;
  games_back?: number;
  runs_scored?: number;
  runs_allowed?: number;
  run_diff?: number;
  division_rank?: number | null;
  streak?: string | null;
}

export interface SavantStats {
  id: number;
  player_id: number;
  is_pitcher: boolean;
  avg_exit_velocity: number | null;
  max_exit_velocity: number | null;
  avg_launch_angle: number | null;
  barrel_rate: number | null;
  xba: number | null;
  xslg: number | null;
  xwoba: number | null;
}

export interface Player {
  id: number;
  mlb_id: number;
  full_name: string;
  first_name: string;
  last_name: string;
  primary_position: string;
  bats: string;
  throws: string;
  birth_date: string | null;
  birth_country: string;
  height: string;
  weight: number;
  jersey_number: string;
  headshot_url: string;
  active: boolean;
  team?: Team;
  savant_stats?: SavantStats | null;
}

export interface SavantLeader {
  rank: number;
  player_id: number;
  player_name: string;
  position: string;
  headshot_url: string;
  team: string;
  value: number;
}


export interface PlayerListItem {
  id: number;
  mlb_id: number;
  full_name: string;
  primary_position: string;
  jersey_number: string;
  headshot_url: string;
  team_abbreviation: string | null;
  team_name: string | null;
}

export interface PaginatedPlayers {
  total: number;
  page: number;
  per_page: number;
  data: PlayerListItem[];
}

export interface BattingStats {
  player_name: string;
  player_id: number;
  at_bats: number;
  runs: number;
  hits: number;
  doubles: number;
  triples: number;
  home_runs: number;
  rbi: number;
  walks: number;
  strikeouts: number;
  stolen_bases: number;
  plate_appearances: number;
  avg: number;
  obp: number;
  slg: number;
  ops: number;
}

export interface PitchingStats {
  player_name: string;
  player_id: number;
  innings_pitched: number;
  hits_allowed: number;
  runs_allowed: number;
  earned_runs: number;
  walks_allowed: number;
  strikeouts: number;
  home_runs_allowed: number;
  pitches_thrown: number;
  era: number;
  whip: number;
  wins: number;
  losses: number;
  saves: number;
}

export interface PlayerGameLog {
  game_date: string;
  opponent: string;
  opponent_abbr: string;
  is_home: boolean;
  is_pitcher?: boolean;
  
  // Batting stats
  at_bats?: number;
  hits?: number;
  home_runs?: number;
  rbi?: number;
  walks?: number;
  strikeouts?: number;
  avg?: number;

  // Pitching stats
  innings_pitched?: number;
  hits_allowed?: number;
  runs_allowed?: number;
  earned_runs?: number;
  pitching_strikeouts?: number;
}

export interface Game {
  id: number;
  mlb_game_pk: number;
  game_date: string;
  status: string;
  home_team_id: number;
  away_team_id: number;
  home_score: number | null;
  away_score: number | null;
  venue: string;
  season: number;
  game_type: string;
  winning_team_id: number | null;
  losing_team_id: number | null;
  home_starter_id?: number | null;
  away_starter_id?: number | null;
}

export interface GameListItem {
  id: number;
  mlb_game_pk: number;
  game_date: string;
  status: string;
  home_team_name: string;
  home_team_abbr: string;
  away_team_name: string;
  away_team_abbr: string;
  home_score: number | null;
  away_score: number | null;
  venue: string;
  home_logo: string | null;
  away_logo: string | null;
  home_win_prob?: number;
  away_win_prob?: number;
}

export interface StandingsEntry {
  team: Team;
  wins: number;
  losses: number;
  win_pct: number;
  games_back: number;
  runs_scored: number;
  runs_allowed: number;
  run_diff: number;
  division_rank: number;
  streak: string;
}

export interface DivisionStandings {
  division: string;
  league: string;
  teams: StandingsEntry[];
}

export interface BattingLeader {
  rank: number;
  player_id: number;
  player_name: string;
  position: string;
  headshot_url: string;
  team: string;
  value: number;
  avg: number;
}

export interface PitchingLeader {
  rank: number;
  player_id: number;
  player_name: string;
  headshot_url: string;
  team: string;
  value: number;
  era: number;
}

// ──────────────────────────────────────────────
// API Fetching Functions
// ──────────────────────────────────────────────

export async function getSummary(): Promise<SummaryData> {
  const data = await fetchAPI<SummaryData>("/api/analysis/summary");
  return data || {
    teams: 0,
    players: 0,
    games: 0,
    completed_games: 0,
    batting_records: 0,
    pitching_records: 0,
    season: 2024
  };
}

export async function getTeams(): Promise<Team[]> {
  const data = await fetchAPI<Team[]>("/api/teams");
  return data || [];
}

export async function getTeam(id: number): Promise<Team | null> {
  return await fetchAPI<Team>(`/api/teams/${id}`);
}

export async function getTeamRoster(id: number): Promise<PlayerListItem[]> {
  const data = await fetchAPI<PlayerListItem[]>(`/api/teams/${id}/roster`);
  return data || [];
}

export async function getPlayers(params: {
  search?: string;
  position?: string;
  teamId?: number;
  page?: number;
  perPage?: number;
}): Promise<PaginatedPlayers> {
  const queryParts = [];
  if (params.search) queryParts.push(`search=${encodeURIComponent(params.search)}`);
  if (params.position) queryParts.push(`position=${encodeURIComponent(params.position)}`);
  if (params.teamId) queryParts.push(`team_id=${params.teamId}`);
  if (params.page) queryParts.push(`page=${params.page}`);
  if (params.perPage) queryParts.push(`per_page=${params.perPage}`);
  
  const queryString = queryParts.length > 0 ? `?${queryParts.join("&")}` : "";
  const data = await fetchAPI<PaginatedPlayers>(`/api/players${queryString}`);
  
  return data || { total: 0, page: 1, per_page: 25, data: [] };
}

export async function getPlayer(id: number): Promise<Player | null> {
  return await fetchAPI<Player>(`/api/players/${id}`);
}

export async function getPlayerBattingStats(id: number): Promise<BattingStats | null> {
  return await fetchAPI<BattingStats>(`/api/players/${id}/batting-stats`);
}

export async function getPlayerPitchingStats(id: number): Promise<PitchingStats | null> {
  return await fetchAPI<PitchingStats>(`/api/players/${id}/pitching-stats`);
}

export async function getPlayerGamelog(id: number): Promise<PlayerGameLog[]> {
  const data = await fetchAPI<PlayerGameLog[]>(`/api/players/${id}/gamelog`);
  return data || [];
}

export async function getGames(params: {
  date?: string;
  teamId?: number;
  status?: string;
}): Promise<GameListItem[]> {
  const queryParts = [];
  if (params.date) queryParts.push(`date=${params.date}`);
  if (params.teamId) queryParts.push(`team_id=${params.teamId}`);
  if (params.status) queryParts.push(`status=${params.status}`);
  
  const queryString = queryParts.length > 0 ? `?${queryParts.join("&")}` : "";
  const data = await fetchAPI<GameListItem[]>(`/api/games${queryString}`);
  return data || [];
}

export async function getGame(id: number): Promise<Game | null> {
  return await fetchAPI<Game>(`/api/games/${id}`);
}

export async function getStandings(): Promise<DivisionStandings[]> {
  const data = await fetchAPI<DivisionStandings[]>("/api/standings");
  return data || [];
}

export async function getBattingLeaders(stat: string = "home_runs", limit: number = 5): Promise<BattingLeader[]> {
  const data = await fetchAPI<BattingLeader[]>(`/api/analysis/leaders/batting?stat=${stat}&limit=${limit}`);
  return data || [];
}

export async function getPitchingLeaders(stat: string = "strikeouts", limit: number = 5): Promise<PitchingLeader[]> {
  const data = await fetchAPI<PitchingLeader[]>(`/api/analysis/leaders/pitching?stat=${stat}&limit=${limit}`);
  return data || [];
}

export async function getPlayerSavantStats(id: number): Promise<SavantStats | null> {
  return await fetchAPI<SavantStats>(`/api/players/${id}/savant-stats`);
}

export async function getSavantLeaders(stat: string = "avg_exit_velocity", playerType: string = "batter", limit: number = 5): Promise<SavantLeader[]> {
  const data = await fetchAPI<SavantLeader[]>(`/api/analysis/leaders/savant?stat=${stat}&player_type=${playerType}&limit=${limit}`);
  return data || [];
}

// ──────────────────────────────────────────────
// GenAI API Functions
// ──────────────────────────────────────────────
export interface GenAIAnalysis {
  player_name?: string;
  game_date?: string;
  matchup?: string;
  analysis: string;
  source: string;
  model: string;
}

export async function getGenAIPlayerAnalysis(id: number): Promise<GenAIAnalysis | null> {
  return await fetchAPI<GenAIAnalysis>(`/api/genai/player/${id}/analysis`);
}

export async function getGenAIGameAnalysis(id: number): Promise<GenAIAnalysis | null> {
  return await fetchAPI<GenAIAnalysis>(`/api/genai/game/${id}/analysis`);
}

// ──────────────────────────────────────────────
// ML & SHAP API Functions
// ──────────────────────────────────────────────
export interface MLStatus {
  model_loaded: boolean;
  feature_names: string[] | null;
  has_training_metrics: boolean;
  has_shap_results: boolean;
  model_type: string | null;
}

export interface TrainingMetrics {
  baseline?: {
    model: string;
    mean_accuracy: number;
    pooled_auc_roc: number;
    pooled_precision: number;
    pooled_recall: number;
    pooled_f1: number;
  };
  random_forest?: {
    model: string;
    best_params: Record<string, unknown>;
    mean_accuracy: number;
    pooled_auc_roc: number;
    pooled_precision: number;
    pooled_recall: number;
    pooled_f1: number;
    confusion_matrix: number[][];
  };
  shap?: {
    feature_importance: Record<string, number>;
    feature_labels_cn: Record<string, string>;
  };
  dataset_info?: {
    total_games: number;
    home_win_rate: number;
    features: string[];
  };
}

export async function getMLStatus(): Promise<MLStatus | null> {
  return await fetchAPI<MLStatus>('/api/ml/status');
}

export async function getTrainingMetrics(): Promise<TrainingMetrics | null> {
  return await fetchAPI<TrainingMetrics>('/api/ml/metrics');
}

export async function getSHAPResults(): Promise<Record<string, unknown> | null> {
  return await fetchAPI<Record<string, unknown>>('/api/ml/shap');
}

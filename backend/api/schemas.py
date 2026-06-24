"""
Pydantic schemas for API request/response serialization.
"""

from pydantic import BaseModel, computed_field
from typing import Optional, List
from datetime import date, datetime


# ──────────────────────────────────────────────
# Team Schemas
# ──────────────────────────────────────────────
class TeamBase(BaseModel):
    mlb_id: int
    name: str
    abbreviation: str
    league: Optional[str] = None
    division: Optional[str] = None
    venue_name: Optional[str] = None
    logo_url: Optional[str] = None


class TeamResponse(TeamBase):
    id: int

    class Config:
        from_attributes = True


class TeamWithStats(TeamResponse):
    wins: int = 0
    losses: int = 0
    win_pct: float = 0.0
    games_back: float = 0.0
    runs_scored: int = 0
    runs_allowed: int = 0
    run_diff: int = 0
    division_rank: Optional[int] = None
    streak: Optional[str] = None


# ──────────────────────────────────────────────
# Player Schemas
# ──────────────────────────────────────────────
class PlayerBase(BaseModel):
    mlb_id: int
    full_name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    primary_position: Optional[str] = None
    bats: Optional[str] = None
    throws: Optional[str] = None
    birth_date: Optional[date] = None
    height: Optional[str] = None
    weight: Optional[int] = None
    jersey_number: Optional[str] = None
    headshot_url: Optional[str] = None
    active: bool = True


class SavantStatsResponse(BaseModel):
    id: int
    player_id: int
    is_pitcher: bool
    avg_exit_velocity: Optional[float] = None
    max_exit_velocity: Optional[float] = None
    avg_launch_angle: Optional[float] = None
    barrel_rate: Optional[float] = None
    xba: Optional[float] = None
    xslg: Optional[float] = None
    xwoba: Optional[float] = None

    class Config:
        from_attributes = True


class PlayerResponse(PlayerBase):
    id: int
    team: Optional[TeamResponse] = None
    savant_stats: Optional[SavantStatsResponse] = None

    class Config:
        from_attributes = True


class PlayerListItem(BaseModel):
    id: int
    mlb_id: int
    full_name: str
    primary_position: Optional[str] = None
    jersey_number: Optional[str] = None
    headshot_url: Optional[str] = None
    team_abbreviation: Optional[str] = None
    team_name: Optional[str] = None

    class Config:
        from_attributes = True


# ──────────────────────────────────────────────
# Game Schemas
# ──────────────────────────────────────────────
class GameResponse(BaseModel):
    id: int
    mlb_game_pk: int
    game_date: date
    status: Optional[str] = None
    home_team: Optional[TeamResponse] = None
    away_team: Optional[TeamResponse] = None
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    venue: Optional[str] = None
    season: int
    game_type: Optional[str] = None
    home_win_prob: Optional[int] = None
    away_win_prob: Optional[int] = None

    class Config:
        from_attributes = True


class GameListItem(BaseModel):
    id: int
    mlb_game_pk: int
    game_date: date
    status: Optional[str] = None
    home_team_name: str
    home_team_abbr: str
    away_team_name: str
    away_team_abbr: str
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    venue: Optional[str] = None
    home_logo: Optional[str] = None
    away_logo: Optional[str] = None
    home_win_prob: Optional[int] = None
    away_win_prob: Optional[int] = None


# ──────────────────────────────────────────────
# Stats Schemas
# ──────────────────────────────────────────────
class BattingStatsResponse(BaseModel):
    player_name: str
    player_id: int
    at_bats: int = 0
    runs: int = 0
    hits: int = 0
    doubles: int = 0
    triples: int = 0
    home_runs: int = 0
    rbi: int = 0
    walks: int = 0
    strikeouts: int = 0
    stolen_bases: int = 0
    plate_appearances: int = 0
    avg: float = 0.0
    obp: float = 0.0
    slg: float = 0.0
    ops: float = 0.0

    class Config:
        from_attributes = True


class PitchingStatsResponse(BaseModel):
    player_name: str
    player_id: int
    innings_pitched: float = 0.0
    hits_allowed: int = 0
    runs_allowed: int = 0
    earned_runs: int = 0
    walks_allowed: int = 0
    strikeouts: int = 0
    home_runs_allowed: int = 0
    pitches_thrown: int = 0
    era: float = 0.0
    whip: float = 0.0
    wins: int = 0
    losses: int = 0
    saves: int = 0

    class Config:
        from_attributes = True


class PlayerGameLog(BaseModel):
    game_date: date
    opponent: str
    opponent_abbr: str
    is_home: bool
    is_pitcher: bool = False
    
    # Batting stats
    at_bats: int = 0
    hits: int = 0
    home_runs: int = 0
    rbi: int = 0
    walks: int = 0
    strikeouts: int = 0
    avg: float = 0.0

    # Pitching stats
    innings_pitched: Optional[float] = None
    hits_allowed: Optional[int] = None
    runs_allowed: Optional[int] = None
    earned_runs: Optional[int] = None
    pitching_strikeouts: Optional[int] = None

# ──────────────────────────────────────────────
# Standings Schemas
# ──────────────────────────────────────────────
class StandingsEntry(BaseModel):
    team: TeamResponse
    wins: int
    losses: int
    win_pct: float
    games_back: float
    runs_scored: int
    runs_allowed: int
    run_diff: int
    division_rank: Optional[int] = None
    streak: Optional[str] = None

    class Config:
        from_attributes = True


class DivisionStandings(BaseModel):
    division: str
    league: str
    teams: List[StandingsEntry]


# ──────────────────────────────────────────────
# Pagination
# ──────────────────────────────────────────────
class PaginatedResponse(BaseModel):
    total: int
    page: int
    per_page: int
    data: list


# ──────────────────────────────────────────────
# Prediction Schemas
# ──────────────────────────────────────────────
class PredictionRequest(BaseModel):
    home_team_id: int
    away_team_id: int
    home_starter_id: Optional[int] = None
    away_starter_id: Optional[int] = None


class PredictionResponse(BaseModel):
    home_team: str
    away_team: str
    home_win_probability: float
    away_win_probability: float
    predicted_winner: str
    confidence: str          # "High" / "Medium" / "Low"
    key_factors: List[str]
    model_name: str

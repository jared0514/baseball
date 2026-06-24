"""
FastAPI Routers — Teams, Players, Games, Standings, GenAI, ML Prediction
"""

import json
import logging
from pathlib import Path

import joblib
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, or_, Float, cast
from typing import Optional, List, Dict, Any
from datetime import date, datetime

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database.models import (
    Team, Player, Game, BattingStats, PitchingStats, TeamStandings, SavantStats, get_db
)
from api.schemas import (
    TeamResponse, TeamWithStats, PlayerResponse, PlayerListItem,
    GameResponse, GameListItem, BattingStatsResponse, PitchingStatsResponse,
    PlayerGameLog, StandingsEntry, DivisionStandings, PaginatedResponse,
    SavantStatsResponse
)
from genai.analyzer import generate_player_analysis, generate_game_analysis

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# ML Model Loading (Trained Random Forest)
# ──────────────────────────────────────────────
MODELS_DIR = Path(__file__).resolve().parent.parent.parent / "analysis" / "models"
PLOTS_DIR = Path(__file__).resolve().parent.parent.parent / "analysis" / "plots"

_rf_model = None
_feature_names = None
_training_metrics = None
_shap_results = None


def _load_ml_artifacts():
    """Load trained ML model and associated artifacts on first use."""
    global _rf_model, _feature_names, _training_metrics, _shap_results

    model_path = MODELS_DIR / "rf_predictor.pkl"
    features_path = MODELS_DIR / "feature_names.json"
    metrics_path = MODELS_DIR / "training_metrics.json"
    shap_path = MODELS_DIR / "shap_results.json"

    if model_path.exists() and _rf_model is None:
        try:
            _rf_model = joblib.load(model_path)
            logger.info(f"Loaded ML model from {model_path}")
        except Exception as e:
            logger.warning(f"Failed to load ML model: {e}")

    if features_path.exists() and _feature_names is None:
        try:
            with open(features_path) as f:
                _feature_names = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load feature names: {e}")

    if metrics_path.exists() and _training_metrics is None:
        try:
            with open(metrics_path, encoding="utf-8") as f:
                _training_metrics = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load training metrics: {e}")

    if shap_path.exists() and _shap_results is None:
        try:
            with open(shap_path, encoding="utf-8") as f:
                _shap_results = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load SHAP results: {e}")


# Load artifacts at module import time
_load_ml_artifacts()


# ──────────────────────────────────────────────
# Helper: Rolling Statistics & Win Prediction
# ──────────────────────────────────────────────
def get_rolling_stats(db: Session, team_id: int, before_date: date, window: int = 10):
    """Calculate rolling win percentage and run differential for a team before a given date."""
    # Query the last `window` completed games for this team before before_date
    past_games = (
        db.query(Game)
        .filter(
            (Game.home_team_id == team_id) | (Game.away_team_id == team_id),
            Game.status == "Final",
            Game.game_date < before_date
        )
        .order_by(desc(Game.game_date))
        .limit(window)
        .all()
    )
    
    if not past_games:
        return 0.5, 0  # Fallback default
        
    wins = 0
    run_diff = 0
    for g in past_games:
        if g.home_score is not None and g.away_score is not None:
            is_home = g.home_team_id == team_id
            if is_home:
                run_diff += (g.home_score - g.away_score)
                if g.home_score > g.away_score:
                    wins += 1
            else:
                run_diff += (g.away_score - g.home_score)
                if g.away_score > g.home_score:
                    wins += 1
                    
    win_pct = wins / len(past_games)
    return win_pct, run_diff


def calculate_rolling_prediction(db: Session, home_team_id: int, away_team_id: int, game_date: date):
    """Calculate win probability using the trained ML model, with formula fallback."""
    home_win_pct, home_run_diff = get_rolling_stats(db, home_team_id, game_date, window=10)
    away_win_pct, away_run_diff = get_rolling_stats(db, away_team_id, game_date, window=10)

    win_pct_diff = home_win_pct - away_win_pct
    run_diff_diff = home_run_diff - away_run_diff

    # --- Try the trained Random Forest model first ---
    if _rf_model is not None and _feature_names is not None:
        try:
            # Build feature vector matching training feature order
            home_rs = home_run_diff + 700  # Approximate RS from run_diff
            home_ra = 700  # Approximate baseline
            away_rs = away_run_diff + 700
            away_ra = 700
            home_scoring_rate = home_rs / max(home_rs + home_ra, 1)
            away_scoring_rate = away_rs / max(away_rs + away_ra, 1)
            scoring_rate_diff = home_scoring_rate - away_scoring_rate

            feature_values = {
                'home_win_pct': home_win_pct,
                'away_win_pct': away_win_pct,
                'win_pct_diff': win_pct_diff,
                'home_run_diff': home_run_diff,
                'away_run_diff': away_run_diff,
                'run_diff_diff': run_diff_diff,
                'home_scoring_rate': home_scoring_rate,
                'away_scoring_rate': away_scoring_rate,
                'scoring_rate_diff': scoring_rate_diff,
                'home_advantage': 1,
            }

            X = np.array([[feature_values.get(f, 0) for f in _feature_names]])
            proba = _rf_model.predict_proba(X)[0]
            home_prob = float(proba[1])
            home_prob = max(0.15, min(0.85, home_prob))
            away_prob = 1.0 - home_prob
            return round(home_prob * 100), round(away_prob * 100)
        except Exception as e:
            logger.warning(f"ML model prediction failed, using fallback: {e}")

    # --- Fallback: original formula ---
    home_prob = 0.51 + 0.35 * win_pct_diff + 0.008 * run_diff_diff
    home_prob = max(0.15, min(0.85, home_prob))
    away_prob = 1.0 - home_prob

    return round(home_prob * 100), round(away_prob * 100)


# ──────────────────────────────────────────────
# Teams Router
# ──────────────────────────────────────────────
teams_router = APIRouter(prefix="/api/teams", tags=["Teams"])


@teams_router.get("", response_model=List[TeamResponse])
def get_teams(db: Session = Depends(get_db)):
    """Get all MLB teams."""
    teams = db.query(Team).order_by(Team.league, Team.division, Team.name).all()
    return teams


@teams_router.get("/{team_id}", response_model=TeamWithStats)
def get_team(team_id: int, db: Session = Depends(get_db)):
    """Get team details with standings."""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    standings = db.query(TeamStandings).filter(
        TeamStandings.team_id == team.id
    ).first()

    result = TeamWithStats(
        id=team.id,
        mlb_id=team.mlb_id,
        name=team.name,
        abbreviation=team.abbreviation,
        league=team.league,
        division=team.division,
        venue_name=team.venue_name,
        logo_url=team.logo_url,
        wins=standings.wins if standings else 0,
        losses=standings.losses if standings else 0,
        win_pct=standings.win_pct if standings else 0.0,
        games_back=standings.games_back if standings else 0.0,
        runs_scored=standings.runs_scored if standings else 0,
        runs_allowed=standings.runs_allowed if standings else 0,
        run_diff=standings.run_diff if standings else 0,
        division_rank=standings.division_rank if standings else None,
        streak=standings.streak if standings else None,
    )
    return result


@teams_router.get("/{team_id}/roster", response_model=List[PlayerListItem])
def get_team_roster(team_id: int, db: Session = Depends(get_db)):
    """Get team roster."""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    players = db.query(Player).filter(
        Player.team_id == team_id, Player.active == True
    ).order_by(Player.primary_position, Player.last_name).all()

    return [
        PlayerListItem(
            id=p.id,
            mlb_id=p.mlb_id,
            full_name=p.full_name,
            primary_position=p.primary_position,
            jersey_number=p.jersey_number,
            headshot_url=p.headshot_url,
            team_abbreviation=team.abbreviation,
            team_name=team.name,
        )
        for p in players
    ]


# ──────────────────────────────────────────────
# Players Router
# ──────────────────────────────────────────────
players_router = APIRouter(prefix="/api/players", tags=["Players"])


@players_router.get("", response_model=PaginatedResponse)
def get_players(
    search: Optional[str] = None,
    position: Optional[str] = None,
    team_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Search and list players with pagination."""
    query = db.query(Player).filter(Player.active == True)

    if search:
        query = query.filter(Player.full_name.ilike(f"%{search}%"))
    if position:
        query = query.filter(Player.primary_position == position)
    if team_id:
        query = query.filter(Player.team_id == team_id)

    total = query.count()
    players = query.order_by(Player.last_name).offset((page - 1) * per_page).limit(per_page).all()

    items = []
    for p in players:
        team = db.query(Team).filter(Team.id == p.team_id).first()
        items.append(
            PlayerListItem(
                id=p.id,
                mlb_id=p.mlb_id,
                full_name=p.full_name,
                primary_position=p.primary_position,
                jersey_number=p.jersey_number,
                headshot_url=p.headshot_url,
                team_abbreviation=team.abbreviation if team else None,
                team_name=team.name if team else None,
            ).model_dump()
        )

    return PaginatedResponse(total=total, page=page, per_page=per_page, data=items)


@players_router.get("/{player_id}", response_model=PlayerResponse)
def get_player(player_id: int, db: Session = Depends(get_db)):
    """Get player details."""
    player = db.query(Player).options(joinedload(Player.team), joinedload(Player.savant_stats)).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player


@players_router.get("/{player_id}/batting-stats", response_model=BattingStatsResponse)
def get_player_batting_stats(player_id: int, db: Session = Depends(get_db)):
    """Get player's season batting stats (aggregated)."""
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    stats = db.query(
        func.sum(BattingStats.at_bats).label("at_bats"),
        func.sum(BattingStats.runs).label("runs"),
        func.sum(BattingStats.hits).label("hits"),
        func.sum(BattingStats.doubles).label("doubles"),
        func.sum(BattingStats.triples).label("triples"),
        func.sum(BattingStats.home_runs).label("home_runs"),
        func.sum(BattingStats.rbi).label("rbi"),
        func.sum(BattingStats.walks).label("walks"),
        func.sum(BattingStats.strikeouts).label("strikeouts"),
        func.sum(BattingStats.stolen_bases).label("stolen_bases"),
        func.sum(BattingStats.plate_appearances).label("plate_appearances"),
        func.sum(BattingStats.hit_by_pitch).label("hit_by_pitch"),
        func.sum(BattingStats.sacrifice_flies).label("sacrifice_flies"),
    ).filter(BattingStats.player_id == player_id).first()

    if not stats or stats.at_bats is None:
        return BattingStatsResponse(player_name=player.full_name, player_id=player.id)

    ab = int(stats.at_bats or 0)
    h = int(stats.hits or 0)
    bb = int(stats.walks or 0)
    hbp = int(stats.hit_by_pitch or 0)
    sf = int(stats.sacrifice_flies or 0)
    doubles = int(stats.doubles or 0)
    triples = int(stats.triples or 0)
    hr = int(stats.home_runs or 0)

    avg = round(h / ab, 3) if ab > 0 else 0.0
    obp_denom = ab + bb + hbp + sf
    obp = round((h + bb + hbp) / obp_denom, 3) if obp_denom > 0 else 0.0
    singles = h - doubles - triples - hr
    tb = singles + 2 * doubles + 3 * triples + 4 * hr
    slg = round(tb / ab, 3) if ab > 0 else 0.0
    ops = round(obp + slg, 3)

    return BattingStatsResponse(
        player_name=player.full_name,
        player_id=player.id,
        at_bats=ab,
        runs=int(stats.runs or 0),
        hits=h,
        doubles=doubles,
        triples=triples,
        home_runs=hr,
        rbi=int(stats.rbi or 0),
        walks=bb,
        strikeouts=int(stats.strikeouts or 0),
        stolen_bases=int(stats.stolen_bases or 0),
        plate_appearances=int(stats.plate_appearances or 0),
        avg=avg,
        obp=obp,
        slg=slg,
        ops=ops,
    )


@players_router.get("/{player_id}/pitching-stats", response_model=PitchingStatsResponse)
def get_player_pitching_stats(player_id: int, db: Session = Depends(get_db)):
    """Get player's season pitching stats (aggregated)."""
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    stats = db.query(
        func.sum(PitchingStats.innings_pitched).label("ip"),
        func.sum(PitchingStats.hits_allowed).label("hits"),
        func.sum(PitchingStats.runs_allowed).label("runs"),
        func.sum(PitchingStats.earned_runs).label("er"),
        func.sum(PitchingStats.walks_allowed).label("bb"),
        func.sum(PitchingStats.strikeouts).label("so"),
        func.sum(PitchingStats.home_runs_allowed).label("hr"),
        func.sum(PitchingStats.pitches_thrown).label("pitches"),
        func.count().filter(PitchingStats.win == True).label("wins"),
        func.count().filter(PitchingStats.loss == True).label("losses"),
        func.count().filter(PitchingStats.save == True).label("saves"),
    ).filter(PitchingStats.player_id == player_id).first()

    if not stats or stats.ip is None:
        return PitchingStatsResponse(player_name=player.full_name, player_id=player.id)

    ip = float(stats.ip or 0)
    er = int(stats.er or 0)
    h = int(stats.hits or 0)
    bb = int(stats.bb or 0)

    era = round((er / ip) * 9, 2) if ip > 0 else 0.0
    whip = round((bb + h) / ip, 2) if ip > 0 else 0.0

    return PitchingStatsResponse(
        player_name=player.full_name,
        player_id=player.id,
        innings_pitched=ip,
        hits_allowed=h,
        runs_allowed=int(stats.runs or 0),
        earned_runs=er,
        walks_allowed=bb,
        strikeouts=int(stats.so or 0),
        home_runs_allowed=int(stats.hr or 0),
        pitches_thrown=int(stats.pitches or 0),
        era=era,
        whip=whip,
        wins=int(stats.wins or 0),
        losses=int(stats.losses or 0),
        saves=int(stats.saves or 0),
    )


@players_router.get("/{player_id}/gamelog", response_model=List[PlayerGameLog])
def get_player_gamelog(
    player_id: int,
    limit: int = Query(30, ge=1, le=162),
    db: Session = Depends(get_db)
):
    """Get player's recent game log."""
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    is_pitcher = player.primary_position == "P"
    
    if is_pitcher:
        games_stats = (
            db.query(PitchingStats, Game)
            .join(Game, PitchingStats.game_id == Game.id)
            .filter(PitchingStats.player_id == player_id)
            .order_by(desc(Game.game_date))
            .limit(limit)
            .all()
        )
    else:
        games_stats = (
            db.query(BattingStats, Game)
            .join(Game, BattingStats.game_id == Game.id)
            .filter(BattingStats.player_id == player_id)
            .order_by(desc(Game.game_date))
            .limit(limit)
            .all()
        )

    results = []
    for stat_obj, game in games_stats:
        # Determine opponent
        if stat_obj.team_id == game.home_team_id:
            opp_team = db.query(Team).filter(Team.id == game.away_team_id).first()
            is_home = True
        else:
            opp_team = db.query(Team).filter(Team.id == game.home_team_id).first()
            is_home = False

        if is_pitcher:
            ps = stat_obj
            results.append(PlayerGameLog(
                game_date=game.game_date,
                opponent=opp_team.name if opp_team else "Unknown",
                opponent_abbr=opp_team.abbreviation if opp_team else "???",
                is_home=is_home,
                is_pitcher=True,
                innings_pitched=ps.innings_pitched,
                hits_allowed=ps.hits_allowed,
                runs_allowed=ps.runs_allowed,
                earned_runs=ps.earned_runs,
                pitching_strikeouts=ps.strikeouts,
            ))
        else:
            bs = stat_obj
            avg = round(bs.hits / bs.at_bats, 3) if bs.at_bats > 0 else 0.0
            results.append(PlayerGameLog(
                game_date=game.game_date,
                opponent=opp_team.name if opp_team else "Unknown",
                opponent_abbr=opp_team.abbreviation if opp_team else "???",
                is_home=is_home,
                is_pitcher=False,
                at_bats=bs.at_bats,
                hits=bs.hits,
                home_runs=bs.home_runs,
                rbi=bs.rbi,
                walks=bs.walks,
                strikeouts=bs.strikeouts,
                avg=avg,
            ))

    return results


@players_router.get("/{player_id}/savant-stats", response_model=Optional[SavantStatsResponse])
def get_player_savant_stats(player_id: int, db: Session = Depends(get_db)):
    """Get player's Baseball Savant/Statcast advanced metrics."""
    s_stats = db.query(SavantStats).filter(SavantStats.player_id == player_id).first()
    return s_stats


# ──────────────────────────────────────────────
# Games Router
# ──────────────────────────────────────────────
games_router = APIRouter(prefix="/api/games", tags=["Games"])


@games_router.get("", response_model=List[GameListItem])
def get_games(
    date: Optional[str] = None,
    team_id: Optional[int] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Get games with optional date/team filtering."""
    query = db.query(Game)

    if date:
        try:
            game_date = datetime.strptime(date, "%Y-%m-%d").date()
            query = query.filter(Game.game_date == game_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    if team_id:
        query = query.filter(or_(Game.home_team_id == team_id, Game.away_team_id == team_id))

    if status:
        query = query.filter(Game.status == status)

    games = query.order_by(desc(Game.game_date)).offset((page - 1) * per_page).limit(per_page).all()

    results = []
    for g in games:
        home = db.query(Team).filter(Team.id == g.home_team_id).first()
        away = db.query(Team).filter(Team.id == g.away_team_id).first()

        home_win_prob, away_win_prob = 50, 50
        if home and away:
            home_win_prob, away_win_prob = calculate_rolling_prediction(db, home.id, away.id, g.game_date)

        results.append(GameListItem(
            id=g.id,
            mlb_game_pk=g.mlb_game_pk,
            game_date=g.game_date,
            status=g.status,
            home_team_name=home.name if home else "Unknown",
            home_team_abbr=home.abbreviation if home else "???",
            away_team_name=away.name if away else "Unknown",
            away_team_abbr=away.abbreviation if away else "???",
            home_score=g.home_score,
            away_score=g.away_score,
            venue=g.venue,
            home_logo=home.logo_url if home else None,
            away_logo=away.logo_url if away else None,
            home_win_prob=home_win_prob,
            away_win_prob=away_win_prob,
        ))

    return results


@games_router.get("/{game_id}", response_model=GameResponse)
def get_game(game_id: int, db: Session = Depends(get_db)):
    """Get single game details."""
    game = db.query(Game).options(
        joinedload(Game.home_team),
        joinedload(Game.away_team),
    ).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
        
    home_win_prob, away_win_prob = calculate_rolling_prediction(db, game.home_team_id, game.away_team_id, game.game_date)
    game.home_win_prob = home_win_prob
    game.away_win_prob = away_win_prob
    return game


# ──────────────────────────────────────────────
# Standings Router
# ──────────────────────────────────────────────
standings_router = APIRouter(prefix="/api/standings", tags=["Standings"])


@standings_router.get("", response_model=List[DivisionStandings])
def get_standings(season: int = 2024, db: Session = Depends(get_db)):
    """Get league standings grouped by division."""
    standings = (
        db.query(TeamStandings, Team)
        .join(Team, TeamStandings.team_id == Team.id)
        .filter(TeamStandings.season == season)
        .order_by(Team.league, Team.division, TeamStandings.division_rank)
        .all()
    )

    # Group by division
    divisions = {}
    for s, t in standings:
        div_key = f"{t.league} {t.division}"
        if div_key not in divisions:
            divisions[div_key] = {
                "division": t.division,
                "league": t.league,
                "teams": []
            }

        divisions[div_key]["teams"].append(StandingsEntry(
            team=TeamResponse(
                id=t.id,
                mlb_id=t.mlb_id,
                name=t.name,
                abbreviation=t.abbreviation,
                league=t.league,
                division=t.division,
                venue_name=t.venue_name,
                logo_url=t.logo_url,
            ),
            wins=s.wins,
            losses=s.losses,
            win_pct=s.win_pct,
            games_back=s.games_back,
            runs_scored=s.runs_scored,
            runs_allowed=s.runs_allowed,
            run_diff=s.run_diff,
            division_rank=s.division_rank,
            streak=s.streak,
        ))

    return [DivisionStandings(**v) for v in divisions.values()]


# ──────────────────────────────────────────────
# Stats/Analysis Router
# ──────────────────────────────────────────────
analysis_router = APIRouter(prefix="/api/analysis", tags=["Analysis"])


@analysis_router.get("/leaders/batting")
def get_batting_leaders(
    stat: str = Query("home_runs", description="Stat to rank by"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get batting leaderboard."""
    stat_column_map = {
        "home_runs": func.sum(BattingStats.home_runs),
        "rbi": func.sum(BattingStats.rbi),
        "hits": func.sum(BattingStats.hits),
        "stolen_bases": func.sum(BattingStats.stolen_bases),
        "runs": func.sum(BattingStats.runs),
        "walks": func.sum(BattingStats.walks),
    }

    if stat not in stat_column_map:
        raise HTTPException(status_code=400, detail=f"Invalid stat. Choose from: {list(stat_column_map.keys())}")

    stat_col = stat_column_map[stat]

    results = (
        db.query(
            Player.id,
            Player.full_name,
            Player.primary_position,
            Player.headshot_url,
            Team.abbreviation.label("team"),
            stat_col.label("value"),
            func.sum(BattingStats.at_bats).label("at_bats"),
            func.sum(BattingStats.hits).label("hits"),
        )
        .join(BattingStats, BattingStats.player_id == Player.id)
        .outerjoin(Team, Player.team_id == Team.id)
        .group_by(Player.id)
        .having(func.sum(BattingStats.at_bats) >= 5)
        .order_by(desc("value"))
        .limit(limit)
        .all()
    )

    return [
        {
            "rank": i + 1,
            "player_id": r.id,
            "player_name": r.full_name,
            "position": r.primary_position,
            "headshot_url": r.headshot_url,
            "team": r.team,
            "value": int(r.value),
            "avg": round(int(r.hits) / int(r.at_bats), 3) if int(r.at_bats) > 0 else 0.0,
        }
        for i, r in enumerate(results)
    ]


@analysis_router.get("/leaders/pitching")
def get_pitching_leaders(
    stat: str = Query("strikeouts", description="Stat to rank by"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get pitching leaderboard."""
    stat_column_map = {
        "strikeouts": func.sum(PitchingStats.strikeouts),
        "wins": func.count().filter(PitchingStats.win == True),
        "saves": func.count().filter(PitchingStats.save == True),
    }

    if stat not in stat_column_map:
        raise HTTPException(status_code=400, detail=f"Invalid stat. Choose from: {list(stat_column_map.keys())}")

    results = (
        db.query(
            Player.id,
            Player.full_name,
            Player.headshot_url,
            Team.abbreviation.label("team"),
            stat_column_map[stat].label("value"),
            func.sum(PitchingStats.innings_pitched).label("ip"),
            func.sum(PitchingStats.earned_runs).label("er"),
        )
        .join(PitchingStats, PitchingStats.player_id == Player.id)
        .outerjoin(Team, Player.team_id == Team.id)
        .group_by(Player.id)
        .having(func.sum(PitchingStats.innings_pitched) >= 1.0)
        .order_by(desc("value"))
        .limit(limit)
        .all()
    )

    return [
        {
            "rank": i + 1,
            "player_id": r.id,
            "player_name": r.full_name,
            "headshot_url": r.headshot_url,
            "team": r.team,
            "value": int(r.value),
            "era": round((int(r.er) / float(r.ip)) * 9, 2) if float(r.ip) > 0 else 0.0,
        }
        for i, r in enumerate(results)
    ]


@analysis_router.get("/summary")
def get_data_summary(db: Session = Depends(get_db)):
    """Get database summary stats."""
    return {
        "teams": db.query(Team).count(),
        "players": db.query(Player).filter(Player.active == True).count(),
        "games": db.query(Game).count(),
        "completed_games": db.query(Game).filter(Game.status == "Final").count(),
        "batting_records": db.query(BattingStats).count(),
        "pitching_records": db.query(PitchingStats).count(),
        "season": 2024,
    }


@analysis_router.get("/leaders/savant")
def get_savant_leaders(
    stat: str = Query("avg_exit_velocity", description="Savant stat to rank by"),
    player_type: str = Query("batter", description="Rank batters or pitchers ('batter' or 'pitcher')"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get Savant advanced metrics leaderboard."""
    valid_stats = ["avg_exit_velocity", "max_exit_velocity", "avg_launch_angle", "barrel_rate", "xba", "xslg", "xwoba"]
    if stat not in valid_stats:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid stat. Choose from: {valid_stats}"
        )
    
    is_pitcher = player_type == "pitcher"
    stat_column = getattr(SavantStats, stat)
    
    results = (
        db.query(
            Player.id,
            Player.full_name,
            Player.primary_position,
            Player.headshot_url,
            Team.abbreviation.label("team"),
            stat_column.label("value")
        )
        .join(SavantStats, SavantStats.player_id == Player.id)
        .outerjoin(Team, Player.team_id == Team.id)
        .filter(SavantStats.is_pitcher == is_pitcher)
        .filter(stat_column.isnot(None))
        .order_by(desc("value"))
        .limit(limit)
        .all()
    )
    
    return [
        {
            "rank": i + 1,
            "player_id": r.id,
            "player_name": r.full_name,
            "position": r.primary_position,
            "headshot_url": r.headshot_url,
            "team": r.team,
            "value": r.value,
        }
        for i, r in enumerate(results)
    ]


@analysis_router.get("/leaderboard/batting")
def get_batting_leaderboard(
    sort: str = Query("home_runs", description="Stat to sort by"),
    order: str = Query("desc", description="Sort order: 'desc' or 'asc'"),
    min_pa: int = Query(50, ge=0, description="Minimum plate appearances"),
    limit: int = Query(50, ge=1, le=200),
    page: int = Query(1, ge=1),
    team: Optional[str] = Query(None, description="Filter by team abbreviation"),
    position: Optional[str] = Query(None, description="Filter by position"),
    db: Session = Depends(get_db)
):
    """Comprehensive batting leaderboard with all computed stats."""
    base_query = (
        db.query(
            Player.id.label("player_id"),
            Player.full_name.label("player_name"),
            Player.primary_position.label("position"),
            Player.headshot_url,
            Team.abbreviation.label("team"),
            func.sum(BattingStats.plate_appearances).label("pa"),
            func.sum(BattingStats.at_bats).label("ab"),
            func.sum(BattingStats.hits).label("h"),
            func.sum(BattingStats.doubles).label("doubles"),
            func.sum(BattingStats.triples).label("triples"),
            func.sum(BattingStats.home_runs).label("home_runs"),
            func.sum(BattingStats.runs).label("runs"),
            func.sum(BattingStats.rbi).label("rbi"),
            func.sum(BattingStats.walks).label("walks"),
            func.sum(BattingStats.strikeouts).label("strikeouts"),
            func.sum(BattingStats.stolen_bases).label("stolen_bases"),
            func.sum(BattingStats.caught_stealing).label("caught_stealing"),
            func.sum(BattingStats.hit_by_pitch).label("hbp"),
            func.sum(BattingStats.sacrifice_flies).label("sf"),
        )
        .join(BattingStats, BattingStats.player_id == Player.id)
        .outerjoin(Team, Player.team_id == Team.id)
        .group_by(Player.id)
        .having(func.sum(BattingStats.plate_appearances) >= min_pa)
    )

    if team:
        base_query = base_query.filter(Team.abbreviation == team)
    if position:
        base_query = base_query.filter(Player.primary_position == position)

    # For sort, computed columns need special handling
    sort_map = {
        "home_runs": func.sum(BattingStats.home_runs),
        "rbi": func.sum(BattingStats.rbi),
        "hits": func.sum(BattingStats.hits),
        "runs": func.sum(BattingStats.runs),
        "stolen_bases": func.sum(BattingStats.stolen_bases),
        "walks": func.sum(BattingStats.walks),
        "strikeouts": func.sum(BattingStats.strikeouts),
        "doubles": func.sum(BattingStats.doubles),
        "triples": func.sum(BattingStats.triples),
        "pa": func.sum(BattingStats.plate_appearances),
        "ab": func.sum(BattingStats.at_bats),
        "avg": cast(func.sum(BattingStats.hits), Float) / func.nullif(func.sum(BattingStats.at_bats), 0),
        "obp": (cast(func.sum(BattingStats.hits) + func.sum(BattingStats.walks) + func.sum(BattingStats.hit_by_pitch), Float))
               / func.nullif(func.sum(BattingStats.at_bats) + func.sum(BattingStats.walks) + func.sum(BattingStats.hit_by_pitch) + func.sum(BattingStats.sacrifice_flies), 0),
        "slg": (cast(
                    func.sum(BattingStats.hits) - func.sum(BattingStats.doubles) - func.sum(BattingStats.triples) - func.sum(BattingStats.home_runs)
                    + func.sum(BattingStats.doubles) * 2
                    + func.sum(BattingStats.triples) * 3
                    + func.sum(BattingStats.home_runs) * 4, Float)
               ) / func.nullif(func.sum(BattingStats.at_bats), 0),
    }

    sort_col = sort_map.get(sort, sort_map["home_runs"])
    if order == "asc":
        base_query = base_query.order_by(sort_col.asc())
    else:
        base_query = base_query.order_by(sort_col.desc())

    # Get total count
    count_query = base_query.subquery()
    total = db.query(func.count()).select_from(count_query).scalar()

    # Apply pagination
    offset = (page - 1) * limit
    results = base_query.offset(offset).limit(limit).all()

    data = []
    for i, r in enumerate(results):
        ab = int(r.ab or 0)
        h = int(r.h or 0)
        bb = int(r.walks or 0)
        hbp = int(r.hbp or 0)
        sf = int(r.sf or 0)
        doubles = int(r.doubles or 0)
        triples = int(r.triples or 0)
        hr = int(r.home_runs or 0)
        singles = h - doubles - triples - hr

        avg = round(h / ab, 3) if ab > 0 else 0.0
        obp = round((h + bb + hbp) / (ab + bb + hbp + sf), 3) if (ab + bb + hbp + sf) > 0 else 0.0
        slg = round((singles + doubles * 2 + triples * 3 + hr * 4) / ab, 3) if ab > 0 else 0.0
        ops = round(obp + slg, 3)

        data.append({
            "rank": offset + i + 1,
            "player_id": r.player_id,
            "player_name": r.player_name,
            "position": r.position,
            "headshot_url": r.headshot_url,
            "team": r.team,
            "pa": int(r.pa or 0),
            "ab": ab,
            "h": h,
            "doubles": doubles,
            "triples": triples,
            "home_runs": hr,
            "runs": int(r.runs or 0),
            "rbi": int(r.rbi or 0),
            "walks": bb,
            "strikeouts": int(r.strikeouts or 0),
            "stolen_bases": int(r.stolen_bases or 0),
            "caught_stealing": int(r.caught_stealing or 0),
            "avg": avg,
            "obp": obp,
            "slg": slg,
            "ops": ops,
        })

    return {
        "total": total or 0,
        "page": page,
        "per_page": limit,
        "data": data,
    }


@analysis_router.get("/leaderboard/pitching")
def get_pitching_leaderboard(
    sort: str = Query("strikeouts", description="Stat to sort by"),
    order: str = Query("desc", description="Sort order: 'desc' or 'asc'"),
    min_ip: float = Query(10.0, ge=0, description="Minimum innings pitched"),
    limit: int = Query(50, ge=1, le=200),
    page: int = Query(1, ge=1),
    team: Optional[str] = Query(None, description="Filter by team abbreviation"),
    db: Session = Depends(get_db)
):
    """Comprehensive pitching leaderboard with all computed stats."""
    base_query = (
        db.query(
            Player.id.label("player_id"),
            Player.full_name.label("player_name"),
            Player.primary_position.label("position"),
            Player.headshot_url,
            Team.abbreviation.label("team"),
            func.sum(PitchingStats.innings_pitched).label("ip"),
            func.sum(PitchingStats.hits_allowed).label("h"),
            func.sum(PitchingStats.runs_allowed).label("r"),
            func.sum(PitchingStats.earned_runs).label("er"),
            func.sum(PitchingStats.walks_allowed).label("bb"),
            func.sum(PitchingStats.strikeouts).label("strikeouts"),
            func.sum(PitchingStats.home_runs_allowed).label("hr"),
            func.sum(PitchingStats.pitches_thrown).label("pitches"),
            func.sum(PitchingStats.strikes).label("strikes"),
            func.count().filter(PitchingStats.win == True).label("wins"),
            func.count().filter(PitchingStats.loss == True).label("losses"),
            func.count().filter(PitchingStats.save == True).label("saves"),
            func.count().filter(PitchingStats.hold == True).label("holds"),
            func.count().filter(PitchingStats.blown_save == True).label("blown_saves"),
            func.count(PitchingStats.id).label("games"),
            func.count().filter(PitchingStats.is_starter == True).label("games_started"),
        )
        .join(PitchingStats, PitchingStats.player_id == Player.id)
        .outerjoin(Team, Player.team_id == Team.id)
        .group_by(Player.id)
        .having(func.sum(PitchingStats.innings_pitched) >= min_ip)
    )

    if team:
        base_query = base_query.filter(Team.abbreviation == team)

    sort_map = {
        "strikeouts": func.sum(PitchingStats.strikeouts),
        "wins": func.count().filter(PitchingStats.win == True),
        "saves": func.count().filter(PitchingStats.save == True),
        "holds": func.count().filter(PitchingStats.hold == True),
        "ip": func.sum(PitchingStats.innings_pitched),
        "era": func.sum(PitchingStats.earned_runs) * 9.0 / func.nullif(func.sum(PitchingStats.innings_pitched), 0),
        "whip": (cast(func.sum(PitchingStats.walks_allowed) + func.sum(PitchingStats.hits_allowed), Float))
                / func.nullif(func.sum(PitchingStats.innings_pitched), 0),
        "k9": func.sum(PitchingStats.strikeouts) * 9.0 / func.nullif(func.sum(PitchingStats.innings_pitched), 0),
        "bb9": func.sum(PitchingStats.walks_allowed) * 9.0 / func.nullif(func.sum(PitchingStats.innings_pitched), 0),
        "hr_allowed": func.sum(PitchingStats.home_runs_allowed),
        "pitches": func.sum(PitchingStats.pitches_thrown),
    }

    sort_col = sort_map.get(sort, sort_map["strikeouts"])
    # ERA, WHIP, bb9 should default ascending
    if sort in ["era", "whip", "bb9"] and order == "desc":
        order = "asc"

    if order == "asc":
        base_query = base_query.order_by(sort_col.asc())
    else:
        base_query = base_query.order_by(sort_col.desc())

    count_query = base_query.subquery()
    total = db.query(func.count()).select_from(count_query).scalar()

    offset = (page - 1) * limit
    results = base_query.offset(offset).limit(limit).all()

    data = []
    for i, r in enumerate(results):
        ip = float(r.ip or 0)
        er = int(r.er or 0)
        h = int(r.h or 0)
        bb = int(r.bb or 0)
        k = int(r.strikeouts or 0)

        era = round((er / ip) * 9, 2) if ip > 0 else 0.0
        whip = round((bb + h) / ip, 2) if ip > 0 else 0.0
        k9 = round((k / ip) * 9, 1) if ip > 0 else 0.0
        bb9 = round((bb / ip) * 9, 1) if ip > 0 else 0.0

        data.append({
            "rank": offset + i + 1,
            "player_id": r.player_id,
            "player_name": r.player_name,
            "position": r.position,
            "headshot_url": r.headshot_url,
            "team": r.team,
            "ip": round(ip, 1),
            "h": h,
            "r": int(r.r or 0),
            "er": er,
            "bb": bb,
            "strikeouts": k,
            "hr": int(r.hr or 0),
            "wins": int(r.wins or 0),
            "losses": int(r.losses or 0),
            "saves": int(r.saves or 0),
            "holds": int(r.holds or 0),
            "games": int(r.games or 0),
            "games_started": int(r.games_started or 0),
            "era": era,
            "whip": whip,
            "k9": k9,
            "bb9": bb9,
        })

    return {
        "total": total or 0,
        "page": page,
        "per_page": limit,
        "data": data,
    }

@analysis_router.get("/leaderboard/savant")
def get_savant_leaderboard(
    is_pitcher: bool = Query(False, description="True for pitchers, False for batters"),
    sort: str = Query("avg_exit_velocity", description="Stat to sort by"),
    order: str = Query("desc", description="Sort order: 'desc' or 'asc'"),
    limit: int = Query(50, ge=1, le=200),
    page: int = Query(1, ge=1),
    team: Optional[str] = Query(None, description="Filter by team abbreviation"),
    db: Session = Depends(get_db)
):
    """Savant leaderboard."""
    base_query = (
        db.query(
            Player.id.label("player_id"),
            Player.full_name.label("player_name"),
            Player.primary_position.label("position"),
            Player.headshot_url,
            Team.abbreviation.label("team"),
            SavantStats.avg_exit_velocity,
            SavantStats.max_exit_velocity,
            SavantStats.avg_launch_angle,
            SavantStats.barrel_rate,
            SavantStats.xba,
            SavantStats.xslg,
            SavantStats.xwoba,
        )
        .join(SavantStats, SavantStats.player_id == Player.id)
        .outerjoin(Team, Player.team_id == Team.id)
        .filter(SavantStats.is_pitcher == is_pitcher)
    )

    if team:
        base_query = base_query.filter(Team.abbreviation == team)

    sort_map = {
        "avg_exit_velocity": SavantStats.avg_exit_velocity,
        "max_exit_velocity": SavantStats.max_exit_velocity,
        "avg_launch_angle": SavantStats.avg_launch_angle,
        "barrel_rate": SavantStats.barrel_rate,
        "xba": SavantStats.xba,
        "xslg": SavantStats.xslg,
        "xwoba": SavantStats.xwoba,
    }

    sort_col = sort_map.get(sort, sort_map["avg_exit_velocity"])

    if order == "asc":
        base_query = base_query.order_by(sort_col.asc().nulls_last())
    else:
        base_query = base_query.order_by(sort_col.desc().nulls_last())

    total = base_query.count()

    offset = (page - 1) * limit
    results = base_query.offset(offset).limit(limit).all()

    data = []
    for i, r in enumerate(results):
        data.append({
            "rank": offset + i + 1,
            "player_id": r.player_id,
            "player_name": r.player_name,
            "position": r.position,
            "headshot_url": r.headshot_url,
            "team": r.team,
            "avg_exit_velocity": r.avg_exit_velocity,
            "max_exit_velocity": r.max_exit_velocity,
            "avg_launch_angle": r.avg_launch_angle,
            "barrel_rate": r.barrel_rate,
            "xba": r.xba,
            "xslg": r.xslg,
            "xwoba": r.xwoba,
        })

    return {
        "total": total or 0,
        "page": page,
        "per_page": limit,
        "data": data,
    }


# ──────────────────────────────────────────────
# GenAI Router — AI-Powered Analysis
# ──────────────────────────────────────────────
genai_router = APIRouter(prefix="/api/genai", tags=["GenAI"])


@genai_router.get("/player/{player_id}/analysis")
def get_genai_player_analysis(player_id: int, db: Session = Depends(get_db)):
    """Generate AI-powered natural language analysis for a player."""
    player = db.query(Player).options(
        joinedload(Player.team), joinedload(Player.savant_stats)
    ).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    # Fetch batting stats
    batting_raw = db.query(
        func.sum(BattingStats.at_bats).label("at_bats"),
        func.sum(BattingStats.hits).label("hits"),
        func.sum(BattingStats.home_runs).label("home_runs"),
        func.sum(BattingStats.rbi).label("rbi"),
        func.sum(BattingStats.walks).label("walks"),
        func.sum(BattingStats.strikeouts).label("strikeouts"),
        func.sum(BattingStats.stolen_bases).label("stolen_bases"),
        func.sum(BattingStats.plate_appearances).label("plate_appearances"),
        func.sum(BattingStats.doubles).label("doubles"),
        func.sum(BattingStats.triples).label("triples"),
        func.sum(BattingStats.hit_by_pitch).label("hbp"),
        func.sum(BattingStats.sacrifice_flies).label("sf"),
    ).filter(BattingStats.player_id == player_id).first()

    batting = None
    if batting_raw and batting_raw.at_bats and int(batting_raw.at_bats) > 0:
        ab = int(batting_raw.at_bats)
        h = int(batting_raw.hits or 0)
        bb = int(batting_raw.walks or 0)
        hbp = int(batting_raw.hbp or 0)
        sf = int(batting_raw.sf or 0)
        doubles = int(batting_raw.doubles or 0)
        triples = int(batting_raw.triples or 0)
        hr = int(batting_raw.home_runs or 0)
        singles = h - doubles - triples - hr
        tb = singles + 2 * doubles + 3 * triples + 4 * hr
        avg = round(h / ab, 3) if ab > 0 else 0.0
        obp_denom = ab + bb + hbp + sf
        obp = round((h + bb + hbp) / obp_denom, 3) if obp_denom > 0 else 0.0
        slg = round(tb / ab, 3) if ab > 0 else 0.0

        batting = {
            "at_bats": ab, "hits": h, "home_runs": hr,
            "rbi": int(batting_raw.rbi or 0),
            "walks": bb, "strikeouts": int(batting_raw.strikeouts or 0),
            "stolen_bases": int(batting_raw.stolen_bases or 0),
            "plate_appearances": int(batting_raw.plate_appearances or 0),
            "doubles": doubles, "triples": triples,
            "avg": avg, "obp": obp, "slg": slg, "ops": round(obp + slg, 3),
        }

    # Fetch pitching stats
    pitching_raw = db.query(
        func.sum(PitchingStats.innings_pitched).label("ip"),
        func.sum(PitchingStats.earned_runs).label("er"),
        func.sum(PitchingStats.hits_allowed).label("ha"),
        func.sum(PitchingStats.walks_allowed).label("bb"),
        func.sum(PitchingStats.strikeouts).label("so"),
        func.sum(PitchingStats.home_runs_allowed).label("hr"),
        func.count().filter(PitchingStats.win == True).label("wins"),
        func.count().filter(PitchingStats.loss == True).label("losses"),
    ).filter(PitchingStats.player_id == player_id).first()

    pitching = None
    if pitching_raw and pitching_raw.ip and float(pitching_raw.ip) > 0:
        ip = float(pitching_raw.ip)
        er = int(pitching_raw.er or 0)
        pitching = {
            "innings_pitched": ip,
            "era": round(er / ip * 9, 2) if ip > 0 else 0.0,
            "whip": round((int(pitching_raw.bb or 0) + int(pitching_raw.ha or 0)) / ip, 2) if ip > 0 else 0.0,
            "strikeouts": int(pitching_raw.so or 0),
            "wins": int(pitching_raw.wins or 0),
            "losses": int(pitching_raw.losses or 0),
            "walks_allowed": int(pitching_raw.bb or 0),
            "home_runs_allowed": int(pitching_raw.hr or 0),
        }

    # Savant stats
    savant = None
    if player.savant_stats:
        s = player.savant_stats
        savant = {
            "avg_exit_velocity": s.avg_exit_velocity,
            "max_exit_velocity": s.max_exit_velocity,
            "barrel_rate": s.barrel_rate,
            "xba": s.xba, "xslg": s.xslg, "xwoba": s.xwoba,
        }

    player_dict = {
        "full_name": player.full_name,
        "primary_position": player.primary_position,
        "team_name": player.team.name if player.team else "",
    }

    result = generate_player_analysis(player_dict, batting, pitching, savant)
    return result


@genai_router.get("/game/{game_id}/analysis")
def get_genai_game_analysis(game_id: int, db: Session = Depends(get_db)):
    """Generate AI-powered natural language analysis for a game."""
    game = db.query(Game).options(
        joinedload(Game.home_team), joinedload(Game.away_team)
    ).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    home_prob, away_prob = calculate_rolling_prediction(
        db, game.home_team_id, game.away_team_id, game.game_date
    )

    game_dict = {
        "game_date": str(game.game_date),
        "home_team_name": game.home_team.name if game.home_team else "Home",
        "home_team_abbr": game.home_team.abbreviation if game.home_team else "???",
        "away_team_name": game.away_team.name if game.away_team else "Away",
        "away_team_abbr": game.away_team.abbreviation if game.away_team else "???",
        "home_score": game.home_score,
        "away_score": game.away_score,
        "status": game.status,
        "venue": game.venue or "",
    }

    result = generate_game_analysis(game_dict, home_prob, away_prob)
    return result


# ──────────────────────────────────────────────
# ML Metrics & SHAP Router
# ──────────────────────────────────────────────
ml_router = APIRouter(prefix="/api/ml", tags=["ML & SHAP"])


@ml_router.get("/status")
def get_ml_status():
    """Check ML model loading status."""
    _load_ml_artifacts()  # Try to load if not yet loaded
    return {
        "model_loaded": _rf_model is not None,
        "feature_names": _feature_names,
        "has_training_metrics": _training_metrics is not None,
        "has_shap_results": _shap_results is not None,
        "model_type": "RandomForestClassifier" if _rf_model is not None else None,
    }


@ml_router.get("/metrics")
def get_training_metrics():
    """Get training metrics (accuracy, precision, recall, F1, AUC-ROC)."""
    _load_ml_artifacts()
    if not _training_metrics:
        return {
            "status": "not_available",
            "message": "Training metrics not found. Run train_model.py first.",
        }
    return _training_metrics


@ml_router.get("/shap")
def get_shap_results():
    """Get SHAP feature importance analysis results."""
    _load_ml_artifacts()
    if not _shap_results:
        return {
            "status": "not_available",
            "message": "SHAP results not found. Run train_model.py first.",
        }
    return _shap_results


@ml_router.get("/shap/plot/{plot_name}")
def get_shap_plot(plot_name: str):
    """Get SHAP plot image path. plot_name: 'summary', 'bar', 'roc_curve', 'confusion_matrix'."""
    plot_map = {
        "summary": "shap_summary.png",
        "bar": "shap_bar.png",
        "roc_curve": "roc_curve.png",
        "confusion_matrix": "confusion_matrix.png",
    }
    filename = plot_map.get(plot_name)
    if not filename:
        raise HTTPException(status_code=400, detail=f"Invalid plot name. Choose from: {list(plot_map.keys())}")

    plot_path = PLOTS_DIR / filename
    if not plot_path.exists():
        raise HTTPException(status_code=404, detail=f"Plot not found. Run train_model.py first.")

    from fastapi.responses import FileResponse
    return FileResponse(str(plot_path), media_type="image/png")

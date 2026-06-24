"""
MLB Data Pipeline — Fetches data from MLB Stats API and pybaseball
Populates the SQLite database with 2024 season data.
"""

import sys
import os
import time
import logging
import socket
from datetime import datetime, date, timedelta

# Set global socket timeout to prevent hanging on network requests
socket.setdefaulttimeout(30)

import statsapi
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database.models import (
    Base, Team, Player, Game, BattingStats, PitchingStats, TeamStandings,
    engine, SessionLocal
)

# ──────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

SEASON = int(os.getenv("MLB_SEASON", "2024"))


# ──────────────────────────────────────────────
# Helper: safe get from nested dicts
# ──────────────────────────────────────────────
def safe_get(d, *keys, default=None):
    """Safely navigate nested dictionaries."""
    for key in keys:
        if isinstance(d, dict):
            d = d.get(key, default)
        else:
            return default
    return d


# ──────────────────────────────────────────────
# 1. Fetch Teams
# ──────────────────────────────────────────────
def fetch_teams(session):
    """Fetch all 30 MLB teams and insert into database."""
    logger.info("📋 Fetching MLB teams...")

    teams_data = statsapi.get("teams", {"sportId": 1, "season": SEASON})
    teams = teams_data.get("teams", [])

    count = 0
    for t in teams:
        existing = session.query(Team).filter_by(mlb_id=t["id"]).first()
        if existing:
            existing.name = t.get("name", "")
            existing.abbreviation = t.get("abbreviation", "")
            existing.league = safe_get(t, "league", "abbreviation", default="")
            existing.division = safe_get(t, "division", "name", default="").replace(" ", " ").split()[-1] if safe_get(t, "division", "name") else ""
            existing.venue_name = safe_get(t, "venue", "name", default="")
        else:
            team = Team(
                mlb_id=t["id"],
                name=t.get("name", ""),
                abbreviation=t.get("abbreviation", ""),
                league=safe_get(t, "league", "abbreviation", default=""),
                division=safe_get(t, "division", "name", default="").split()[-1] if safe_get(t, "division", "name") else "",
                venue_name=safe_get(t, "venue", "name", default=""),
                logo_url=f"https://www.mlbstatic.com/team-logos/{t['id']}.svg"
            )
            session.add(team)
            count += 1

    session.commit()
    logger.info(f"✅ Teams: {count} new, {len(teams)} total")
    return len(teams)


# ──────────────────────────────────────────────
# 2. Fetch Players (Rosters)
# ──────────────────────────────────────────────
def fetch_players(session):
    """Fetch rosters for all teams and insert players."""
    logger.info("👤 Fetching player rosters...")

    teams = session.query(Team).all()
    total_new = 0

    for team in teams:
        try:
            roster = statsapi.get(
                "team_roster",
                {"teamId": team.mlb_id, "season": SEASON, "rosterType": "fullSeason"}
            )
        except Exception as e:
            logger.warning(f"⚠️ Failed to fetch roster for {team.name}: {e}")
            # Try 40-man roster as fallback
            try:
                roster = statsapi.get(
                    "team_roster",
                    {"teamId": team.mlb_id, "season": SEASON, "rosterType": "40Man"}
                )
            except Exception:
                logger.warning(f"⚠️ Skipping roster for {team.name}")
                continue

        players = roster.get("roster", [])

        for p in players:
            person = p.get("person", {})
            player_id = person.get("id")
            if not player_id:
                continue

            existing = session.query(Player).filter_by(mlb_id=player_id).first()

            # Get player details
            try:
                details = statsapi.get("person", {"personId": player_id})
                pinfo = details.get("people", [{}])[0]
            except Exception:
                pinfo = person

            birth_date_str = pinfo.get("birthDate", "")
            birth_date = None
            if birth_date_str:
                try:
                    birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d").date()
                except ValueError:
                    pass

            if existing:
                existing.team_id = team.id
                existing.full_name = pinfo.get("fullName", person.get("fullName", ""))
                existing.primary_position = safe_get(p, "position", "abbreviation", default=safe_get(pinfo, "primaryPosition", "abbreviation", default=""))
                existing.jersey_number = p.get("jerseyNumber", "")
                existing.active = pinfo.get("active", True)
            else:
                player = Player(
                    mlb_id=player_id,
                    full_name=pinfo.get("fullName", person.get("fullName", "")),
                    first_name=pinfo.get("firstName", ""),
                    last_name=pinfo.get("lastName", ""),
                    primary_position=safe_get(p, "position", "abbreviation",
                                              default=safe_get(pinfo, "primaryPosition", "abbreviation", default="")),
                    bats=safe_get(pinfo, "batSide", "code", default=""),
                    throws=safe_get(pinfo, "pitchHand", "code", default=""),
                    birth_date=birth_date,
                    birth_country=pinfo.get("birthCountry", ""),
                    height=pinfo.get("height", ""),
                    weight=pinfo.get("weight"),
                    team_id=team.id,
                    jersey_number=p.get("jerseyNumber", ""),
                    headshot_url=f"https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people/{player_id}/headshot/67/current",
                    active=pinfo.get("active", True),
                )
                session.add(player)
                total_new += 1

        session.commit()
        logger.info(f"  ✓ {team.abbreviation}: {len(players)} players")
        time.sleep(0.3)  # Rate limiting

    logger.info(f"✅ Players: {total_new} new players added")
    return total_new


# ──────────────────────────────────────────────
# 3. Fetch Games & Scores
# ──────────────────────────────────────────────
def fetch_games(session, start_date=None, end_date=None):
    """Fetch game schedule and scores for the season."""
    if start_date is None:
        start_date = f"{SEASON}-03-20"  # Spring training / opening
    if end_date is None:
        end_date = f"{SEASON}-11-05"    # World Series end

    logger.info(f"🏟️ Fetching games from {start_date} to {end_date}...")

    # Split date range into smaller chunks to avoid 503 timeouts from MLB API
    start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()

    chunks = []
    curr_dt = start_dt
    while curr_dt <= end_dt:
        chunk_end = min(curr_dt + timedelta(days=30), end_dt)
        chunks.append((curr_dt.strftime("%Y-%m-%d"), chunk_end.strftime("%Y-%m-%d")))
        curr_dt = chunk_end + timedelta(days=1)

    schedule = []
    for c_start, c_end in chunks:
        logger.info(f"  Fetching schedule chunk: {c_start} to {c_end}...")
        for attempt in range(3):
            try:
                chunk_schedule = statsapi.schedule(
                    start_date=c_start,
                    end_date=c_end,
                    sportId=1
                )
                schedule.extend(chunk_schedule)
                time.sleep(0.5)  # rate limiting sleep
                break
            except Exception as e:
                logger.warning(f"  Attempt {attempt+1} failed for {c_start} to {c_end}: {e}")
                if attempt == 2:
                    raise e
                time.sleep(2)

    count_new = 0
    count_updated = 0
    processed_game_pks = set()

    for g in schedule:
        game_pk = g.get("game_id")
        if not game_pk or game_pk in processed_game_pks:
            continue
        processed_game_pks.add(game_pk)

        # Look up team IDs
        home_team = session.query(Team).filter_by(mlb_id=g.get("home_id")).first()
        away_team = session.query(Team).filter_by(mlb_id=g.get("away_id")).first()

        if not home_team or not away_team:
            continue

        game_date_str = g.get("game_date", "")
        try:
            game_date = datetime.strptime(game_date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            continue

        game_type = g.get("game_type", "R")
        status = g.get("status", "")
        home_score = g.get("home_score")
        away_score = g.get("away_score")

        # Determine winner/loser
        winning_team_id = None
        losing_team_id = None
        if status == "Final" and home_score is not None and away_score is not None:
            if home_score > away_score:
                winning_team_id = home_team.id
                losing_team_id = away_team.id
            elif away_score > home_score:
                winning_team_id = away_team.id
                losing_team_id = home_team.id

        existing = session.query(Game).filter_by(mlb_game_pk=game_pk).first()

        if existing:
            existing.status = status
            existing.home_score = home_score
            existing.away_score = away_score
            existing.winning_team_id = winning_team_id
            existing.losing_team_id = losing_team_id
            count_updated += 1
        else:
            game = Game(
                mlb_game_pk=game_pk,
                game_date=game_date,
                status=status,
                home_team_id=home_team.id,
                away_team_id=away_team.id,
                home_score=home_score,
                away_score=away_score,
                venue=g.get("venue_name", ""),
                season=SEASON,
                game_type=game_type,
                winning_team_id=winning_team_id,
                losing_team_id=losing_team_id,
            )
            session.add(game)
            count_new += 1

    session.commit()
    logger.info(f"✅ Games: {count_new} new, {count_updated} updated, {len(schedule)} total")
    return count_new + count_updated


# ──────────────────────────────────────────────
# 4. Fetch Box Scores (Batting + Pitching Stats)
# ──────────────────────────────────────────────
def fetch_boxscores(session, limit=None):
    """Fetch detailed box scores for completed games."""
    logger.info("📊 Fetching box scores...")

    # Get games that are Final but don't have batting stats yet
    games = session.query(Game).filter(
        Game.status == "Final",
        Game.season == SEASON,
    ).all()

    if limit:
        games = games[:limit]

    count = 0
    errors = 0

    for game in games:
        # Check if we already have stats for this game
        existing_stats = session.query(BattingStats).filter_by(game_id=game.id).first()
        if existing_stats:
            continue

        try:
            boxscore = statsapi.boxscore_data(game.mlb_game_pk)
        except Exception as e:
            logger.warning(f"⚠️ Failed boxscore for game {game.mlb_game_pk}: {e}")
            errors += 1
            continue

        processed_batters = set()
        processed_pitchers = set()
        # Process both teams
        for side in ["home", "away"]:
            team_data = boxscore.get(side, {})
            team_mlb_id = safe_get(team_data, "team", "id")
            team = session.query(Team).filter_by(mlb_id=team_mlb_id).first() if team_mlb_id else None

            # Batting stats
            batters = team_data.get("batters", [])
            players_dict = team_data.get("players", {})

            for batter_id in batters:
                if batter_id in processed_batters:
                    continue
                processed_batters.add(batter_id)
                
                player_key = f"ID{batter_id}"
                if player_key not in players_dict:
                    continue

                stats = players_dict[player_key].get("stats", {}).get("batting", {})
                if not stats:
                    continue

                player = session.query(Player).filter_by(mlb_id=batter_id).first()
                if not player:
                    continue

                bs = BattingStats(
                    player_id=player.id,
                    game_id=game.id,
                    team_id=team.id if team else None,
                    at_bats=int(stats.get("atBats", 0)),
                    runs=int(stats.get("runs", 0)),
                    hits=int(stats.get("hits", 0)),
                    doubles=int(stats.get("doubles", 0)),
                    triples=int(stats.get("triples", 0)),
                    home_runs=int(stats.get("homeRuns", 0)),
                    rbi=int(stats.get("rbi", 0)),
                    walks=int(stats.get("baseOnBalls", 0)),
                    strikeouts=int(stats.get("strikeOuts", 0)),
                    stolen_bases=int(stats.get("stolenBases", 0)),
                    caught_stealing=int(stats.get("caughtStealing", 0)),
                    hit_by_pitch=int(stats.get("hitByPitch", 0)),
                    sacrifice_flies=int(stats.get("sacFlies", 0)),
                    plate_appearances=int(stats.get("plateAppearances", 0)) or (
                        int(stats.get("atBats", 0)) + int(stats.get("baseOnBalls", 0)) +
                        int(stats.get("hitByPitch", 0)) + int(stats.get("sacFlies", 0))
                    ),
                )
                session.add(bs)

            # Pitching stats
            pitchers = team_data.get("pitchers", [])

            for i, pitcher_id in enumerate(pitchers):
                if pitcher_id in processed_pitchers:
                    continue
                processed_pitchers.add(pitcher_id)
                
                player_key = f"ID{pitcher_id}"
                if player_key not in players_dict:
                    continue

                stats = players_dict[player_key].get("stats", {}).get("pitching", {})
                if not stats:
                    continue

                player = session.query(Player).filter_by(mlb_id=pitcher_id).first()
                if not player:
                    continue

                # Parse innings pitched (e.g., "6.1" = 6 and 1/3)
                ip_str = stats.get("inningsPitched", "0.0")
                try:
                    ip_parts = str(ip_str).split(".")
                    ip = int(ip_parts[0]) + (int(ip_parts[1]) / 3 if len(ip_parts) > 1 else 0)
                except (ValueError, IndexError):
                    ip = 0.0

                ps = PitchingStats(
                    player_id=player.id,
                    game_id=game.id,
                    team_id=team.id if team else None,
                    innings_pitched=ip,
                    hits_allowed=int(stats.get("hits", 0)),
                    runs_allowed=int(stats.get("runs", 0)),
                    earned_runs=int(stats.get("earnedRuns", 0)),
                    walks_allowed=int(stats.get("baseOnBalls", 0)),
                    strikeouts=int(stats.get("strikeOuts", 0)),
                    home_runs_allowed=int(stats.get("homeRuns", 0)),
                    pitches_thrown=int(stats.get("pitchesThrown", 0)),
                    strikes=int(stats.get("strikes", 0)),
                    win="W" in stats.get("note", ""),
                    loss="L" in stats.get("note", ""),
                    save="S" in stats.get("note", "") and "BS" not in stats.get("note", ""),
                    hold="H" in stats.get("note", ""),
                    blown_save="BS" in stats.get("note", ""),
                    is_starter=(i == 0),
                )
                session.add(ps)

                # Track starting pitcher on game record
                if i == 0:
                    if side == "home":
                        game.home_starter_id = player.id
                    else:
                        game.away_starter_id = player.id

        try:
            session.commit()
            count += 1
        except Exception as e:
            session.rollback()
            logger.warning(f"⚠️ Integrity or commit error for game {game.mlb_game_pk}: {e}")
            errors += 1
            
        if count > 0 and count % 50 == 0:
            logger.info(f"  ... processed {count} games")
            time.sleep(0.2)

    logger.info(f"✅ Box scores: {count} games processed, {errors} errors")
    return count


# ──────────────────────────────────────────────
# 5. Fetch Standings
# ──────────────────────────────────────────────
def fetch_standings(session):
    """Fetch current standings."""
    logger.info("🏆 Fetching standings...")

    try:
        standings_data = statsapi.standings_data(leagueId="103,104", season=SEASON)
    except Exception as e:
        logger.error(f"❌ Failed to fetch standings: {e}")
        return 0

    count = 0
    for div_id, div_data in standings_data.items():
        teams_in_div = div_data.get("teams", [])

        for t in teams_in_div:
            team_name = t.get("name", "")
            team = session.query(Team).filter_by(name=team_name).first()
            if not team:
                logger.warning(f"⚠️ Team not found: {team_name}")
                continue

            existing = session.query(TeamStandings).filter_by(
                team_id=team.id, season=SEASON
            ).first()

            wins = int(t.get("w", 0))
            losses = int(t.get("l", 0))
            rs = int(t.get("rs", 0)) if t.get("rs") else 0
            ra = int(t.get("ra", 0)) if t.get("ra") else 0

            if existing:
                existing.wins = wins
                existing.losses = losses
                existing.win_pct = round(wins / (wins + losses), 3) if (wins + losses) > 0 else 0.0
                existing.games_back = float(t.get("gb", 0)) if t.get("gb", "-") != "-" else 0.0
                existing.runs_scored = rs
                existing.runs_allowed = ra
                existing.run_diff = rs - ra
                existing.division_rank = int(t.get("div_rank", 0))
            else:
                standing = TeamStandings(
                    team_id=team.id,
                    season=SEASON,
                    wins=wins,
                    losses=losses,
                    win_pct=round(wins / (wins + losses), 3) if (wins + losses) > 0 else 0.0,
                    games_back=float(t.get("gb", 0)) if t.get("gb", "-") != "-" else 0.0,
                    runs_scored=rs,
                    runs_allowed=ra,
                    run_diff=rs - ra,
                    division_rank=int(t.get("div_rank", 0)),
                    streak=t.get("strk", ""),
                )
                session.add(standing)
                count += 1

    session.commit()
    logger.info(f"✅ Standings: {count} new entries")
    return count


# ──────────────────────────────────────────────
# Main Pipeline
# ──────────────────────────────────────────────
def run_full_pipeline(boxscore_limit=None):
    """Run the complete data pipeline."""
    start_time = time.time()
    logger.info("=" * 60)
    logger.info(f"🚀 Starting MLB Data Pipeline — Season {SEASON}")
    logger.info("=" * 60)

    # Initialize database
    os.makedirs("data", exist_ok=True)
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()

    try:
        # Step 1: Teams
        fetch_teams(session)

        # Step 2: Players
        fetch_players(session)

        # Step 3: Games
        fetch_games(session)

        # Step 4: Box Scores
        fetch_boxscores(session, limit=boxscore_limit)

        # Step 5: Standings
        fetch_standings(session)

        elapsed = time.time() - start_time
        logger.info("=" * 60)
        logger.info(f"✅ Pipeline completed in {elapsed:.1f} seconds")
        logger.info("=" * 60)

        # Print summary
        logger.info(f"  Teams:    {session.query(Team).count()}")
        logger.info(f"  Players:  {session.query(Player).count()}")
        logger.info(f"  Games:    {session.query(Game).count()}")
        logger.info(f"  Batting:  {session.query(BattingStats).count()}")
        logger.info(f"  Pitching: {session.query(PitchingStats).count()}")

    except Exception as e:
        logger.error(f"❌ Pipeline failed: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="MLB Data Pipeline")
    parser.add_argument("--boxscore-limit", type=int, default=None,
                        help="Limit number of boxscores to fetch (for testing)")
    parser.add_argument("--step", choices=["teams", "players", "games", "boxscores", "standings", "all"],
                        default="all", help="Run a specific pipeline step")
    args = parser.parse_args()

    if args.step == "all":
        run_full_pipeline(boxscore_limit=args.boxscore_limit)
    else:
        os.makedirs("data", exist_ok=True)
        Base.metadata.create_all(bind=engine)
        session = SessionLocal()
        try:
            if args.step == "teams":
                fetch_teams(session)
            elif args.step == "players":
                fetch_players(session)
            elif args.step == "games":
                fetch_games(session)
            elif args.step == "boxscores":
                fetch_boxscores(session, limit=args.boxscore_limit)
            elif args.step == "standings":
                fetch_standings(session)
        finally:
            session.close()

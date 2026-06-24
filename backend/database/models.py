"""
MLB Baseball Analytics Platform — Database Models
SQLAlchemy ORM models for SQLite database.
"""

from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Boolean,
    Date, DateTime, ForeignKey, UniqueConstraint, Text
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.sql import func
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/mlb.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite specific
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency for FastAPI - yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ──────────────────────────────────────────────
# Teams
# ──────────────────────────────────────────────
class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, autoincrement=True)
    mlb_id = Column(Integer, unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    abbreviation = Column(String(10), nullable=False)
    league = Column(String(2))        # AL / NL
    division = Column(String(10))     # East / Central / West
    venue_name = Column(String(200))
    logo_url = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    players = relationship("Player", back_populates="team")
    home_games = relationship("Game", foreign_keys="Game.home_team_id", back_populates="home_team")
    away_games = relationship("Game", foreign_keys="Game.away_team_id", back_populates="away_team")

    def __repr__(self):
        return f"<Team(name='{self.name}', abbreviation='{self.abbreviation}')>"


# ──────────────────────────────────────────────
# Players
# ──────────────────────────────────────────────
class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, autoincrement=True)
    mlb_id = Column(Integer, unique=True, nullable=False, index=True)
    full_name = Column(String(200), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    primary_position = Column(String(10))
    bats = Column(String(1))          # R / L / S
    throws = Column(String(1))        # R / L
    birth_date = Column(Date)
    birth_country = Column(String(100))
    height = Column(String(10))       # e.g. "6' 2\""
    weight = Column(Integer)          # lbs
    team_id = Column(Integer, ForeignKey("teams.id"), index=True)
    jersey_number = Column(String(5))
    headshot_url = Column(Text)
    active = Column(Boolean, default=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    team = relationship("Team", back_populates="players")
    batting_stats = relationship("BattingStats", back_populates="player")
    pitching_stats = relationship("PitchingStats", back_populates="player")
    savant_stats = relationship("SavantStats", back_populates="player", uselist=False)

    def __repr__(self):
        return f"<Player(name='{self.full_name}', position='{self.primary_position}')>"


# ──────────────────────────────────────────────
# Games
# ──────────────────────────────────────────────
class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, autoincrement=True)
    mlb_game_pk = Column(Integer, unique=True, nullable=False, index=True)
    game_date = Column(Date, nullable=False, index=True)
    status = Column(String(20))       # Final / Live / Scheduled
    home_team_id = Column(Integer, ForeignKey("teams.id"), index=True)
    away_team_id = Column(Integer, ForeignKey("teams.id"), index=True)
    home_score = Column(Integer)
    away_score = Column(Integer)
    home_hits = Column(Integer)
    away_hits = Column(Integer)
    home_errors = Column(Integer)
    away_errors = Column(Integer)
    innings = Column(Integer, default=9)
    venue = Column(String(200))
    season = Column(Integer, nullable=False, index=True)
    game_type = Column(String(5))     # R=Regular, P=Postseason
    winning_team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    losing_team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    # Starting pitchers
    home_starter_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    away_starter_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    home_team = relationship("Team", foreign_keys=[home_team_id], back_populates="home_games")
    away_team = relationship("Team", foreign_keys=[away_team_id], back_populates="away_games")
    home_starter = relationship("Player", foreign_keys=[home_starter_id])
    away_starter = relationship("Player", foreign_keys=[away_starter_id])
    batting_stats = relationship("BattingStats", back_populates="game")
    pitching_stats = relationship("PitchingStats", back_populates="game")

    def __repr__(self):
        return f"<Game(date='{self.game_date}', pk={self.mlb_game_pk})>"


# ──────────────────────────────────────────────
# Batting Stats (per player per game)
# ──────────────────────────────────────────────
class BattingStats(Base):
    __tablename__ = "batting_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    at_bats = Column(Integer, default=0)
    runs = Column(Integer, default=0)
    hits = Column(Integer, default=0)
    doubles = Column(Integer, default=0)
    triples = Column(Integer, default=0)
    home_runs = Column(Integer, default=0)
    rbi = Column(Integer, default=0)
    walks = Column(Integer, default=0)
    strikeouts = Column(Integer, default=0)
    stolen_bases = Column(Integer, default=0)
    caught_stealing = Column(Integer, default=0)
    hit_by_pitch = Column(Integer, default=0)
    sacrifice_flies = Column(Integer, default=0)
    plate_appearances = Column(Integer, default=0)

    __table_args__ = (
        UniqueConstraint("player_id", "game_id", name="uq_batting_player_game"),
    )

    # Relationships
    player = relationship("Player", back_populates="batting_stats")
    game = relationship("Game", back_populates="batting_stats")

    @property
    def avg(self):
        """Batting average."""
        return round(self.hits / self.at_bats, 3) if self.at_bats > 0 else 0.0

    @property
    def obp(self):
        """On-base percentage."""
        denom = self.at_bats + self.walks + self.hit_by_pitch + self.sacrifice_flies
        if denom == 0:
            return 0.0
        return round((self.hits + self.walks + self.hit_by_pitch) / denom, 3)

    @property
    def slg(self):
        """Slugging percentage."""
        if self.at_bats == 0:
            return 0.0
        singles = self.hits - self.doubles - self.triples - self.home_runs
        total_bases = singles + (2 * self.doubles) + (3 * self.triples) + (4 * self.home_runs)
        return round(total_bases / self.at_bats, 3)

    @property
    def ops(self):
        """On-base plus slugging."""
        return round(self.obp + self.slg, 3)


# ──────────────────────────────────────────────
# Pitching Stats (per player per game)
# ──────────────────────────────────────────────
class PitchingStats(Base):
    __tablename__ = "pitching_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    innings_pitched = Column(Float, default=0.0)
    hits_allowed = Column(Integer, default=0)
    runs_allowed = Column(Integer, default=0)
    earned_runs = Column(Integer, default=0)
    walks_allowed = Column(Integer, default=0)
    strikeouts = Column(Integer, default=0)
    home_runs_allowed = Column(Integer, default=0)
    pitches_thrown = Column(Integer, default=0)
    strikes = Column(Integer, default=0)
    win = Column(Boolean, default=False)
    loss = Column(Boolean, default=False)
    save = Column(Boolean, default=False)
    hold = Column(Boolean, default=False)
    blown_save = Column(Boolean, default=False)
    is_starter = Column(Boolean, default=False)

    __table_args__ = (
        UniqueConstraint("player_id", "game_id", name="uq_pitching_player_game"),
    )

    # Relationships
    player = relationship("Player", back_populates="pitching_stats")
    game = relationship("Game", back_populates="pitching_stats")

    @property
    def era(self):
        """Earned run average (per 9 innings)."""
        if self.innings_pitched == 0:
            return 0.0
        return round((self.earned_runs / self.innings_pitched) * 9, 2)

    @property
    def whip(self):
        """Walks + Hits per Inning Pitched."""
        if self.innings_pitched == 0:
            return 0.0
        return round((self.walks_allowed + self.hits_allowed) / self.innings_pitched, 2)


# ──────────────────────────────────────────────
# Team Standings (materialized/cached per season)
# ──────────────────────────────────────────────
class TeamStandings(Base):
    __tablename__ = "team_standings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False, index=True)
    season = Column(Integer, nullable=False)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    win_pct = Column(Float, default=0.0)
    games_back = Column(Float, default=0.0)
    runs_scored = Column(Integer, default=0)
    runs_allowed = Column(Integer, default=0)
    run_diff = Column(Integer, default=0)
    home_wins = Column(Integer, default=0)
    home_losses = Column(Integer, default=0)
    away_wins = Column(Integer, default=0)
    away_losses = Column(Integer, default=0)
    last_10_wins = Column(Integer, default=0)
    last_10_losses = Column(Integer, default=0)
    streak = Column(String(10))       # e.g. W3, L2
    division_rank = Column(Integer)
    league_rank = Column(Integer)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("team_id", "season", name="uq_standings_team_season"),
    )

    team = relationship("Team")


# ──────────────────────────────────────────────
# Savant Stats (Statcast advanced metrics)
# ──────────────────────────────────────────────
class SavantStats(Base):
    __tablename__ = "savant_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False, unique=True, index=True)
    is_pitcher = Column(Boolean, default=False)
    avg_exit_velocity = Column(Float)
    max_exit_velocity = Column(Float)
    avg_launch_angle = Column(Float)
    barrel_rate = Column(Float)
    xba = Column(Float)
    xslg = Column(Float)
    xwoba = Column(Float)

    player = relationship("Player", back_populates="savant_stats")


# ──────────────────────────────────────────────
# Initialize Database
# ──────────────────────────────────────────────
def init_db():
    """Create all tables if they don't exist."""
    os.makedirs("data", exist_ok=True)
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")


if __name__ == "__main__":
    init_db()

import os
import sys
import logging
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure backend modules can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import Base, Player, SavantStats
from pybaseball import (
    statcast_batter_exitvelo_barrels,
    statcast_batter_expected_stats,
    statcast_pitcher_exitvelo_barrels,
    statcast_pitcher_expected_stats
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "mlb.db"))
DATABASE_URL = f"sqlite:///{DB_PATH}"

def fetch_savant_data(season=2024, min_events=50):
    logger.info(f"⚾ Fetching Baseball Savant Stats for {season}...")
    
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        # Clear existing savant_stats
        session.query(SavantStats).delete()
        session.commit()
        logger.info("🗑️ Cleared existing savant stats")
        
        # 1. Fetch Batter Data
        logger.info("📊 Fetching Batter EV & Barrels...")
        b_ev = statcast_batter_exitvelo_barrels(season, min_events)
        logger.info("📊 Fetching Batter Expected Stats...")
        b_x = statcast_batter_expected_stats(season, min_events)
        
        # Merge Batter Data
        b_merged = pd.merge(b_ev, b_x, on='player_id', how='outer', suffixes=('', '_y'))
        
        # 2. Fetch Pitcher Data
        logger.info("📊 Fetching Pitcher EV & Barrels...")
        p_ev = statcast_pitcher_exitvelo_barrels(season, min_events)
        logger.info("📊 Fetching Pitcher Expected Stats...")
        p_x = statcast_pitcher_expected_stats(season, min_events)
        
        # Merge Pitcher Data
        p_merged = pd.merge(p_ev, p_x, on='player_id', how='outer', suffixes=('', '_y'))
        
        count = 0
        
        # Process Batters
        for _, row in b_merged.iterrows():
            player_id = int(row['player_id'])
            
            # Find player in DB
            player = session.query(Player).filter_by(mlb_id=player_id).first()
            if not player:
                continue
                
            # Check if already inserted
            if session.query(SavantStats).filter_by(player_id=player.id).first():
                continue
                
            savant = SavantStats(
                player_id=player.id,
                is_pitcher=False,
                avg_exit_velocity=float(row.get('avg_hit_speed', 0)) if pd.notnull(row.get('avg_hit_speed')) else None,
                max_exit_velocity=float(row.get('max_hit_speed', 0)) if pd.notnull(row.get('max_hit_speed')) else None,
                avg_launch_angle=float(row.get('avg_hit_angle', 0)) if pd.notnull(row.get('avg_hit_angle')) else None,
                barrel_rate=float(row.get('brl_percent', 0)) if pd.notnull(row.get('brl_percent')) else None,
                xba=float(row.get('est_ba', 0)) if pd.notnull(row.get('est_ba')) else None,
                xslg=float(row.get('est_slg', 0)) if pd.notnull(row.get('est_slg')) else None,
                xwoba=float(row.get('est_woba', 0)) if pd.notnull(row.get('est_woba')) else None,
            )
            session.add(savant)
            session.commit()
            count += 1
            
        # Process Pitchers
        for _, row in p_merged.iterrows():
            player_id = int(row['player_id'])
            
            # Find player in DB
            player = session.query(Player).filter_by(mlb_id=player_id).first()
            if not player:
                continue
                
            # Check if already inserted (for two-way players)
            if session.query(SavantStats).filter_by(player_id=player.id).first():
                continue
                
            savant = SavantStats(
                player_id=player.id,
                is_pitcher=True,
                avg_exit_velocity=float(row.get('avg_hit_speed', 0)) if pd.notnull(row.get('avg_hit_speed')) else None,
                max_exit_velocity=float(row.get('max_hit_speed', 0)) if pd.notnull(row.get('max_hit_speed')) else None,
                avg_launch_angle=float(row.get('avg_hit_angle', 0)) if pd.notnull(row.get('avg_hit_angle')) else None,
                barrel_rate=float(row.get('brl_percent', 0)) if pd.notnull(row.get('brl_percent')) else None,
                xba=float(row.get('est_ba', 0)) if pd.notnull(row.get('est_ba')) else None,
                xslg=float(row.get('est_slg', 0)) if pd.notnull(row.get('est_slg')) else None,
                xwoba=float(row.get('est_woba', 0)) if pd.notnull(row.get('est_woba')) else None,
            )
            session.add(savant)
            session.commit() # commit each to avoid large transaction failure
            count += 1
            
        logger.info(f"✅ Successfully integrated {count} Savant Stats records!")
        
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Error fetching Savant data: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    fetch_savant_data()

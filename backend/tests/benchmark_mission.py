import sys
import os
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the parent directory to sys.path to allow imports from app
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from app.database import Base
from app.modules.missions import service as mission_service
from app.modules.missions import schemas as mission_schemas
from app.modules.campaigns import models as campaign_models

# Setup in-memory DB
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def setup_db():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()

    # Create a campaign
    camp = campaign_models.Campaign(
        name="Benchmark Campaign",
        discord_guild_id="bench_guild",
        dm_role_id="dm",
        player_role_id="player"
    )
    session.add(camp)
    session.commit()
    session.refresh(camp)
    return session, camp.id

def benchmark():
    session, campaign_id = setup_db()

    # Prepare data
    num_missions = 100
    rewards_per_mission = 5

    print(f"Benchmarking creation of {num_missions} missions with {rewards_per_mission} rewards each...")

    start_time = time.time()

    for i in range(num_missions):
        rewards = []
        for j in range(rewards_per_mission):
            rewards.append(mission_schemas.MissionRewardCreate(
                xp=100,
                scrip=50
            ))

        mission_in = mission_schemas.MissionCreate(
            name=f"Mission {i}",
            description="Benchmark Mission",
            status="Available",
            rewards=rewards
        )

        mission_service.create_mission(session, mission_in, campaign_id)

    end_time = time.time()
    total_time = end_time - start_time

    print(f"Total time: {total_time:.4f} seconds")
    print(f"Avg time per mission: {total_time/num_missions:.4f} seconds")

if __name__ == "__main__":
    benchmark()

import time
import sys
import os

# Mocking modules that might be missing or hard to load in this environment
# if they are not needed for the core benchmark logic.
# But we need sqlalchemy and the app modules.

try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
except ImportError:
    print("SQLAlchemy not found. Cannot run benchmark.")
    sys.exit(0)

# Add backend to path
sys.path.append(os.getcwd())

try:
    from app.database import Base
    from app.modules.auth import models as auth_models
    from app.modules.characters import models as char_models
    from app.modules.items import models as item_models
    from app.modules.missions import models as mission_models
    from app.modules.campaigns import models as campaign_models

    from app.modules.auth import schemas as auth_schemas
    from app.modules.items import schemas as item_schemas
    from app.modules.missions import schemas as mission_schemas
    from app.modules.characters import schemas as char_schemas

    from app.modules.auth import service as auth_service
    from app.modules.items import service as item_service
    from app.modules.missions import service as mission_service
    from app.modules.characters import service as char_service
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(0)

# Use SQLite for benchmarking
SQLALCHEMY_DATABASE_URL = "sqlite:///./benchmark.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

def benchmark_distribute_rewards(num_players=10, num_rewards=5):
    db = SessionLocal()

    # Setup campaign
    camp = campaign_models.Campaign(
        name="Benchmark Campaign",
        discord_guild_id="bench",
        dm_role_id="dm",
        player_role_id="player"
    )
    db.add(camp)
    db.commit()
    db.refresh(camp)

    # Setup characters
    characters = []
    for i in range(num_players):
        user_in = auth_schemas.UserCreate(
            username=f"user_{i}",
            discord_id=f"discord_{i}",
            campaign_id=camp.id,
            role="player"
        )
        db_user = auth_service.create_user(db, user_in)
        characters.append(db_user.characters[0])

    # Setup items
    items = []
    for i in range(num_rewards):
        item_in = item_schemas.ItemCreate(name=f"Item {i}", description=f"Desc {i}")
        db_item = item_service.create_item(db, item_in, campaign_id=camp.id)
        items.append(db_item)

    # Setup mission
    mission_in = mission_schemas.MissionCreate(
        name="Benchmark Mission",
        description="Bench",
        status="Completed",
        rewards=[]
    )
    db_mission = mission_service.create_mission(db, mission_in, campaign_id=camp.id)

    # Add rewards to mission
    for item in items:
        reward = mission_models.MissionReward(mission_id=db_mission.id, gold=10, item_id=item.id)
        db.add(reward)

    # Add players to mission
    for char in characters:
        mission_service.add_character_to_mission(db, db_mission, char)

    db.commit()
    db.refresh(db_mission)

    print(f"Starting benchmark with {num_players} players and {num_rewards} rewards...")
    start_time = time.time()
    mission_service.distribute_mission_rewards(db, db_mission)
    end_time = time.time()

    duration = end_time - start_time
    print(f"Time taken: {duration:.4f} seconds")

    db.close()
    return duration

if __name__ == "__main__":
    setup_db()
    # Warm up
    benchmark_distribute_rewards(num_players=2, num_rewards=2)

    # Actual benchmark
    total_time = 0
    runs = 3
    for _ in range(runs):
        setup_db()
        total_time += benchmark_distribute_rewards(num_players=50, num_rewards=10)

    print(f"\nAverage time over {runs} runs: {total_time/runs:.4f} seconds")

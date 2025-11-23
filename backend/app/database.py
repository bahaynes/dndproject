import os
import logging
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

logger = logging.getLogger(__name__)

engine = create_engine(
    DATABASE_URL,
    # required for sqlite
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def ensure_character_status_column():
    """Backfill the characters.status column if the DB was created before the field existed."""
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    if "characters" not in table_names:
        return

    column_names = [col["name"] for col in inspector.get_columns("characters")]
    if "status" in column_names:
        return

    # Import locally to avoid circular import at module load time
    from app.modules.common.enums import CharacterStatus

    status_default = CharacterStatus.READY.value
    with engine.begin() as conn:
        logger.info("Ensuring characters.status column exists (dialect=%s)", engine.dialect.name)
        if engine.dialect.name == "postgresql":
            # Ensure the enum exists before adding the column
            conn.execute(
                text(
                    """
                    DO $$
                    BEGIN
                        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'characterstatus') THEN
                            CREATE TYPE characterstatus AS ENUM ('ready', 'deployed', 'fatigued', 'medical_leave');
                        END IF;
                    END$$;
                    """
                )
            )
            conn.execute(
                text("ALTER TABLE characters ADD COLUMN status characterstatus NOT NULL DEFAULT :default"),
                {"default": status_default},
            )
        else:
            # SQLite does not allow parameter binding in ALTER TABLE DEFAULT clauses
            conn.execute(
                text(f"ALTER TABLE characters ADD COLUMN status VARCHAR NOT NULL DEFAULT '{status_default}'")
            )


def ensure_legacy_columns():
    """Backfill columns that were added in later revisions but may be missing in older dev databases.

    This helps avoid ResponseValidationError / OperationalError when loading related objects such as
    character stats, inventory, missions, and sessions.
    """
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    # Log current schema state for debugging
    logger.info("Database dialect: %s", engine.dialect.name)
    logger.info("Existing tables: %s", sorted(existing_tables))

    def get_columns(table_name: str):
        if table_name not in existing_tables:
            logger.warning("Expected table '%s' is missing in the database.", table_name)
            return set()
        cols = {col["name"] for col in inspector.get_columns(table_name)}
        logger.info("Columns for '%s': %s", table_name, sorted(cols))
        return cols

    character_stats_cols = get_columns("character_stats")
    inventory_items_cols = get_columns("inventory_items")
    missions_cols = get_columns("missions")
    game_sessions_cols = get_columns("game_sessions")

    with engine.begin() as conn:
        # character_stats: commendations, current_hp, short_rest_available
        if "character_stats" in existing_tables:
            if "commendations" not in character_stats_cols:
                logger.warning("Adding missing column character_stats.commendations")
                conn.execute(
                    text("ALTER TABLE character_stats ADD COLUMN commendations INTEGER NOT NULL DEFAULT 0")
                )
            if "current_hp" not in character_stats_cols:
                logger.warning("Adding missing column character_stats.current_hp")
                conn.execute(
                    text("ALTER TABLE character_stats ADD COLUMN current_hp INTEGER NOT NULL DEFAULT 0")
                )
            if "short_rest_available" not in character_stats_cols:
                logger.warning("Adding missing column character_stats.short_rest_available")
                default_expr = "1" if engine.dialect.name == "postgresql" else "1"
                conn.execute(
                    text(
                        f"ALTER TABLE character_stats ADD COLUMN short_rest_available BOOLEAN NOT NULL DEFAULT {default_expr}"
                    )
                )

        # inventory_items: is_attuned
        if "inventory_items" in existing_tables and "is_attuned" not in inventory_items_cols:
            logger.warning("Adding missing column inventory_items.is_attuned")
            default_expr = "0" if engine.dialect.name == "postgresql" else "0"
            conn.execute(
                text(
                    f"ALTER TABLE inventory_items ADD COLUMN is_attuned BOOLEAN NOT NULL DEFAULT {default_expr}"
                )
            )

        # missions: title, summary, status, target_hex, dossier_data
        if "missions" in existing_tables:
            if "title" not in missions_cols:
                logger.warning("Adding missing column missions.title")
                conn.execute(
                    text("ALTER TABLE missions ADD COLUMN title VARCHAR NOT NULL DEFAULT ''")
                )
            if "summary" not in missions_cols:
                logger.warning("Adding missing column missions.summary")
                conn.execute(
                    text("ALTER TABLE missions ADD COLUMN summary VARCHAR")
                )
            if "status" not in missions_cols:
                logger.warning("Adding missing column missions.status")
                conn.execute(
                    text("ALTER TABLE missions ADD COLUMN status VARCHAR NOT NULL DEFAULT 'available'")
                )
            if "target_hex" not in missions_cols:
                logger.warning("Adding missing column missions.target_hex")
                conn.execute(
                    text("ALTER TABLE missions ADD COLUMN target_hex VARCHAR")
                )
            if "dossier_data" not in missions_cols:
                logger.warning("Adding missing column missions.dossier_data")
                # Use a generic JSON/text column; exact type depends on dialect
                if engine.dialect.name == "postgresql":
                    conn.execute(
                        text("ALTER TABLE missions ADD COLUMN dossier_data JSONB NOT NULL DEFAULT '{}'::jsonb")
                    )
                else:
                    conn.execute(
                        text("ALTER TABLE missions ADD COLUMN dossier_data JSON NOT NULL DEFAULT '{}'")  # type: ignore[assignment]
                    )

        # game_sessions: mission_id, title, session_date, status, route_data, gm_notes, aar_summary
        if "game_sessions" in existing_tables:
            if "mission_id" not in game_sessions_cols:
                logger.warning("Adding missing column game_sessions.mission_id")
                conn.execute(
                    text("ALTER TABLE game_sessions ADD COLUMN mission_id VARCHAR")
                )
            if "title" not in game_sessions_cols:
                logger.warning("Adding missing column game_sessions.title")
                conn.execute(
                    text("ALTER TABLE game_sessions ADD COLUMN title VARCHAR NOT NULL DEFAULT ''")
                )
            if "session_date" not in game_sessions_cols:
                logger.warning("Adding missing column game_sessions.session_date")
                if engine.dialect.name == "postgresql":
                    conn.execute(
                        text("ALTER TABLE game_sessions ADD COLUMN session_date TIMESTAMP")
                    )
                else:
                    conn.execute(
                        text("ALTER TABLE game_sessions ADD COLUMN session_date DATETIME")
                    )
            if "status" not in game_sessions_cols:
                logger.warning("Adding missing column game_sessions.status")
                conn.execute(
                    text("ALTER TABLE game_sessions ADD COLUMN status VARCHAR NOT NULL DEFAULT 'open'")
                )
            if "route_data" not in game_sessions_cols:
                logger.warning("Adding missing column game_sessions.route_data")
                if engine.dialect.name == "postgresql":
                    conn.execute(
                        text("ALTER TABLE game_sessions ADD COLUMN route_data JSONB NOT NULL DEFAULT '[]'::jsonb")
                    )
                else:
                    conn.execute(
                        text("ALTER TABLE game_sessions ADD COLUMN route_data JSON NOT NULL DEFAULT '[]'")  # type: ignore[assignment]
                    )
            if "gm_notes" not in game_sessions_cols:
                logger.warning("Adding missing column game_sessions.gm_notes")
                conn.execute(
                    text("ALTER TABLE game_sessions ADD COLUMN gm_notes TEXT")
                )
            if "aar_summary" not in game_sessions_cols:
                logger.warning("Adding missing column game_sessions.aar_summary")
                conn.execute(
                    text("ALTER TABLE game_sessions ADD COLUMN aar_summary TEXT")
                )


def ensure_default_admin():
    """Ensure there is at least one admin user, optionally driven by DEV_ADMIN_* env vars.

    This is intended for development and initial bootstrap. It will:
    - Skip entirely if DEV_ADMIN_PASSWORD is not set.
    - Skip if an admin user already exists.
    - Otherwise create a new admin user with a default character and stats.
    """
    # Only run when explicitly configured; avoid surprising credentials in shared environments.
    password = os.getenv("DEV_ADMIN_PASSWORD")
    if not password:
        msg = "DEV_ADMIN_PASSWORD not set; skipping default admin seeding."
        logger.info(msg)
        print(msg)
        return

    username = os.getenv("DEV_ADMIN_USERNAME", "admin")
    email = os.getenv("DEV_ADMIN_EMAIL", "admin@example.com")

    from app.modules.auth import models as auth_models, schemas as auth_schemas, service as auth_service
    from app.modules.characters import models as char_models

    db = SessionLocal()
    try:
        existing_admin = (
            db.query(auth_models.User)
            .filter(auth_models.User.role == "admin")
            .first()
        )
        if existing_admin:
            msg = (
                f"Admin user already exists (id={existing_admin.id}, "
                f"username={existing_admin.username}); skipping default admin seeding."
            )
            logger.info(msg)
            print(msg)
            return

        msg = f"No admin user found; creating default admin username={username} email={email}"
        logger.warning(msg)
        print(msg)
        payload = auth_schemas.UserCreate(
            username=username,
            email=email,
            password=password,
            role="admin",
        )
        user = auth_service.create_user(db, payload)

        # Ensure character/stats exist (create_user already does this, but keep the intent explicit)
        character = (
            db.query(char_models.Character)
            .filter(char_models.Character.owner_id == user.id)
            .first()
        )
        if not character:
            character = char_models.Character(
                name=f"{user.username}'s Character",
                owner_id=user.id,
            )
            db.add(character)
            db.commit()
            db.refresh(character)

        if not character.stats:
            stats = char_models.CharacterStats(character_id=character.id)
            db.add(stats)
            db.commit()
            db.refresh(stats)

        msg = f"Default admin created successfully (id={user.id}, username={user.username})."
        logger.info(msg)
        print(msg)
    finally:
        db.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

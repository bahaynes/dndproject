import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv

load_dotenv()

# These are initialized to None. They will be set by the init_db function.
engine = None
SessionLocal = None
Base = declarative_base()

def init_db():
    """
    Initializes the database engine and session. This should be called once
    at application startup.
    """
    global engine, SessionLocal

    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sql_app.db")

    print(f"INFO: Initializing database connection to {DATABASE_URL}")

    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create tables if they don't exist.
    # In a real production app, you'd likely use Alembic migrations for this.
    Base.metadata.create_all(bind=engine)


def get_db():
    """
    Dependency to get a DB session. Ensures the session is always closed.
    """
    if SessionLocal is None:
        raise RuntimeError("Database is not initialized. Call init_db() on startup.")

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

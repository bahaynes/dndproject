import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
import sys

# Add the project's root `backend` directory to the Python path
# This ensures that `app.xxx` imports work correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import Base, get_db
from app.main import app
from app.models import *  # noqa

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """
    Fixture to create a new database session for each test function.
    Creates all tables, yields a session, then drops all tables.
    """
    # Create all tables in the in-memory database
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop all tables after the test is done
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """
    Fixture to create a TestClient that uses the test database session.
    """
    def override_get_db():
        """
        This inner function is the dependency override.
        It yields the session provided by the `db_session` fixture.
        """
        try:
            yield db_session
        finally:
            # The session's lifecycle is managed by the `db_session` fixture.
            pass

    # Apply the dependency override for the duration of this client's life.
    app.dependency_overrides[get_db] = override_get_db

    # Yield the TestClient to the test function.
    yield TestClient(app)

    # Clean up the override after the test is done to ensure no leakage.
    app.dependency_overrides.clear()

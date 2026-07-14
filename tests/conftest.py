"""Common test fixtures and setup for LedgerBud."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.fastapi_app.db.base import Base
from app.fastapi_app.models.user import User


@pytest.fixture(name="db_session")
def fixture_db_session():
    """Create a clean in-memory SQLite database and session for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    session = TestingSessionLocal()
    
    # Create a test user
    test_user = User(
        full_name="Test User",
        email="test@example.com",
        password_hash="fakehash",
        is_active=True
    )
    session.add(test_user)
    session.commit()
    
    yield session
    
    session.close()
    Base.metadata.drop_all(bind=engine)

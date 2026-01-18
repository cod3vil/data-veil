import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import Task, SensitiveItem, DesensitizationRule, OperationLog
import os

# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def test_engine():
    """Create a test database engine"""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_db(test_engine):
    """Create a test database session"""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Setup for API tests - ensure test_api.db exists and has tables
@pytest.fixture(scope="session", autouse=True)
def setup_api_test_database():
    """Ensure API test database is properly initialized"""
    api_db_path = "test_api.db"
    
    # Create new database with tables
    from sqlalchemy import create_engine
    engine = create_engine(f"sqlite:///./{api_db_path}", connect_args={"check_same_thread": False})
    
    # Drop and recreate all tables to ensure clean state
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    engine.dispose()
    
    yield
    
    # Cleanup - remove database after all tests complete
    if os.path.exists(api_db_path):
        try:
            os.remove(api_db_path)
        except:
            pass

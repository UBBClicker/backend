import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
import tempfile

from app.database import Base, get_db
from app.models.user import User
from main import fastapi_app

@pytest.fixture(scope="function")
def db_engine():
    """Create a test database engine with an in-memory SQLite database."""
    # Use a unique temporary file for each test
    db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    db_file.close()
    
    # Create connection string from the temporary file
    TEST_SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_file.name}"
    
    engine = create_engine(
        TEST_SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Close the connection before cleanup
    engine.dispose()
    
    # Clean up the temporary file
    try:
        os.unlink(db_file.name)
    except:
        pass  # If file is still locked, let the OS handle it later


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create a test database session."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with a test database."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
            
    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as client:
        yield client
        
    # Reset dependency overrides
    fastapi_app.dependency_overrides = {}
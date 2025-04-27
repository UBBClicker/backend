import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.crud.user import user as user_crud
from app.schemas.user import UserCreate


def test_register_user(client: TestClient, db_session: Session):
    """Test user registration."""
    response = client.post(
        "/user/register",
        json={"nickname": "testuser", "password": "testpass"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["nickname"] == "testuser"
    assert "id" in data
    # Password should not be in the response for security reasons
    assert "password" not in data

    # Try registering the same user again
    response = client.post(
        "/user/register",
        json={"nickname": "testuser", "password": "testpass"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "User already exists"


def test_login_user(client: TestClient, db_session: Session):
    """Test user login."""
    # Create a test user
    user_create = UserCreate(nickname="loginuser", password="password123")
    user_crud.register(db_session, user_create)
    
    # Login with correct credentials
    response = client.post(
        "/user/login",
        data={"username": "loginuser", "password": "password123"}  # Note: OAuth2 uses form data
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    
    # Login with incorrect password
    response = client.post(
        "/user/login",
        data={"username": "loginuser", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    
    # Login with non-existent user
    response = client.post(
        "/user/login",
        data={"username": "nonexistentuser", "password": "password123"}
    )
    assert response.status_code == 401


def test_get_user_me(client: TestClient, db_session: Session):
    """Test getting current user details."""
    # Create a test user
    user_create = UserCreate(nickname="currentuser", password="password123")
    user = user_crud.register(db_session, user_create)
    
    # Login to get token
    response = client.post(
        "/user/login",
        data={"username": "currentuser", "password": "password123"}
    )
    token = response.json()["access_token"]
    
    # Get current user with valid token
    response = client.get(
        "/user/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["nickname"] == "currentuser"
    assert data["id"] == user.id
    # Password should not be in the response
    assert "password" not in data
    
    # Try with invalid token
    response = client.get(
        "/user/me",
        headers={"Authorization": "Bearer invalidtoken"}
    )
    assert response.status_code == 401
    
    # Try without token
    response = client.get("/user/me")
    assert response.status_code == 401


def test_refresh_token(client: TestClient, db_session: Session):
    """Test token refresh endpoint."""
    # Create a test user
    user_create = UserCreate(nickname="refreshuser", password="password123")
    user = user_crud.register(db_session, user_create)
    
    # Login to get initial token
    response = client.post(
        "/user/login",
        data={"username": "refreshuser", "password": "password123"}
    )
    assert response.status_code == 200
    initial_token = response.json()["access_token"]
    
    # Use the token to refresh and get a new token
    response = client.post(
        "/user/refresh-token",
        headers={"Authorization": f"Bearer {initial_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    refreshed_token = data["access_token"]
    
    # Verify that the refreshed token is different from the initial token
    assert initial_token != refreshed_token
    
    # Verify that the new token is valid by using it to access a protected endpoint
    response = client.get(
        "/user/me",
        headers={"Authorization": f"Bearer {refreshed_token}"}
    )
    assert response.status_code == 200
    assert response.json()["nickname"] == "refreshuser"
    
    # Try with invalid token
    response = client.post(
        "/user/refresh-token",
        headers={"Authorization": "Bearer invalidtoken"}
    )
    assert response.status_code == 401
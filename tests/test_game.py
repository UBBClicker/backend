import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import time

from app.models.user import User
from app.models.item import Item, UserItem
from app.schemas.user import UserCreate
from app.schemas.item import ItemCreate
from app.crud.user import user as user_crud
from app.crud.item import item as item_crud
from app.crud.game import game as game_crud


def test_get_game_state(client, db_session):
    """Test retrieving game state."""
    # Create test user
    user_create = UserCreate(nickname="gameuser", password="password123")
    user = user_crud.register(db_session, user_create)
    
    # Login to get token
    response = client.post(
        "/user/login",
        data={"username": "gameuser", "password": "password123"}
    )
    token = response.json()["access_token"]
    
    # Get game state
    response = client.get(
        "/game/state",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["points"] == 0
    assert data["lifetime_points"] == 0
    assert data["clicks"] == 0
    assert data["points_per_click"] == 1.0
    assert data["points_per_second"] == 0.0


def test_process_click(client, db_session):
    """Test processing a click."""
    # Create test user
    user_create = UserCreate(nickname="clickuser", password="password123")
    user = user_crud.register(db_session, user_create)
    
    # Login to get token
    response = client.post(
        "/user/login",
        data={"username": "clickuser", "password": "password123"}
    )
    token = response.json()["access_token"]
    
    # Process a click
    response = client.post(
        "/game/click",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["points_earned"] == 1.0
    assert data["new_total"] == 1
    assert data["lifetime_points"] == 1
    assert data["clicks"] == 1
    
    # Process another click
    response = client.post(
        "/game/click",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Verify cumulative effect
    data = response.json()
    assert data["new_total"] == 2
    assert data["lifetime_points"] == 2
    assert data["clicks"] == 2


def test_buy_item(client, db_session):
    """Test buying an item."""
    # Create test user with points
    user_create = UserCreate(nickname="buyuser", password="password123")
    user = user_crud.register(db_session, user_create)
    
    # Update user to have 100 points
    user.points = 100
    db_session.commit()
    
    # Create test item
    item_create = ItemCreate(
        name="Test Cursor", 
        description="Clicks automatically",
        base_cost=10,
        points_per_click=0,
        points_per_second=0.1
    )
    item = item_crud.create(db_session, item_create)
    
    # Login to get token
    response = client.post(
        "/user/login",
        data={"username": "buyuser", "password": "password123"}
    )
    token = response.json()["access_token"]
    
    # Buy the item
    response = client.post(
        f"/game/buy/{item.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["new_points"] == 90  # 100 - 10
    assert data["new_points_per_second"] == 0.1
    assert data["item_quantity"] == 1
    assert data["item_cost"] > 10  # Cost should increase for next purchase
    
    # Try to buy a non-existent item
    response = client.post(
        "/game/buy/999",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404


def test_get_leaderboard(client, db_session):
    """Test retrieving the leaderboard."""
    # Create multiple users with different lifetime points
    users_data = [
        {"nickname": "leader1", "password": "password", "lifetime_points": 1000},
        {"nickname": "leader2", "password": "password", "lifetime_points": 500},
        {"nickname": "leader3", "password": "password", "lifetime_points": 1500}
    ]
    
    for user_data in users_data:
        user_create = UserCreate(nickname=user_data["nickname"], password=user_data["password"])
        user = user_crud.register(db_session, user_create)
        user.lifetime_points = user_data["lifetime_points"]
        db_session.commit()
    
    # Get leaderboard
    response = client.get("/game/leaderboard")
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3  # All users should be in the leaderboard
    
    # Verify ordering (by lifetime_points desc)
    assert data[0]["nickname"] == "leader3"  # 1500 points
    assert data[0]["rank"] == 1
    assert data[1]["nickname"] == "leader1"  # 1000 points
    assert data[1]["rank"] == 2
    assert data[2]["nickname"] == "leader2"  # 500 points
    assert data[2]["rank"] == 3


def test_passive_points_generation(db_session):
    """Test passive points generation over time."""
    # Create test user
    user_create = UserCreate(nickname="passiveuser", password="password123")
    user = user_crud.register(db_session, user_create)
    
    # Create an item that generates points per second
    item_create = ItemCreate(
        name="Passive Generator", 
        description="Generates points over time",
        base_cost=10,
        points_per_click=0,
        points_per_second=1.0  # 1 point per second
    )
    item = item_crud.create(db_session, item_create)
    
    # Give the user the item and update points_per_second
    user_item = item_crud.add_user_item(db_session, user.id, item.id)
    user.points_per_second = 1.0
    
    # Set last_updated to current time
    current_time = int(time.time())
    user.last_updated = current_time
    db_session.commit()
    
    # Simulate time passing (5 seconds)
    # In a real test, we'd use something like freezegun to mock time
    user.last_updated = current_time - 5
    
    # Update passive points
    game_crud.update_passive_points(db_session, user)
    
    # Verify points were added
    assert user.points == 5  # 1 point/sec * 5 seconds
    assert user.lifetime_points == 5
    assert user.last_updated > current_time - 5  # Should be updated to current time


def test_calculate_item_cost(db_session):
    """Test item cost calculation based on quantity."""
    base_cost = 10
    multiplier = 1.15
    
    # Test various quantities
    assert item_crud.calculate_item_cost(base_cost, 0, multiplier) == 10
    assert item_crud.calculate_item_cost(base_cost, 1, multiplier) == 11  # 10 * 1.15 = 11.5, rounded to 11
    assert item_crud.calculate_item_cost(base_cost, 2, multiplier) == 13  # 10 * 1.15^2 = 13.225, rounded to 13
    assert item_crud.calculate_item_cost(base_cost, 10, multiplier) == 41  # 10 * 1.15^10 = 40.87, rounded to 41
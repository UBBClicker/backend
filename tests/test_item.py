import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import json

from app.models.user import User
from app.models.item import Item, UserItem
from app.schemas.user import UserCreate
from app.schemas.item import ItemCreate
from app.crud.user import user as user_crud
from app.crud.item import item as item_crud


def test_create_item(client, db_session):
    """Test creating a new item."""
    # Create a test user for authentication
    user_create = UserCreate(nickname="itemadmin", password="password123")
    user = user_crud.register(db_session, user_create)
    
    # Login to get token
    response = client.post(
        "/user/login",
        data={"username": "itemadmin", "password": "password123"}
    )
    token = response.json()["access_token"]
    
    # Create a new item
    item_data = {
        "name": "Super Clicker",
        "description": "Increases click power",
        "base_cost": 50,
        "points_per_click": 0.5,
        "points_per_second": 0,
        "cost_multiplier": 1.2
    }
    
    response = client.post(
        "/items/",
        json=item_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Verify response
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Super Clicker"
    assert data["base_cost"] == 50
    assert data["points_per_click"] == 0.5
    assert "id" in data
    
    # Try to create item with duplicate name
    response = client.post(
        "/items/",
        json=item_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400  # Bad request due to duplicate


def test_get_all_items(client, db_session):
    """Test retrieving all items."""
    # Create several test items
    items_data = [
        {"name": "Item1", "description": "First item", "base_cost": 10, "points_per_click": 0.1},
        {"name": "Item2", "description": "Second item", "base_cost": 20, "points_per_second": 0.2},
        {"name": "Item3", "description": "Third item", "base_cost": 30, "points_per_click": 0.3, "points_per_second": 0.3}
    ]
    
    for item_data in items_data:
        item_create = ItemCreate(**item_data)
        item_crud.create(db_session, item_create)
    
    # Get all items
    response = client.get("/items/")
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3  # At least the 3 items we created
    
    # Verify items are returned in ascending order by base_cost
    item_costs = [item["base_cost"] for item in data]
    assert sorted(item_costs) == item_costs


def test_get_item_by_id(client, db_session):
    """Test retrieving a single item by ID."""
    # Create a test item
    item_create = ItemCreate(
        name="Unique Item",
        description="Special test item",
        base_cost=100,
        points_per_click=1.0,
        points_per_second=0
    )
    item = item_crud.create(db_session, item_create)
    
    # Get the item by ID
    response = client.get(f"/items/{item.id}")
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Unique Item"
    assert data["description"] == "Special test item"
    assert data["base_cost"] == 100
    
    # Try to get non-existent item
    response = client.get("/items/999")
    assert response.status_code == 404


def test_update_item(client, db_session):
    """Test updating an item."""
    # Create a test user for authentication
    user_create = UserCreate(nickname="updateadmin", password="password123")
    user = user_crud.register(db_session, user_create)
    
    # Login to get token
    response = client.post(
        "/user/login",
        data={"username": "updateadmin", "password": "password123"}
    )
    token = response.json()["access_token"]
    
    # Create a test item
    item_create = ItemCreate(
        name="Item To Update",
        description="This will be updated",
        base_cost=50,
        points_per_click=0.5,
        points_per_second=0.5
    )
    item = item_crud.create(db_session, item_create)
    
    # Update the item
    update_data = {
        "description": "Updated description",
        "base_cost": 75,
        "points_per_click": 1.0
    }
    
    response = client.put(
        f"/items/{item.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "Updated description"
    assert data["base_cost"] == 75
    assert data["points_per_click"] == 1.0
    assert data["points_per_second"] == 0.5  # Should be unchanged
    
    # Try to update non-existent item
    response = client.put(
        "/items/999",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404


def test_delete_item(client, db_session):
    """Test deleting an item."""
    # Create a test user for authentication
    user_create = UserCreate(nickname="deleteadmin", password="password123")
    user = user_crud.register(db_session, user_create)
    
    # Login to get token
    response = client.post(
        "/user/login",
        data={"username": "deleteadmin", "password": "password123"}
    )
    token = response.json()["access_token"]
    
    # Create a test item
    item_create = ItemCreate(
        name="Item To Delete",
        description="This will be deleted",
        base_cost=30,
        points_per_click=0.3
    )
    item = item_crud.create(db_session, item_create)
    
    # Delete the item
    response = client.delete(
        f"/items/{item.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Verify response
    assert response.status_code == 204
    
    # Verify item is gone
    response = client.get(f"/items/{item.id}")
    assert response.status_code == 404


def test_get_user_items(client, db_session):
    """Test retrieving a user's items."""
    # Create a test user
    user_create = UserCreate(nickname="itemowner", password="password123")
    user = user_crud.register(db_session, user_create)
    
    # Create test items
    item1 = item_crud.create(db_session, ItemCreate(
        name="User Item 1",
        description="First user item",
        base_cost=10,
        points_per_click=0.1
    ))
    
    item2 = item_crud.create(db_session, ItemCreate(
        name="User Item 2",
        description="Second user item",
        base_cost=20,
        points_per_second=0.2
    ))
    
    # Add items to user's inventory
    item_crud.add_user_item(db_session, user.id, item1.id, quantity=2)
    item_crud.add_user_item(db_session, user.id, item2.id, quantity=1)
    
    # Login to get token
    response = client.post(
        "/user/login",
        data={"username": "itemowner", "password": "password123"}
    )
    token = response.json()["access_token"]
    
    # Get user's items
    response = client.get(
        f"/items/user/{user.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    
    # Check quantities
    for item_data in data:
        if item_data["item_id"] == item1.id:
            assert item_data["quantity"] == 2
        elif item_data["item_id"] == item2.id:
            assert item_data["quantity"] == 1
    
    # Try to get another user's items
    other_user = user_crud.register(db_session, UserCreate(nickname="otheruser", password="password123"))
    response = client.get(
        f"/items/user/{other_user.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403  # Forbidden
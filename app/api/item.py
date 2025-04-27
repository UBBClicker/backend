from fastapi import APIRouter, HTTPException, Depends, status, File, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
import json
import os

from app import schemas, crud
from app.database import get_db
from app.api.user import get_current_user_dependency
from app.models.user import User

item_router = APIRouter(prefix="/items", tags=["Items"])


@item_router.get(
    "/",
    response_model=List[schemas.Item],
    status_code=status.HTTP_200_OK,
    summary="Get all items",
    description="Get a list of all available items in the game"
)
def get_all_items(
    db: Session = Depends(get_db)
):
    """
    Get a list of all available items in the game.
    
    This endpoint retrieves all items that can be purchased in the game,
    including their base cost, bonuses, and other attributes.
    """
    return crud.item.get_all_items(db)


@item_router.get(
    "/{item_id}",
    response_model=schemas.Item,
    status_code=status.HTTP_200_OK,
    summary="Get item by ID",
    description="Get detailed information about a specific item"
)
def get_item(
    item_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific item.
    
    Path Parameters:
    - **item_id**: ID of the item to retrieve
    """
    item = crud.item.get(db, item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    return item


@item_router.get(
    "/user/{user_id}",
    response_model=List[schemas.UserItem],
    status_code=status.HTTP_200_OK,
    summary="Get user's items",
    description="Get all items owned by a specific user"
)
def get_user_items(
    user_id: int,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    Get all items owned by a specific user.
    
    Path Parameters:
    - **user_id**: ID of the user whose items to retrieve
    
    Note: You can only view your own items unless you're an admin.
    """
    # Check if user is requesting their own items or is admin
    if current_user.id != user_id:
        # In a real app, you'd check if the current user has admin privileges
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own items"
        )
        
    return crud.item.get_user_items(db, user_id)


@item_router.post(
    "/",
    response_model=schemas.Item,
    status_code=status.HTTP_201_CREATED,
    summary="Create new item",
    description="Create a new purchasable item in the game"
)
def create_item(
    item: schemas.ItemCreate,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    Create a new purchasable item in the game.
    
    This endpoint is typically restricted to admins. It creates a new item that
    players can purchase to increase their points per click or points per second.
    
    Request Body:
    - **name**: Item name
    - **description**: Item description
    - **base_cost**: Base cost in points
    - **points_per_click**: Additional points per click from this item
    - **points_per_second**: Additional points per second from this item
    - **cost_multiplier**: Cost multiplier for each purchase (default: 1.15)
    - **image_url**: Optional URL to the item's image
    """
    try:
        # In a real app, you'd check if the current user has admin privileges here
        return crud.item.create(db, item)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Item with this name already exists"
        )


@item_router.put(
    "/{item_id}",
    response_model=schemas.Item,
    status_code=status.HTTP_200_OK,
    summary="Update item",
    description="Update an existing item's attributes"
)
def update_item(
    item_id: int,
    item_update: schemas.ItemUpdate,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    Update an existing item's attributes.
    
    This endpoint is typically restricted to admins. It allows updating various
    attributes of an existing game item.
    
    Path Parameters:
    - **item_id**: ID of the item to update
    
    Request Body (all fields are optional):
    - **name**: Item name
    - **description**: Item description
    - **base_cost**: Base cost in points
    - **points_per_click**: Additional points per click from this item
    - **points_per_second**: Additional points per second from this item
    - **cost_multiplier**: Cost multiplier for each purchase
    - **image_url**: URL to the item's image
    """
    # In a real app, you'd check if the current user has admin privileges
    
    # Get existing item
    db_item = crud.item.get(db, item_id)
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
        
    # Update and return
    return crud.item.update(db, db_obj=db_item, obj_in=item_update)


@item_router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete item",
    description="Delete an existing item from the game"
)
def delete_item(
    item_id: int,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    Delete an existing item from the game.
    
    This endpoint is typically restricted to admins. It allows removing an item
    from the game entirely.
    
    Path Parameters:
    - **item_id**: ID of the item to delete
    
    Note: Deleting an item will not remove it from users who have already purchased it.
    """
    # In a real app, you'd check if the current user has admin privileges
    
    # Get existing item
    db_item = crud.item.get(db, item_id)
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
        
    # Delete the item
    crud.item.delete(db, id=item_id)
    return None


@item_router.post(
    "/import",
    status_code=status.HTTP_201_CREATED,
    summary="Import items from JSON",
    description="Import multiple items from a JSON file"
)
async def import_items_from_json(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    Import multiple items from a JSON file.
    
    This endpoint allows admins to easily add multiple items at once by uploading a JSON file.
    The file should contain an array of item objects with the required fields.
    
    Request Body:
    - **file**: JSON file containing an array of items
    
    Example JSON format:
    ```json
    [
      {
        "name": "Cursor",
        "description": "Automatically clicks once every 10 seconds",
        "base_cost": 15,
        "points_per_click": 0,
        "points_per_second": 0.1,
        "cost_multiplier": 1.15
      },
      {
        "name": "Grandma",
        "description": "A nice grandma to bake more cookies",
        "base_cost": 100,
        "points_per_click": 0,
        "points_per_second": 1,
        "cost_multiplier": 1.15
      }
    ]
    ```
    """
    # In a real app, you'd check if the current user has admin privileges
    
    # Read and parse JSON file
    content = await file.read()
    items_data = json.loads(content)
    
    # Validate each item and create
    created_items = []
    errors = []
    
    for i, item_data in enumerate(items_data):
        try:
            # Create schema for validation
            item_schema = schemas.ItemCreate(**item_data)
            # Create item in database
            item = crud.item.create(db, item_schema)
            created_items.append(item)
        except Exception as e:
            errors.append(f"Error at item {i}: {str(e)}")
    
    # Return results
    return {
        "created_count": len(created_items),
        "total_count": len(items_data),
        "errors": errors
    }
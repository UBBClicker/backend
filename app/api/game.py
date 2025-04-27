from fastapi import APIRouter, HTTPException, Depends, status, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
import json

from app import schemas, crud
from app.database import get_db
from app.api.user import get_current_user_dependency
from app.models.user import User
from app.api.websocket import manager, get_user_id_from_token, periodic_leaderboard_update

game_router = APIRouter(prefix="/game", tags=["Game"])


@game_router.get(
    "/state",
    response_model=schemas.GameState,
    status_code=status.HTTP_200_OK,
    summary="Get current game state",
    description="Retrieve the current game state for the authenticated user"
)
def get_game_state(
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    Get the current game state for the authenticated user, including:
    
    - Points
    - Lifetime points
    - Clicks count
    - Points per click
    - Points per second
    """
    return crud.game.get_user_game_state(db, current_user.id)


@game_router.get(
    "/state/with-items",
    response_model=schemas.GameStateWithItems,
    status_code=status.HTTP_200_OK,
    summary="Get game state with all items",
    description="Retrieve the game state with all available items and their current costs"
)
def get_game_state_with_items(
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    Get the current game state and all available items with their costs.
    
    This endpoint returns:
    - Current game state (points, clicks, etc.)
    - List of all available items with calculated current costs based on owned quantity
    """
    # Get user's game state
    user = crud.game.get_user_game_state(db, current_user.id)
    
    # Get all available items
    all_items = crud.item.get_all_items(db)
    
    # Get user's items
    user_items_db = crud.item.get_user_items(db, current_user.id)
    user_items = {ui.item_id: ui.quantity for ui in user_items_db}
    
    # Create calculated items list
    calculated_items = []
    for item in all_items:
        quantity = user_items.get(item.id, 0)
        current_cost = crud.item.calculate_item_cost(
            item.base_cost, quantity, item.cost_multiplier
        )
        calculated_items.append(schemas.CalculatedItem(
            id=item.id,
            name=item.name,
            description=item.description,
            base_cost=item.base_cost,
            current_cost=current_cost,
            points_per_click=item.points_per_click,
            points_per_second=item.points_per_second,
            cost_multiplier=item.cost_multiplier,
            quantity=quantity,
            image_url=item.image_url
        ))
    
    # Create response
    response = jsonable_encoder(user)
    response["items"] = calculated_items
    
    return response


@game_router.post(
    "/click",
    response_model=schemas.ClickResult,
    status_code=status.HTTP_200_OK,
    summary="Process a click",
    description="Process a user's click and return the points earned"
)
def process_click(
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    Process a user's click and return the points earned.
    
    This endpoint:
    - Adds points based on the user's current points per click value
    - Updates the user's lifetime points
    - Increments the click counter
    - Returns the new total points and the points earned from this click
    """
    points_earned, user = crud.game.process_click(db, current_user.id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return schemas.ClickResult(
        points_earned=points_earned,
        new_total=user.points,
        lifetime_points=user.lifetime_points,
        clicks=user.clicks
    )


@game_router.post(
    "/buy/{item_id}",
    response_model=schemas.PurchaseResult,
    status_code=status.HTTP_200_OK,
    summary="Buy an item",
    description="Purchase an item for the authenticated user"
)
def buy_item(
    item_id: int,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    Purchase an item for the current user.
    
    This endpoint:
    - Checks if the user has enough points
    - Deducts the cost from the user's points
    - Adds the item to the user's inventory or increases its quantity
    - Updates the user's points per click and points per second
    - Returns the result of the purchase
    
    Path Parameters:
    - **item_id**: ID of the item to purchase
    """
    # Check if item exists first
    item = crud.item.get(db, item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    
    result = crud.game.buy_item(db, current_user.id, item_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return schemas.PurchaseResult(**result)


@game_router.get(
    "/leaderboard",
    response_model=List[schemas.LeaderboardEntry],
    status_code=status.HTTP_200_OK,
    summary="Get leaderboard",
    description="Get the top players by lifetime points"
)
def get_leaderboard(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Get the leaderboard of top players sorted by lifetime points.
    
    Query Parameters:
    - **limit**: Maximum number of entries to return (default: 10)
    """
    return crud.game.get_leaderboard(db, limit)


# Start the periodic leaderboard update task
@game_router.on_event("startup")
async def startup_event():
    """Start the background task for leaderboard updates when the application starts"""
    BackgroundTasks().add_task(periodic_leaderboard_update)


@game_router.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str, db: Session = Depends(get_db)):
    """
    WebSocket endpoint for real-time game interactions.
    
    This endpoint:
    - Validates the user token
    - Establishes a WebSocket connection
    - Processes game events in real-time (clicks, purchases, etc.)
    - Sends game state updates to the client
    
    Path Parameters:
    - **token**: JWT access token for authentication
    """
    # Authenticate user
    user_id = await get_user_id_from_token(token)
    if user_id is None:
        await websocket.close(code=1008)  # Policy violation
        return
        
    # Accept connection and add to connection manager
    await manager.connect(websocket, user_id)
    
    try:
        # Send initial state
        user = crud.game.get_user_game_state(db, user_id)
        await manager.send_personal_message({
            "type": "game_state", 
            "data": jsonable_encoder(user)
        }, user_id)
        
        # Process messages
        while True:
            # Wait for messages from the client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message["type"] == "click":
                # Process click
                points_earned, user = crud.game.process_click(db, user_id)
                
                # Send click result back to user
                await manager.send_personal_message({
                    "type": "click_result",
                    "data": {
                        "points_earned": points_earned,
                        "new_total": user.points,
                        "lifetime_points": user.lifetime_points,
                        "clicks": user.clicks
                    }
                }, user_id)
                
            elif message["type"] == "buy_item":
                # Process item purchase
                item_id = message["item_id"]
                result = crud.game.buy_item(db, user_id, item_id)
                
                # Send purchase result back to user
                await manager.send_personal_message({
                    "type": "purchase_result",
                    "data": result
                }, user_id)
                
                # If the purchase changes the leaderboard, update all clients
                if result["success"]:
                    await manager.broadcast_leaderboard()
            
            elif message["type"] == "get_state":
                # Send current state
                user = crud.game.get_user_game_state(db, user_id)
                await manager.send_personal_message({
                    "type": "game_state", 
                    "data": jsonable_encoder(user)
                }, user_id)
                
            elif message["type"] == "get_items":
                # Get all items with calculated costs
                user = crud.game.get_user_game_state(db, user_id)
                all_items = crud.item.get_all_items(db)
                user_items_db = crud.item.get_user_items(db, user_id)
                user_items = {ui.item_id: ui.quantity for ui in user_items_db}
                
                # Create calculated items list
                calculated_items = []
                for item in all_items:
                    quantity = user_items.get(item.id, 0)
                    current_cost = crud.item.calculate_item_cost(
                        item.base_cost, quantity, item.cost_multiplier
                    )
                    calculated_items.append({
                        "id": item.id,
                        "name": item.name,
                        "description": item.description,
                        "base_cost": item.base_cost,
                        "current_cost": current_cost,
                        "points_per_click": item.points_per_click,
                        "points_per_second": item.points_per_second,
                        "cost_multiplier": item.cost_multiplier,
                        "quantity": quantity,
                        "image_url": item.image_url
                    })
                
                # Send items to user
                await manager.send_personal_message({
                    "type": "items_list", 
                    "data": calculated_items
                }, user_id)
                
    except WebSocketDisconnect:
        # Remove from connection manager on disconnect
        manager.disconnect(user_id)
    except Exception as e:
        # Log error and disconnect
        print(f"WebSocket error: {str(e)}")
        manager.disconnect(user_id)
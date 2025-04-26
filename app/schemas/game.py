from typing import Optional, List

from pydantic import BaseModel, Field

from app.schemas.item import UserItem, CalculatedItem


class GameState(BaseModel):
    """Current game state for a user"""
    points: int = Field(..., description="Current points")
    lifetime_points: int = Field(..., description="Total points earned")
    clicks: int = Field(..., description="Number of clicks")
    points_per_click: float = Field(..., description="Points earned per click")
    points_per_second: float = Field(..., description="Points earned passively per second")
    
    class Config:
        from_attributes = True


class GameStateUpdate(BaseModel):
    """Update to game state"""
    points: Optional[int] = Field(None, description="Current points")
    lifetime_points: Optional[int] = Field(None, description="Total points earned")
    clicks: Optional[int] = Field(None, description="Number of clicks")
    

class LeaderboardEntry(BaseModel):
    """Schema for leaderboard entries"""
    id: int = Field(..., description="User ID")
    nickname: str = Field(..., description="User's nickname")
    lifetime_points: int = Field(..., description="Total points earned")
    rank: int = Field(..., description="Rank on the leaderboard")


class GameStateWithItems(GameState):
    """Game state including all items"""
    items: List[CalculatedItem] = Field([], description="List of all available items with calculated costs")


class ClickResult(BaseModel):
    """Result of a click action"""
    points_earned: float = Field(..., description="Points earned from this click")
    new_total: int = Field(..., description="New total points")
    lifetime_points: int = Field(..., description="Updated lifetime points")
    clicks: int = Field(..., description="Updated click count")


class PurchaseResult(BaseModel):
    """Result of an item purchase"""
    success: bool = Field(..., description="Whether the purchase was successful")
    message: str = Field(..., description="Message about the purchase")
    new_points: Optional[int] = Field(None, description="New points balance after purchase")
    new_points_per_click: Optional[float] = Field(None, description="New points per click after purchase")
    new_points_per_second: Optional[float] = Field(None, description="New points per second after purchase")
    item_quantity: Optional[int] = Field(None, description="New quantity of the purchased item")
    item_cost: Optional[int] = Field(None, description="New cost of the item for next purchase")


__all__ = [
    "GameState",
    "GameStateUpdate", 
    "LeaderboardEntry",
    "GameStateWithItems",
    "ClickResult",
    "PurchaseResult"
]
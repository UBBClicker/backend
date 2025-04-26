from typing import Optional, List
from pydantic import BaseModel, Field


class ItemBase(BaseModel):
    name: str = Field(..., description="Item name")
    description: str = Field(..., description="Item description")
    base_cost: int = Field(..., description="Base cost of the item")
    points_per_click: float = Field(0.0, description="Additional points per click from this item")
    points_per_second: float = Field(0.0, description="Additional points per second from this item")
    cost_multiplier: float = Field(1.15, description="Cost multiplier for each purchase")
    image_url: Optional[str] = Field(None, description="URL to the item's image")


class ItemCreate(ItemBase):
    """Schema for creating a new item"""
    pass


class ItemUpdate(BaseModel):
    """Schema for updating an item"""
    name: Optional[str] = Field(None, description="Item name")
    description: Optional[str] = Field(None, description="Item description")
    base_cost: Optional[int] = Field(None, description="Base cost of the item")
    points_per_click: Optional[float] = Field(None, description="Additional points per click from this item")
    points_per_second: Optional[float] = Field(None, description="Additional points per second from this item")
    cost_multiplier: Optional[float] = Field(None, description="Cost multiplier for each purchase")
    image_url: Optional[str] = Field(None, description="URL to the item's image")


class Item(ItemBase):
    """Schema for an item in database"""
    id: int

    class Config:
        from_attributes = True


class UserItemBase(BaseModel):
    """Base schema for user's items"""
    item_id: int = Field(..., description="ID of the item")
    quantity: int = Field(..., description="Quantity of the item owned")


class UserItemCreate(UserItemBase):
    """Schema for creating a user's item"""
    pass


class UserItem(UserItemBase):
    """Full schema for a user's item"""
    id: int
    user_id: int
    item: Item

    class Config:
        from_attributes = True


class UserItemSimple(UserItemBase):
    """Simplified schema for a user's item"""
    id: int
    
    class Config:
        from_attributes = True


class CalculatedItem(BaseModel):
    """Schema including calculated current cost"""
    id: int = Field(..., description="Item ID")
    name: str = Field(..., description="Item name")
    description: str = Field(..., description="Item description")
    base_cost: int = Field(..., description="Base cost of the item")
    current_cost: int = Field(..., description="Current cost based on owned quantity")
    points_per_click: float = Field(..., description="Additional points per click from this item")
    points_per_second: float = Field(..., description="Additional points per second from this item")
    cost_multiplier: float = Field(..., description="Cost multiplier for each purchase")
    quantity: int = Field(..., description="Quantity owned by user")
    image_url: Optional[str] = Field(None, description="URL to the item's image")


__all__ = [
    "ItemBase",
    "ItemCreate",
    "ItemUpdate",
    "Item",
    "UserItemBase",
    "UserItemCreate",
    "UserItem",
    "UserItemSimple",
    "CalculatedItem"
]
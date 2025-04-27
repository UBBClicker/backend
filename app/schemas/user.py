from typing import Optional, List

from pydantic import BaseModel, Field


class UserBase(BaseModel):
    nickname: str = Field(..., description="The user's nickname")


class UserCreate(UserBase):
    password: str = Field(...,
                          description="The user's password",
                          min_length=5,
                          max_length=20)


class UserUpdate(BaseModel):
    password: Optional[str] = Field(None,
                                    description="The user's password",
                                    min_length=5,
                                    max_length=20)


class UserInDB(UserBase):
    id: int
    password: str  # No length constraints for the hashed password
    points: int = Field(0, description="Current points")
    lifetime_points: int = Field(0, description="Total points earned")
    clicks: int = Field(0, description="Number of clicks")
    points_per_click: float = Field(1.0, description="Points earned per click")
    points_per_second: float = Field(0.0, description="Points earned passively per second")
    
    class Config:
        from_attributes = True


class UserResponse(UserBase):
    id: int
    
    class Config:
        from_attributes = True


class UserGameResponse(UserResponse):
    """User response with game data"""
    points: int
    lifetime_points: int
    clicks: int
    points_per_click: float
    points_per_second: float
    
    class Config:
        from_attributes = True


__all__ = [
    'UserBase',
    'UserCreate',
    'UserUpdate',
    'UserInDB',
    'UserResponse',
    'UserGameResponse'
]

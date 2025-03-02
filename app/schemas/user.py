from typing import Optional

from pydantic import BaseModel, Field


class UserBase(BaseModel):
    password: Optional[str] = Field(None,
                                    description="The user's password",
                                    min_length=5,
                                    max_length=20)


class UserCreate(UserBase):
    nickname: str = Field(..., description="The user's nickname")
    password: str = Field(...,
                          description="The user's password",
                          min_length=5,
                          max_length=20)


class UserUpdate(UserBase):
    pass


class User(UserCreate):
    pass


__all__ = [
    'UserBase',
    'UserCreate',
    'UserUpdate',
    'User'
]

from typing import Optional
from pydantic import BaseModel


class Token(BaseModel):
    """Token schema for login response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """JWT token data schema."""
    sub: Optional[str] = None
    exp: int = 0


class TokenPayload(TokenData):
    """Alias for TokenData to maintain backward compatibility."""
    pass


class LoginForm(BaseModel):
    """Login form schema."""
    nickname: str
    password: str


__all__ = ["Token", "TokenData", "TokenPayload", "LoginForm"]
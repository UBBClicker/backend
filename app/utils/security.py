from datetime import datetime, timedelta
from typing import Optional, Union

from passlib.context import CryptContext
from jose import jwt
from pydantic import ValidationError

from app.config import config
from app.schemas.token import TokenData

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Constants
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def create_access_token(
    subject: Union[str, int], expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT access token."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, config.PASSWORD_TOKEN, algorithm="HS256")
    return encoded_jwt


def validate_token(token: str) -> Optional[TokenData]:
    """Validate JWT token and return payload."""
    try:
        payload = jwt.decode(
            token, config.PASSWORD_TOKEN, algorithms=["HS256"]
        )
        token_data = TokenData(**payload)
        
        if datetime.fromtimestamp(token_data.exp) < datetime.utcnow():
            return None
        
        return token_data
    except (jwt.JWTError, ValidationError):
        return None


__all__ = [
    "verify_password",
    "get_password_hash",
    "create_access_token",
    "validate_token",
    "ACCESS_TOKEN_EXPIRE_MINUTES"
]
from fastapi import APIRouter, HTTPException, status
from odmantic import exceptions as odmantic_exceptions

from .. import schemas, mongodb

user_router = APIRouter(prefix="/user", tags=["User"])


@user_router.post("/register")
async def register_user(user: schemas.UserCreate):
    try:
        await mongodb.user.register(user)

    except odmantic_exceptions.DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists",
        )

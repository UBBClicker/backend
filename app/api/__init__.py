from fastapi import APIRouter

from .user import user_router
from .game import game_router
from .item import item_router

root_router = APIRouter()
root_router.include_router(user_router)
root_router.include_router(game_router)
root_router.include_router(item_router)

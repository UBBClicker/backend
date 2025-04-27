from fastapi import WebSocket, Depends
from typing import Dict, List, Any
import json
from sqlalchemy.orm import Session
import asyncio

from app.database import get_db, SessionLocal
from app import crud
from app.utils.security import validate_token


class ConnectionManager:
    def __init__(self):
        # Maps user_id to WebSocket connection
        self.active_connections: Dict[int, WebSocket] = {}
        # For broadcasting updates to all users
        self.broadcast_connections: List[WebSocket] = []
        
    async def connect(self, websocket: WebSocket, user_id: int):
        """Connect a user's websocket and register them by user_id"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.broadcast_connections.append(websocket)
        
    def disconnect(self, user_id: int):
        """Disconnect a user's websocket"""
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            if websocket in self.broadcast_connections:
                self.broadcast_connections.remove(websocket)
            del self.active_connections[user_id]
            
    async def send_personal_message(self, message: Any, user_id: int):
        """Send a message to a specific user"""
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(message)
            
    async def broadcast(self, message: Any):
        """Send a message to all connected users"""
        for connection in self.broadcast_connections:
            await connection.send_json(message)
            
    async def broadcast_leaderboard(self):
        """Broadcast updated leaderboard to all connected users"""
        # Open DB session for the background task
        db = SessionLocal()
        try:
            leaderboard = crud.game.get_leaderboard(db)
            await self.broadcast({
                "type": "leaderboard_update",
                "data": leaderboard
            })
        finally:
            db.close()


# Create a global connection manager instance
manager = ConnectionManager()


# Define a background task for periodic leaderboard updates
async def periodic_leaderboard_update():
    """Background task to periodically update the leaderboard for all clients"""
    while True:
        await manager.broadcast_leaderboard()
        # Wait 5 seconds between updates
        await asyncio.sleep(5)


# Helper function to get user_id from token
async def get_user_id_from_token(token: str) -> int:
    """Validate token and extract user_id"""
    token_data = validate_token(token)
    if token_data is None:
        return None
    return int(token_data.sub)
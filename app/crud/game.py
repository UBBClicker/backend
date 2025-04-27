from sqlalchemy.orm import Session
from sqlalchemy import desc, func
import time
from typing import List, Dict, Optional, Tuple

from app.models.user import User
from app.models.item import Item, UserItem
from app.schemas.game import GameStateUpdate
from app.crud.item import item as item_crud


class CRUDGame:
    def get_user_game_state(self, db: Session, user_id: int) -> User:
        """Get the current game state for a user"""
        user = db.query(User).filter(User.id == user_id).first()
        
        # Update points based on passive income since last update
        if user:
            self.update_passive_points(db, user)
        
        return user
    
    def update_passive_points(self, db: Session, user: User) -> User:
        """Update user's points based on passive income since last update"""
        current_time = int(time.time())
        
        # If this is the first update, just set the timestamp
        if user.last_updated == 0:
            user.last_updated = current_time
            db.commit()
            return user
            
        # Calculate time elapsed since last update in seconds
        elapsed_seconds = current_time - user.last_updated
        
        # Only update if meaningful time has passed
        if elapsed_seconds > 0 and user.points_per_second > 0:
            # Calculate points earned passively
            points_earned = int(user.points_per_second * elapsed_seconds)
            
            # Update user's points and lifetime points
            user.points += points_earned
            user.lifetime_points += points_earned
            user.last_updated = current_time
            
            db.commit()
            db.refresh(user)
        elif elapsed_seconds > 0:
            # Just update the timestamp if no passive income
            user.last_updated = current_time
            db.commit()
            
        return user
    
    def process_click(self, db: Session, user_id: int) -> Tuple[float, User]:
        """Process a user's click and return points earned and updated user"""
        user = self.get_user_game_state(db, user_id)
        
        if not user:
            return 0, None
        
        # Calculate points earned from this click
        points_earned = user.points_per_click
        
        # Update user stats
        user.points += int(points_earned)
        user.lifetime_points += int(points_earned)
        user.clicks += 1
        
        db.commit()
        db.refresh(user)
        
        return points_earned, user
    
    def buy_item(self, db: Session, user_id: int, item_id: int) -> Optional[Dict]:
        """Process item purchase and return result"""
        user = self.get_user_game_state(db, user_id)
        if not user:
            return None
            
        item = item_crud.get(db, item_id)
        if not item:
            return {
                "success": False,
                "message": "Item not found"
            }
            
        # Get current quantity and calculate cost
        user_item = item_crud.get_user_item(db, user_id, item_id)
        current_quantity = user_item.quantity if user_item else 0
        cost = item_crud.calculate_item_cost(item.base_cost, current_quantity, item.cost_multiplier)
        
        # Check if user has enough points
        if user.points < cost:
            return {
                "success": False,
                "message": "Not enough points"
            }
            
        # Process purchase
        user.points -= cost
        
        # Add item to user's inventory
        user_item = item_crud.add_user_item(db, user_id, item_id)
        
        # Update user's stats based on item bonuses
        user.points_per_click += item.points_per_click
        user.points_per_second += item.points_per_second
        
        db.commit()
        db.refresh(user)
        
        # Calculate new cost for the next purchase
        new_cost = item_crud.calculate_item_cost(
            item.base_cost, user_item.quantity, item.cost_multiplier
        )
        
        return {
            "success": True,
            "message": f"Successfully purchased {item.name}",
            "new_points": user.points,
            "new_points_per_click": user.points_per_click,
            "new_points_per_second": user.points_per_second,
            "item_quantity": user_item.quantity,
            "item_cost": new_cost
        }
    
    def get_leaderboard(self, db: Session, limit: int = 10) -> List[Dict]:
        """Get the top users by lifetime points"""
        users = db.query(User).order_by(desc(User.lifetime_points)).limit(limit).all()
        
        result = []
        for i, user in enumerate(users):
            result.append({
                "id": user.id,
                "nickname": user.nickname,
                "lifetime_points": user.lifetime_points,
                "rank": i + 1
            })
            
        return result
    
    def update_game_state(self, db: Session, user_id: int, state_update: GameStateUpdate) -> User:
        """Update game state for a user"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
            
        # Update fields if provided
        if state_update.points is not None:
            user.points = state_update.points
            
        if state_update.lifetime_points is not None:
            user.lifetime_points = state_update.lifetime_points
            
        if state_update.clicks is not None:
            user.clicks = state_update.clicks
            
        db.commit()
        db.refresh(user)
        return user
            

game = CRUDGame()
from sqlalchemy import Column, Integer, String, Float, ForeignKey, BigInteger, Boolean
from sqlalchemy.orm import relationship

from app.database import Base


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)
    base_cost = Column(Integer)
    points_per_click = Column(Float, default=0.0)  # Additional points per click
    points_per_second = Column(Float, default=0.0)  # Additional points per second
    cost_multiplier = Column(Float, default=1.15)  # Cost increase per purchase
    image_url = Column(String, nullable=True)
    
    # Relationships
    user_items = relationship("UserItem", back_populates="item")


class UserItem(Base):
    __tablename__ = "user_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    item_id = Column(Integer, ForeignKey("items.id"))
    quantity = Column(Integer, default=0)
    
    # Relationships
    user = relationship("User", back_populates="user_items")
    item = relationship("Item", back_populates="user_items")
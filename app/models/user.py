from sqlalchemy import Column, Integer, String, Float, ForeignKey, BigInteger
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    nickname = Column(String, unique=True, index=True)
    password = Column(String)
    
    # Game-related fields
    points = Column(BigInteger, default=0)  # Current points
    lifetime_points = Column(BigInteger, default=0)  # Total points ever earned
    clicks = Column(Integer, default=0)  # Number of clicks
    points_per_click = Column(Float, default=1.0)  # Points earned per click
    points_per_second = Column(Float, default=0.0)  # Points earned passively per second
    last_updated = Column(Integer, default=0)  # Timestamp for calculating passive points
    
    # Relationships
    user_items = relationship("UserItem", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        {"extend_existing": True},
    )

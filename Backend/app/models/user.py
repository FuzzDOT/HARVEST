"""
User Model
Defines the user entity for authentication and profile management.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    """User model for authentication and profile management."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone_number = Column(String(20), unique=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # Profile information
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    farm_name = Column(String(100))
    location = Column(String(100))
    coordinates = Column(String(50))  # "lat,lng" format
    
    # User type and verification
    user_type = Column(String(20), default="farmer")  # farmer, buyer, trader, admin
    is_verified = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)
    phone_verified = Column(Boolean, default=False)
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # Preferences
    preferred_language = Column(String(10), default="en")
    notification_preferences = Column(Text)  # JSON string
    
    # Farm details
    farm_size = Column(String(20))  # e.g., "5 acres", "2 hectares"
    primary_crops = Column(Text)  # JSON array of crop types
    farming_experience = Column(Integer)  # years
    farming_methods = Column(Text)  # JSON array: organic, conventional, etc.
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    
    # Relationships
    predictions = relationship("Prediction", back_populates="user")
    alerts = relationship("Alert", back_populates="user")
    products = relationship("Product", foreign_keys="Product.seller_id", back_populates="seller")
    orders_as_buyer = relationship("Order", foreign_keys="Order.buyer_id", back_populates="buyer")
    orders_as_seller = relationship("Order", foreign_keys="Order.seller_id", back_populates="seller")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
    
    @property
    def full_name(self):
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"
    
    def to_dict(self):
        """Convert user object to dictionary (excluding sensitive data)."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "farm_name": self.farm_name,
            "location": self.location,
            "user_type": self.user_type,
            "is_verified": self.is_verified,
            "preferred_language": self.preferred_language,
            "farm_size": self.farm_size,
            "farming_experience": self.farming_experience,
            "created_at": self.created_at,
            "last_login": self.last_login
        }
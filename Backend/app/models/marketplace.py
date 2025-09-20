"""
Marketplace Models
Defines product and order entities for the agricultural marketplace.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from decimal import Decimal

from app.core.database import Base


class Product(Base):
    """Product model for marketplace listings."""
    
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Product information
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    category = Column(String(50), nullable=False, index=True)
    
    # Pricing and quantity
    price = Column(Numeric(10, 2), nullable=False)  # Price per unit
    quantity = Column(Float, nullable=False)  # Available quantity
    unit = Column(String(20), nullable=False)  # kg, tons, pieces, etc.
    
    # Location and logistics
    location = Column(String(100), nullable=False, index=True)
    coordinates = Column(String(50))  # "lat,lng" format
    
    # Quality and certification
    quality_grade = Column(String(10))  # A, B, C, Premium, etc.
    organic_certified = Column(Boolean, default=False)
    certifications = Column(Text)  # JSON array of certifications
    
    # Timing
    harvest_date = Column(DateTime)
    expiry_date = Column(DateTime)
    available_from = Column(DateTime)
    available_until = Column(DateTime)
    
    # Product attributes
    variety = Column(String(100))  # Crop variety
    size = Column(String(50))  # Small, Medium, Large, or specific dimensions
    color = Column(String(50))
    freshness_indicator = Column(String(20))  # Fresh, Good, Fair
    
    # Images and media
    image_urls = Column(Text)  # JSON array of image URLs
    video_url = Column(String(500))
    
    # Status and visibility
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    is_sold_out = Column(Boolean, default=False)
    
    # Negotiation
    price_negotiable = Column(Boolean, default=True)
    minimum_order = Column(Float)  # Minimum order quantity
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    seller = relationship("User", foreign_keys=[seller_id], back_populates="products")
    orders = relationship("Order", back_populates="product")
    
    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', price={self.price})>"
    
    @property
    def is_available(self):
        """Check if product is currently available."""
        return (
            self.is_active and 
            not self.is_sold_out and 
            self.quantity > 0
        )
    
    @property
    def total_value(self):
        """Calculate total value of available stock."""
        return float(self.price) * self.quantity if self.price and self.quantity else 0
    
    def to_dict(self):
        """Convert product to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "price": float(self.price) if self.price else None,
            "quantity": self.quantity,
            "unit": self.unit,
            "location": self.location,
            "quality_grade": self.quality_grade,
            "organic_certified": self.organic_certified,
            "harvest_date": self.harvest_date,
            "expiry_date": self.expiry_date,
            "is_available": self.is_available,
            "created_at": self.created_at
        }


class Order(Base):
    """Order model for marketplace transactions."""
    
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    # Order details
    quantity = Column(Float, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False)
    
    # Status tracking
    status = Column(String(20), default="pending", index=True)
    # Status options: pending, confirmed, paid, packed, shipped, delivered, cancelled, disputed
    
    # Delivery information
    delivery_address = Column(Text, nullable=False)
    delivery_date = Column(DateTime)
    estimated_delivery = Column(DateTime)
    
    # Payment information
    payment_method = Column(String(50))
    payment_status = Column(String(20), default="pending")
    # Payment status: pending, paid, failed, refunded
    
    # Communication
    notes = Column(Text)  # Buyer notes
    seller_notes = Column(Text)  # Seller notes
    
    # Tracking
    tracking_number = Column(String(100))
    carrier = Column(String(50))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    confirmed_at = Column(DateTime(timezone=True))
    shipped_at = Column(DateTime(timezone=True))
    delivered_at = Column(DateTime(timezone=True))
    cancelled_at = Column(DateTime(timezone=True))
    
    # Relationships
    buyer = relationship("User", foreign_keys=[buyer_id], back_populates="orders_as_buyer")
    seller = relationship("User", foreign_keys=[seller_id], back_populates="orders_as_seller")
    product = relationship("Product", back_populates="orders")
    
    def __repr__(self):
        return f"<Order(id={self.id}, buyer_id={self.buyer_id}, product_id={self.product_id}, status='{self.status}')>"
    
    @property
    def is_active(self):
        """Check if order is in an active state."""
        active_statuses = ["pending", "confirmed", "paid", "packed", "shipped"]
        return self.status in active_statuses
    
    @property
    def can_be_cancelled(self):
        """Check if order can be cancelled."""
        cancellable_statuses = ["pending", "confirmed"]
        return self.status in cancellable_statuses
    
    @property
    def is_completed(self):
        """Check if order is completed."""
        return self.status == "delivered"
    
    def to_dict(self):
        """Convert order to dictionary."""
        return {
            "id": self.id,
            "buyer_id": self.buyer_id,
            "seller_id": self.seller_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "unit_price": float(self.unit_price) if self.unit_price else None,
            "total_amount": float(self.total_amount) if self.total_amount else None,
            "status": self.status,
            "payment_status": self.payment_status,
            "delivery_address": self.delivery_address,
            "delivery_date": self.delivery_date,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
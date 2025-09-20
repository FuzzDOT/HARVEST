"""
Alert Model
Manages agricultural alerts and notifications.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Alert(Base):
    """Alert model for agricultural monitoring and notifications."""
    
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Alert configuration
    type = Column(String(50), nullable=False, index=True)
    # Types: weather, pest, disease, market, irrigation, harvest
    
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Condition settings
    condition = Column(String(100), nullable=False)
    # Examples: "temperature > 35", "rainfall < 10", "price_change > 0.1"
    
    threshold = Column(Float)
    operator = Column(String(10))  # >, <, >=, <=, ==, !=
    
    # Location and scope
    location = Column(String(100), index=True)
    coordinates = Column(String(50))  # "lat,lng" format
    radius = Column(Float)  # Alert radius in kilometers
    
    # Crop specific
    crop_type = Column(String(50), index=True)
    crop_stage = Column(String(30))  # seedling, flowering, harvest, etc.
    
    # Timing
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    time_of_day = Column(String(20))  # morning, afternoon, evening, all_day
    
    # Frequency and repetition
    frequency = Column(String(20), default="immediate")
    # Options: immediate, daily, weekly, custom
    
    repeat_interval = Column(Integer)  # Minutes between checks
    last_checked = Column(DateTime)
    last_triggered = Column(DateTime)
    
    # Notification settings
    notification_methods = Column(JSON)  # ["sms", "email", "push", "websocket"]
    notification_language = Column(String(10), default="en")
    
    # Priority and urgency
    priority = Column(String(20), default="medium")
    # Options: low, medium, high, critical
    
    urgency_level = Column(Integer, default=3)  # 1-5 scale
    
    # Status
    is_active = Column(Boolean, default=True)
    is_triggered = Column(Boolean, default=False)
    trigger_count = Column(Integer, default=0)
    
    # Snooze functionality
    is_snoozed = Column(Boolean, default=False)
    snooze_until = Column(DateTime)
    
    # Advanced settings
    sensitivity = Column(Float, default=1.0)  # 0.1 to 2.0
    confirmation_required = Column(Boolean, default=False)
    auto_resolve = Column(Boolean, default=True)
    
    # Metadata
    tags = Column(JSON)  # Array of tags for categorization
    custom_data = Column(JSON)  # Additional custom parameters
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    activated_at = Column(DateTime(timezone=True))
    deactivated_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="alerts")
    
    def __repr__(self):
        return f"<Alert(id={self.id}, type='{self.type}', user_id={self.user_id}, active={self.is_active})>"
    
    @property
    def is_currently_active(self):
        """Check if alert is currently active considering time bounds."""
        if not self.is_active:
            return False
        
        from datetime import datetime
        now = datetime.utcnow()
        
        if self.start_date and now < self.start_date:
            return False
        
        if self.end_date and now > self.end_date:
            return False
        
        if self.is_snoozed and self.snooze_until and now < self.snooze_until:
            return False
        
        return True
    
    @property
    def should_check(self):
        """Determine if alert should be checked based on frequency."""
        if not self.is_currently_active:
            return False
        
        if not self.last_checked:
            return True
        
        from datetime import datetime, timedelta
        now = datetime.utcnow()
        
        if self.frequency == "immediate":
            return True
        elif self.frequency == "daily":
            return (now - self.last_checked).days >= 1
        elif self.frequency == "weekly":
            return (now - self.last_checked).days >= 7
        elif self.frequency == "custom" and self.repeat_interval:
            return (now - self.last_checked).total_seconds() >= (self.repeat_interval * 60)
        
        return True
    
    @property
    def days_since_created(self):
        """Calculate days since alert was created."""
        if not self.created_at:
            return None
        
        from datetime import datetime
        return (datetime.utcnow() - self.created_at.replace(tzinfo=None)).days
    
    def trigger(self):
        """Mark alert as triggered."""
        from datetime import datetime
        self.is_triggered = True
        self.last_triggered = datetime.utcnow()
        self.trigger_count += 1
    
    def snooze(self, minutes: int):
        """Snooze alert for specified minutes."""
        from datetime import datetime, timedelta
        self.is_snoozed = True
        self.snooze_until = datetime.utcnow() + timedelta(minutes=minutes)
    
    def unsnooze(self):
        """Remove snooze from alert."""
        self.is_snoozed = False
        self.snooze_until = None
    
    def to_dict(self):
        """Convert alert to dictionary."""
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "description": self.description,
            "condition": self.condition,
            "threshold": self.threshold,
            "location": self.location,
            "crop_type": self.crop_type,
            "priority": self.priority,
            "is_active": self.is_active,
            "is_currently_active": self.is_currently_active,
            "is_triggered": self.is_triggered,
            "trigger_count": self.trigger_count,
            "notification_methods": self.notification_methods,
            "created_at": self.created_at,
            "last_triggered": self.last_triggered,
            "days_since_created": self.days_since_created
        }
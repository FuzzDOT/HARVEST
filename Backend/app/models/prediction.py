"""
Prediction Model
Handles ML prediction records and results storage.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Prediction(Base):
    """Prediction model for storing ML prediction results."""
    
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Prediction metadata
    type = Column(String(50), nullable=False, index=True)
    # Types: crop_yield, weather, pest_disease, market_price, demand_forecast
    
    model_version = Column(String(20))
    model_name = Column(String(100))
    
    # Input data
    input_data = Column(JSON)  # Store input parameters as JSON
    location = Column(String(100), index=True)
    crop_type = Column(String(50), index=True)
    
    # Results
    result = Column(JSON)  # Store prediction results as JSON
    confidence_score = Column(Float)  # 0.0 to 1.0
    
    # Weather prediction specific
    forecast_days = Column(Integer)
    weather_conditions = Column(JSON)
    
    # Crop yield specific
    predicted_yield = Column(Float)
    yield_unit = Column(String(20))  # tons/hectare, kg/acre, etc.
    
    # Market prediction specific
    predicted_price = Column(Float)
    price_currency = Column(String(10))
    price_trend = Column(String(20))  # rising, falling, stable
    
    # Risk assessment
    risk_level = Column(String(20))  # low, medium, high, critical
    risk_factors = Column(JSON)  # Array of risk factors
    
    # Recommendations
    recommendations = Column(JSON)  # Array of actionable recommendations
    action_items = Column(JSON)  # Specific action items
    
    # Validation and feedback
    actual_outcome = Column(JSON)  # Actual results for model validation
    feedback_rating = Column(Integer)  # 1-5 user rating
    feedback_comments = Column(Text)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_archived = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    prediction_date = Column(DateTime(timezone=True))  # When prediction was made
    target_date = Column(DateTime(timezone=True))  # Target date for prediction
    
    # Relationships
    user = relationship("User", back_populates="predictions")
    
    def __repr__(self):
        return f"<Prediction(id={self.id}, type='{self.type}', user_id={self.user_id})>"
    
    @property
    def accuracy_category(self):
        """Categorize prediction accuracy based on confidence score."""
        if not self.confidence_score:
            return "unknown"
        
        if self.confidence_score >= 0.9:
            return "very_high"
        elif self.confidence_score >= 0.8:
            return "high"
        elif self.confidence_score >= 0.7:
            return "medium"
        elif self.confidence_score >= 0.6:
            return "low"
        else:
            return "very_low"
    
    @property
    def days_since_prediction(self):
        """Calculate days since prediction was made."""
        if not self.created_at:
            return None
        
        from datetime import datetime
        return (datetime.utcnow() - self.created_at.replace(tzinfo=None)).days
    
    def to_dict(self):
        """Convert prediction to dictionary."""
        return {
            "id": self.id,
            "type": self.type,
            "location": self.location,
            "crop_type": self.crop_type,
            "confidence_score": self.confidence_score,
            "accuracy_category": self.accuracy_category,
            "risk_level": self.risk_level,
            "created_at": self.created_at,
            "prediction_date": self.prediction_date,
            "target_date": self.target_date,
            "days_since_prediction": self.days_since_prediction,
            "result": self.result,
            "recommendations": self.recommendations
        }
    
    def add_feedback(self, rating: int, comments: str = None, actual_outcome: dict = None):
        """Add user feedback to prediction."""
        self.feedback_rating = rating
        self.feedback_comments = comments
        if actual_outcome:
            self.actual_outcome = actual_outcome
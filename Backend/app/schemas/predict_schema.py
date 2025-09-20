"""
Prediction Schema Definitions
Pydantic models for prediction API requests and responses.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class PredictionType(str, Enum):
    """Supported prediction types."""
    CROP_YIELD = "crop_yield"
    WEATHER = "weather"
    PEST_DISEASE = "pest_disease"
    MARKET_PRICE = "market_price"
    DEMAND_FORECAST = "demand_forecast"


class CropType(str, Enum):
    """Common crop types."""
    RICE = "rice"
    WHEAT = "wheat"
    CORN = "corn"
    SOYBEANS = "soybeans"
    COTTON = "cotton"
    TOMATOES = "tomatoes"
    POTATOES = "potatoes"
    ONIONS = "onions"
    SUGARCANE = "sugarcane"
    OTHER = "other"


class PredictionRequest(BaseModel):
    """Base prediction request schema."""
    user_id: int
    prediction_type: PredictionType
    crop_type: CropType
    location: str = Field(..., min_length=1, max_length=100)
    planting_date: Optional[datetime] = None
    harvest_date: Optional[datetime] = None
    additional_data: Optional[Dict[str, Any]] = {}
    
    @validator('location')
    def validate_location(cls, v):
        if not v or v.strip() == "":
            raise ValueError('Location cannot be empty')
        return v.strip()
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": 1,
                "prediction_type": "crop_yield",
                "crop_type": "rice",
                "location": "Punjab, India",
                "planting_date": "2024-06-15T00:00:00",
                "additional_data": {
                    "soil_type": "clay",
                    "irrigation_method": "drip",
                    "farm_size": 5.0
                }
            }
        }


class CropYieldPrediction(BaseModel):
    """Crop yield prediction response."""
    prediction_id: int
    crop_type: str
    location: str
    predicted_yield: float = Field(..., description="Predicted yield value")
    yield_unit: str = Field(default="tons/hectare", description="Unit of measurement")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Prediction confidence (0-1)")
    factors: Dict[str, Any] = Field(default_factory=dict, description="Contributing factors")
    recommendations: List[str] = Field(default_factory=list, description="Actionable recommendations")
    risk_assessment: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "prediction_id": 123,
                "crop_type": "rice",
                "location": "Punjab, India",
                "predicted_yield": 4.5,
                "yield_unit": "tons/hectare",
                "confidence_score": 0.87,
                "factors": {
                    "weather_score": 0.9,
                    "soil_quality": 0.8,
                    "irrigation": 0.85
                },
                "recommendations": [
                    "Apply fertilizer 2 weeks before harvest",
                    "Monitor for pest activity"
                ]
            }
        }


class WeatherForecast(BaseModel):
    """Single day weather forecast."""
    date: datetime
    temperature_max: float
    temperature_min: float
    humidity: float
    rainfall: float
    wind_speed: float
    conditions: str
    
    class Config:
        schema_extra = {
            "example": {
                "date": "2024-01-15T00:00:00",
                "temperature_max": 28.5,
                "temperature_min": 18.2,
                "humidity": 65.0,
                "rainfall": 2.3,
                "wind_speed": 12.0,
                "conditions": "partly_cloudy"
            }
        }


class WeatherPrediction(BaseModel):
    """Weather prediction response."""
    location: str
    forecast_days: int
    daily_forecasts: List[WeatherForecast]
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    alerts: List[str] = Field(default_factory=list)
    
    class Config:
        schema_extra = {
            "example": {
                "location": "Punjab, India",
                "forecast_days": 7,
                "daily_forecasts": [],
                "confidence_score": 0.82,
                "alerts": ["Heavy rainfall expected on Day 3"]
            }
        }


class ThreatInfo(BaseModel):
    """Pest or disease threat information."""
    name: str
    type: str  # pest or disease
    risk_level: str
    description: str
    symptoms: List[str] = Field(default_factory=list)
    treatment: List[str] = Field(default_factory=list)
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Brown Planthopper",
                "type": "pest",
                "risk_level": "medium",
                "description": "Small insect that feeds on rice plants",
                "symptoms": ["Yellowing leaves", "Stunted growth"],
                "treatment": ["Apply neem oil", "Use sticky traps"]
            }
        }


class PestDiseasePrediction(BaseModel):
    """Pest and disease prediction response."""
    prediction_id: int
    crop_type: str
    location: str
    risk_level: str = Field(..., description="Overall risk level: low, medium, high, critical")
    threats: List[ThreatInfo] = Field(default_factory=list)
    prevention_measures: List[str] = Field(default_factory=list)
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    monitoring_schedule: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "prediction_id": 456,
                "crop_type": "rice",
                "location": "Punjab, India",
                "risk_level": "medium",
                "threats": [],
                "prevention_measures": [
                    "Regular field inspection",
                    "Maintain proper drainage"
                ],
                "confidence_score": 0.79
            }
        }


class PredictionResponse(BaseModel):
    """Generic prediction response."""
    id: int
    type: str
    location: str
    crop_type: Optional[str] = None
    confidence_score: Optional[float] = None
    created_at: datetime
    result: Dict[str, Any]
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 789,
                "type": "crop_yield",
                "location": "Punjab, India",
                "crop_type": "rice",
                "confidence_score": 0.87,
                "created_at": "2024-01-15T10:30:00",
                "result": {"predicted_yield": 4.5}
            }
        }


class PredictionFeedback(BaseModel):
    """Feedback for prediction accuracy."""
    prediction_id: int
    rating: int = Field(..., ge=1, le=5, description="Rating from 1-5")
    comments: Optional[str] = Field(None, max_length=500)
    actual_outcome: Optional[Dict[str, Any]] = None
    
    @validator('rating')
    def validate_rating(cls, v):
        if v < 1 or v > 5:
            raise ValueError('Rating must be between 1 and 5')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "prediction_id": 123,
                "rating": 4,
                "comments": "Very close to actual yield",
                "actual_outcome": {"actual_yield": 4.3}
            }
        }
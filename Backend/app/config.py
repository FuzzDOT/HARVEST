"""
Application Configuration
Settings and configuration management for HARVEST backend.
"""

import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    APP_NAME: str = "HARVEST"
    VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    
    # Security
    SECRET_KEY: str = Field(env="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        env="ALLOWED_ORIGINS"
    )
    
    # Database
    DATABASE_URL: str = Field(env="DATABASE_URL")
    DB_POOL_SIZE: int = Field(default=10, env="DB_POOL_SIZE")
    DB_MAX_OVERFLOW: int = Field(default=20, env="DB_MAX_OVERFLOW")
    
    # Redis Cache
    REDIS_URL: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    CACHE_TTL: int = Field(default=3600, env="CACHE_TTL")  # 1 hour
    
    # External APIs
    WEATHER_API_KEY: str = Field(env="WEATHER_API_KEY")
    WEATHER_API_URL: str = Field(
        default="https://api.openweathermap.org/data/2.5",
        env="WEATHER_API_URL"
    )
    
    MARKET_API_KEY: str = Field(env="MARKET_API_KEY")
    MARKET_API_URL: str = Field(env="MARKET_API_URL")
    
    # SMS Service
    TWILIO_ACCOUNT_SID: str = Field(env="TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: str = Field(env="TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER: str = Field(env="TWILIO_PHONE_NUMBER")
    
    # Translation Service
    GOOGLE_TRANSLATE_API_KEY: str = Field(env="GOOGLE_TRANSLATE_API_KEY")
    
    # ML Model Settings
    MODEL_PATH: str = Field(default="ml/models/", env="MODEL_PATH")
    MODEL_UPDATE_INTERVAL: int = Field(default=24, env="MODEL_UPDATE_INTERVAL")  # hours
    
    # File Storage
    UPLOAD_PATH: str = Field(default="data/uploads/", env="UPLOAD_PATH")
    MAX_FILE_SIZE: int = Field(default=10485760, env="MAX_FILE_SIZE")  # 10MB
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FILE: str = Field(default="logs/harvest.log", env="LOG_FILE")
    
    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = Field(default=30, env="WS_HEARTBEAT_INTERVAL")
    
    # Scheduler
    SCHEDULER_TIMEZONE: str = Field(default="UTC", env="SCHEDULER_TIMEZONE")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()
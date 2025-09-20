"""
Prediction API Endpoints
Handles agricultural prediction requests and ML model interactions.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.predict_schema import (
    PredictionRequest,
    PredictionResponse,
    CropYieldPrediction,
    WeatherPrediction,
    PestDiseasePrediction
)
from app.services.ml_models import MLModelService
from app.services.data_pipeline import DataPipelineService
from app.models.prediction import Prediction
from app.utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()


@router.post("/predict/crop-yield", response_model=CropYieldPrediction)
async def predict_crop_yield(
    request: PredictionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Predict crop yield based on various factors including weather, soil, and historical data.
    """
    try:
        ml_service = MLModelService()
        data_service = DataPipelineService()
        
        # Prepare input data
        input_data = await data_service.prepare_yield_prediction_data(
            crop_type=request.crop_type,
            location=request.location,
            planting_date=request.planting_date,
            additional_data=request.additional_data
        )
        
        # Make prediction
        prediction_result = await ml_service.predict_crop_yield(input_data)
        
        # Save prediction to database
        prediction_record = Prediction(
            type="crop_yield",
            input_data=input_data,
            result=prediction_result,
            user_id=request.user_id,
            location=request.location
        )
        db.add(prediction_record)
        db.commit()
        
        # Schedule model retraining if needed
        background_tasks.add_task(
            ml_service.check_and_retrain_model,
            "crop_yield"
        )
        
        return CropYieldPrediction(
            prediction_id=prediction_record.id,
            crop_type=request.crop_type,
            location=request.location,
            predicted_yield=prediction_result["yield"],
            confidence_score=prediction_result["confidence"],
            factors=prediction_result["factors"],
            recommendations=prediction_result["recommendations"]
        )
        
    except Exception as e:
        logger.error(f"Crop yield prediction failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Prediction service unavailable"
        )


@router.post("/predict/weather", response_model=WeatherPrediction)
async def predict_weather(
    location: str,
    days_ahead: int = 7,
    db: Session = Depends(get_db)
):
    """
    Predict weather conditions for agricultural planning.
    """
    try:
        data_service = DataPipelineService()
        ml_service = MLModelService()
        
        # Get historical weather data
        weather_data = await data_service.get_weather_data(location, days_ahead)
        
        # Make weather prediction
        prediction_result = await ml_service.predict_weather(
            location=location,
            historical_data=weather_data,
            forecast_days=days_ahead
        )
        
        return WeatherPrediction(
            location=location,
            forecast_days=days_ahead,
            daily_forecasts=prediction_result["forecasts"],
            confidence_score=prediction_result["confidence"],
            alerts=prediction_result.get("alerts", [])
        )
        
    except Exception as e:
        logger.error(f"Weather prediction failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Weather prediction service unavailable"
        )


@router.post("/predict/pest-disease", response_model=PestDiseasePrediction)
async def predict_pest_disease(
    request: PredictionRequest,
    db: Session = Depends(get_db)
):
    """
    Predict pest and disease risks for crops.
    """
    try:
        ml_service = MLModelService()
        data_service = DataPipelineService()
        
        # Prepare environmental data
        env_data = await data_service.get_environmental_data(
            location=request.location,
            crop_type=request.crop_type
        )
        
        # Make prediction
        prediction_result = await ml_service.predict_pest_disease(
            crop_type=request.crop_type,
            environmental_data=env_data,
            location=request.location
        )
        
        # Save prediction
        prediction_record = Prediction(
            type="pest_disease",
            input_data={"crop_type": request.crop_type, "location": request.location},
            result=prediction_result,
            user_id=request.user_id,
            location=request.location
        )
        db.add(prediction_record)
        db.commit()
        
        return PestDiseasePrediction(
            prediction_id=prediction_record.id,
            crop_type=request.crop_type,
            location=request.location,
            risk_level=prediction_result["risk_level"],
            threats=prediction_result["threats"],
            prevention_measures=prediction_result["prevention_measures"],
            confidence_score=prediction_result["confidence"]
        )
        
    except Exception as e:
        logger.error(f"Pest/disease prediction failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Pest/disease prediction service unavailable"
        )


@router.get("/predict/history/{user_id}")
async def get_prediction_history(
    user_id: int,
    limit: int = 50,
    offset: int = 0,
    prediction_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get user's prediction history.
    """
    try:
        query = db.query(Prediction).filter(Prediction.user_id == user_id)
        
        if prediction_type:
            query = query.filter(Prediction.type == prediction_type)
        
        predictions = query.offset(offset).limit(limit).all()
        
        return {
            "predictions": [
                {
                    "id": p.id,
                    "type": p.type,
                    "location": p.location,
                    "created_at": p.created_at,
                    "result": p.result
                }
                for p in predictions
            ],
            "total": query.count()
        }
        
    except Exception as e:
        logger.error(f"Failed to get prediction history: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve prediction history"
        )
"""
HARVEST Backend FastAPI Application

This FastAPI application provides REST endpoints for agricultural yield prediction
and crop recommendation services.
"""

from fastapi import FastAPI, HTTPException, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file only if not in production
if not os.getenv("RENDER"):  # Render sets this automatically
    load_dotenv()

# Import HARVEST modules
from src.pipelines.predict_short_term import (
    predict_month_recommendations,
    run_short_term_pipeline_for_all_parcels
)
from src.pipelines.predict_long_term import (
    plan_annual_crop_rotation,
    run_long_term_pipeline_for_all_parcels
)
from src.io_.loaders import (
    load_parcels,
    load_crops,
    load_fertilizers,
    load_weather_forecast,
    load_weather_normals,
    load_price_history
)
from src.model.profit_calc import calculate_net_profit
from src.model.ranker import (
    rank_crops_by_profit,
    filter_profitable_crops,
    create_recommendation_summary
)
from src.rules.crop_eligibility import filter_crops_by_month
from src.utils.tables import format_recommendations_table
from src.services import process_user_prediction_request, format_prediction_results
from src.services.image_service import process_prediction_and_send_images
from src.utils.sessions import session_manager
from src.model.crop_advice_wrapper import CropAdviceWrapper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="HARVEST - Agricultural Prediction API",
    description="API for crop recommendations and agricultural yield predictions",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add missing root and health endpoints
@app.get("/api/v1/", tags=["System"])
async def api_root():
    """API root endpoint"""
    return {
        "message": "HARVEST Agricultural Prediction API",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/health", tags=["System"])
async def api_health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class ParcelInfo(BaseModel):
    parcel_id: str
    region: str
    acreage: float
    soil_ph: float
    soil_type: str

class CropInfo(BaseModel):
    state: str
    crop_name: str
    category: str
    yield_lb_per_acre_est: int
    price_usd_per_lb_est: float

class WeatherConditions(BaseModel):
    temperature: float = Field(..., description="Temperature in Fahrenheit")
    rainfall: float = Field(..., description="Rainfall in inches")
    confidence: Optional[float] = Field(None, description="Forecast confidence percentage")

class ProfitCalculationRequest(BaseModel):
    crop_name: str
    weather_conditions: WeatherConditions
    soil_ph: float
    month: int = Field(..., ge=1, le=12)
    price_override: Optional[float] = None

class MonthlyRecommendationRequest(BaseModel):
    parcel_id: str
    month: int = Field(..., ge=1, le=12)
    top_n: int = Field(5, ge=1, le=20)
    ranking_method: str = Field("profit", pattern="^(profit|roi|yield|suitability)$")
    min_confidence: float = Field(70.0, ge=0, le=100)

class AnnualPlanRequest(BaseModel):
    parcel_id: str
    start_month: int = Field(1, ge=1, le=12)
    diversification_bonus: float = Field(0.1, ge=0, le=1)
    min_profit_threshold: float = Field(0.0)

class CropRecommendation(BaseModel):
    rank: int
    crop_name: str
    net_profit: float
    roi_percent: float
    adjusted_yield: float
    recommendation_confidence: Optional[float] = None

class MonthlyRecommendationResponse(BaseModel):
    parcel_id: str
    month: int
    region: str
    acreage: float
    weather_conditions: Dict[str, Any]
    recommendations: List[CropRecommendation]
    total_crops_evaluated: int
    ranking_method: str
    generated_at: str
    message: Optional[str] = None

class AnnualPlanResponse(BaseModel):
    parcel_id: str
    total_months_planned: int
    annual_summary: Dict[str, Any]
    rotation_sequence: List[Dict[str, Any]]
    generated_at: str


# New models for frontend integration
class LocationData(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in decimal degrees")


class UserPredictionRequest(BaseModel):
    location: LocationData
    timezone: str = Field(..., description="User's timezone (e.g., 'America/New_York')")
    prediction_type: str = Field(..., pattern="^(short_term|long_term)$", description="Type of prediction")


class PredictionResults(BaseModel):
    session_id: str = Field(..., description="Session ID for accessing individual results")
    
    # Top 5 crop recommendations
    cropName1: Optional[str] = None
    cropName2: Optional[str] = None
    cropName3: Optional[str] = None
    cropName4: Optional[str] = None
    cropName5: Optional[str] = None
    
    # Crop prices
    cropPrice1: Optional[float] = None
    cropPrice2: Optional[float] = None
    cropPrice3: Optional[float] = None
    cropPrice4: Optional[float] = None
    cropPrice5: Optional[float] = None
    
    # Fertilizer names
    fertilizerName1: Optional[str] = None
    fertilizerName2: Optional[str] = None
    fertilizerName3: Optional[str] = None
    fertilizerName4: Optional[str] = None
    fertilizerName5: Optional[str] = None
    
    # Fertilizer prices
    fertilizerPrice1: Optional[float] = None
    fertilizerPrice2: Optional[float] = None
    fertilizerPrice3: Optional[float] = None
    fertilizerPrice4: Optional[float] = None
    fertilizerPrice5: Optional[float] = None
    
    # Images
    image1: Optional[str] = None
    image2: Optional[str] = None
    image3: Optional[str] = None
    image4: Optional[str] = None
    image5: Optional[str] = None
    
    # Additional data for frontend
    netProfit1: Optional[float] = None
    netProfit2: Optional[float] = None
    netProfit3: Optional[float] = None
    netProfit4: Optional[float] = None
    netProfit5: Optional[float] = None
    
    roiPercent1: Optional[float] = None
    roiPercent2: Optional[float] = None
    roiPercent3: Optional[float] = None
    roiPercent4: Optional[float] = None
    roiPercent5: Optional[float] = None
    
    confidence1: Optional[float] = None
    confidence2: Optional[float] = None
    confidence3: Optional[float] = None
    confidence4: Optional[float] = None
    confidence5: Optional[float] = None


# Health check endpoint
@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "service": "HARVEST Agricultural Prediction API",
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check with system status."""
    try:
        # Test data loading
        parcels = load_parcels()
        crops = load_crops()
        
        return {
            "status": "healthy",
            "data_status": {
                "parcels_loaded": len(parcels),
                "crops_available": len(crops),
                "timestamp": datetime.now().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy", 
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Add endpoint aliases for missing routes
@app.get("/api/v1/weather", tags=["Data"])
async def get_weather():
    """Get weather data (alias to forecast endpoint)"""
    return await get_weather_forecast()

@app.get("/api/v1/system/summary", tags=["Utilities"])
async def get_system_summary_alias():
    """System summary endpoint (alias)"""
    return await get_system_summary()

@app.post("/api/v1/predict/monthly", tags=["Predictions"])
async def predict_monthly_alias(request: MonthlyRecommendationRequest):
    """Monthly predictions endpoint (alias)"""
    return await predict_monthly_recommendations(request)

# Data endpoints
@app.get("/api/v1/parcels", response_model=List[ParcelInfo], tags=["Data"])
async def get_parcels():
    """Get all available parcels."""
    try:
        parcels_df = load_parcels()
        return parcels_df.to_dict('records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load parcels: {str(e)}")

@app.get("/api/v1/parcels/{parcel_id}", response_model=ParcelInfo, tags=["Data"])
async def get_parcel(parcel_id: str = Path(..., description="Parcel ID")):
    """Get specific parcel information."""
    try:
        from src.io_.loaders import load_parcel_by_id
        parcel = load_parcel_by_id(parcel_id)
        if not parcel:
            raise HTTPException(status_code=404, detail=f"Parcel {parcel_id} not found")
        return parcel
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load parcel: {str(e)}")

@app.get("/api/v1/crops", response_model=List[CropInfo], tags=["Data"])
async def get_crops():
    """Get all available crops."""
    try:
        crops_df = load_crops()
        return crops_df.to_dict('records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load crops: {str(e)}")

@app.get("/api/v1/crops/eligible/{month}", tags=["Data"])
async def get_eligible_crops(month: int = Path(..., ge=1, le=12, description="Month (1-12)")):
    """Get crops eligible for planting in a specific month."""
    try:
        eligible_crops = filter_crops_by_month(month)
        return {
            "month": month,
            "eligible_crops": eligible_crops,
            "count": len(eligible_crops)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get eligible crops: {str(e)}")

@app.get("/api/v1/weather/forecast", tags=["Data"])
async def get_weather_forecast():
    """Get current weather forecast data."""
    try:
        forecast_df = load_weather_forecast()
        return {
            "forecast_data": forecast_df.to_dict('records'),
            "count": len(forecast_df)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load weather forecast: {str(e)}")

@app.get("/api/v1/weather/normals", tags=["Data"])
async def get_weather_normals():
    """Get historical weather normals."""
    try:
        normals_df = load_weather_normals()
        return {
            "normals_data": normals_df.to_dict('records'),
            "count": len(normals_df)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load weather normals: {str(e)}")

# Prediction endpoints
@app.post("/api/v1/predict/month", tags=["Predictions"])
async def predict_monthly_recommendations(request: MonthlyRecommendationRequest):
    """Generate crop recommendations for a specific month."""
    try:
        from src.io_.loaders import load_parcel_by_id, load_weather_forecast
        from datetime import datetime
        
        # Get parcel information
        parcel = load_parcel_by_id(request.parcel_id)
        if not parcel:
            raise HTTPException(status_code=400, detail=f"Parcel {request.parcel_id} not found")
        
        result = predict_month_recommendations(
            parcel_id=request.parcel_id,
            month=request.month,
            top_n=request.top_n,
            ranking_method=request.ranking_method,
            min_confidence=request.min_confidence
        )
        
        # Add rank to recommendations if not present
        for i, rec in enumerate(result.get('recommendations', [])):
            if 'rank' not in rec:
                rec['rank'] = i + 1
        
        # Send images for the predicted crops (short-term prediction)
        image_send_result = None
        try:
            if result.get('recommendations'):
                logger.info(f"Sending images for short-term prediction (parcel: {request.parcel_id}, month: {request.month})")
                image_send_result = await process_prediction_and_send_images(
                    prediction_result=result,
                    prediction_type="short_term",
                    additional_metadata={
                        "ranking_method": request.ranking_method,
                        "min_confidence": request.min_confidence
                    }
                )
        except Exception as e:
            logger.error(f"Failed to send images for short-term prediction: {str(e)}")
            # Don't fail the entire request if image sending fails
            image_send_result = {"success": False, "error": str(e)}
        
        # Return the raw result without forcing it into MonthlyRecommendationResponse
        # since the pipeline function returns a simpler structure
        response = {
            "parcel_id": result.get('parcel_id', request.parcel_id),
            "month": result.get('month', request.month),
            "recommendations": result.get('recommendations', []),
            "message": result.get('message', ''),
            "total_crops_evaluated": len(result.get('recommendations', [])),
            "ranking_method": request.ranking_method,
            "generated_at": datetime.now().isoformat()
        }
        
        # Include image sending result if available
        if image_send_result:
            response["image_send_result"] = image_send_result
        
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.post("/api/v1/predict/month/all", tags=["Predictions"])
async def predict_monthly_all_parcels(
    month: int = Query(..., ge=1, le=12, description="Month (1-12)"),
    top_n: int = Query(5, ge=1, le=20, description="Number of recommendations per parcel"),
    ranking_method: str = Query("profit", pattern="^(profit|roi|yield|suitability)$"),
    min_confidence: float = Query(70.0, ge=0, le=100, description="Minimum forecast confidence")
):
    """Generate crop recommendations for all parcels for a specific month."""
    try:
        results = run_short_term_pipeline_for_all_parcels(
            month=month,
            top_n=top_n,
            ranking_method=ranking_method,
            min_confidence=min_confidence,
            save_results=False
        )
        
        return {
            "month": month,
            "results": results,
            "total_parcels": len(results),
            "successful_predictions": len([r for r in results if 'error' not in r and r.get('recommendations')]),
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Batch prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {str(e)}")

@app.post("/api/v1/plan/annual", response_model=AnnualPlanResponse, tags=["Planning"])
async def plan_annual_rotation(request: AnnualPlanRequest):
    """Generate annual crop rotation plan for a parcel."""
    try:
        result = plan_annual_crop_rotation(
            parcel_id=request.parcel_id,
            start_month=request.start_month,
            diversification_bonus=request.diversification_bonus,
            min_profit_threshold=request.min_profit_threshold
        )
        
        # Send images for the predicted crops (long-term prediction)
        image_send_result = None
        try:
            if result.get('monthly_plans') or result.get('rotation_sequence'):
                logger.info(f"Sending images for long-term prediction (parcel: {request.parcel_id})")
                image_send_result = await process_prediction_and_send_images(
                    prediction_result=result,
                    prediction_type="long_term",
                    additional_metadata={
                        "start_month": request.start_month,
                        "diversification_bonus": request.diversification_bonus,
                        "min_profit_threshold": request.min_profit_threshold
                    }
                )
        except Exception as e:
            logger.error(f"Failed to send images for long-term prediction: {str(e)}")
            # Don't fail the entire request if image sending fails
            image_send_result = {"success": False, "error": str(e)}
        
        # Add image sending result to response if available
        if image_send_result:
            result["image_send_result"] = image_send_result
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Annual planning error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Annual planning failed: {str(e)}")

@app.post("/api/v1/plan/annual/all", tags=["Planning"])
async def plan_annual_all_parcels(
    start_month: int = Query(1, ge=1, le=12, description="Starting month"),
    diversification_bonus: float = Query(0.1, ge=0, le=1, description="Diversification bonus factor"),
    min_profit_threshold: float = Query(0.0, description="Minimum profit threshold")
):
    """Generate annual crop rotation plans for all parcels."""
    try:
        results = run_long_term_pipeline_for_all_parcels(
            start_month=start_month,
            diversification_bonus=diversification_bonus,
            min_profit_threshold=min_profit_threshold,
            save_results=False
        )
        
        return {
            "start_month": start_month,
            "results": results,
            "total_parcels": len(results),
            "successful_plans": len([r for r in results if 'error' not in r and r.get('monthly_plans')]),
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Batch planning error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch planning failed: {str(e)}")

# Calculation endpoints
@app.post("/api/v1/calculate/profit", tags=["Calculations"])
async def calculate_crop_profit(request: ProfitCalculationRequest):
    """Calculate profit for a specific crop under given conditions."""
    try:
        from src.io_.loaders import load_crop_by_id
        
        # Get crop information
        crop = load_crop_by_id(request.crop_name)
        if not crop:
            raise HTTPException(status_code=404, detail=f"Crop {request.crop_name} not found")
        
        # Prepare conditions
        weather_conditions = {
            'avg_temp_f': request.weather_conditions.temperature,
            'avg_rainfall_inches': request.weather_conditions.rainfall
        }
        import pandas as pd
        weather_conditions_df = pd.DataFrame([weather_conditions])
        soil_conditions = {'ph': request.soil_ph}
        
        # Calculate profit
        result = calculate_net_profit(
            crop=crop,
            weather_conditions=weather_conditions_df,
            soil_conditions=soil_conditions,
            month=request.month,
            price_per_unit=request.price_override
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profit calculation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Profit calculation failed: {str(e)}")

@app.get("/api/v1/compare/crops/{month}", tags=["Analysis"])
async def compare_crops_for_month(
    month: int = Path(..., ge=1, le=12, description="Month (1-12)"),
    region: str = Query(..., description="Region name"),
    soil_ph: float = Query(6.5, ge=0, le=14, description="Soil pH"),
    min_profit: float = Query(0.0, description="Minimum profit filter")
):
    """Compare all eligible crops for a specific month and conditions."""
    try:
        from src.pipelines.predict_short_term import get_monthly_weather_forecast
        
        # Get eligible crops
        eligible_crops = filter_crops_by_month(month)
        if not eligible_crops:
            return {
                "month": month,
                "region": region,
                "message": "No crops eligible for this month",
                "comparisons": []
            }
        
        # Get weather conditions
        weather_data = get_monthly_weather_forecast(region, month)
        if not weather_data:
            raise HTTPException(status_code=400, detail=f"No weather data available for region {region}")
        
        # Calculate profits for all crops
        comparisons = []
        import pandas as pd
        weather_conditions = {
            'temperature': weather_data['temperature'],
            'rainfall': weather_data['rainfall']
        }
        soil_conditions = {'ph': soil_ph}
        weather_conditions_df = pd.DataFrame([weather_conditions])
        
        for crop in eligible_crops:
            try:
                profit_calc = calculate_net_profit(
                    crop=crop,
                    weather_conditions=weather_conditions_df,
                    soil_conditions=soil_conditions,
                    month=month
                )
                comparisons.append(profit_calc)
            except Exception as e:
                logger.warning(f"Failed to calculate profit for {crop['crop_id']}: {str(e)}")
                continue
        
        # Filter by minimum profit
        profitable_crops = filter_profitable_crops(comparisons, min_profit)
        
        # Rank by profit
        ranked_crops = rank_crops_by_profit(profitable_crops)
        
        # Create summary
        summary = create_recommendation_summary(ranked_crops)
        
        return {
            "month": month,
            "region": region,
            "weather_conditions": weather_data,
            "soil_ph": soil_ph,
            "comparisons": ranked_crops,
            "summary": summary,
            "generated_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Crop comparison error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Crop comparison failed: {str(e)}")

# Utility endpoints
@app.get("/api/v1/summary/system", tags=["Utilities"])
async def get_system_summary():
    """Get system data summary and statistics."""
    try:
        from datetime import datetime
        
        parcels_df = load_parcels()
        crops_df = load_crops()
        fertilizers_df = load_fertilizers()
        prices_df = load_price_history()
        
        return {
            "data_summary": {
                "parcels": {
                    "count": len(parcels_df),
                    "regions": parcels_df['region'].unique().tolist(),
                    "total_acreage": float(parcels_df['acreage'].sum())
                },
                "crops": {
                    "count": len(crops_df),
                    "crop_types": crops_df['crop_name'].unique().tolist()
                },
                "fertilizers": {
                    "count": len(fertilizers_df),
                    "fertilizer_types": fertilizers_df['fertilizer_name'].tolist()
                },
                "price_history": {
                    "records": len(prices_df),
                    "crops_with_prices": prices_df['crop_name'].unique().tolist()
                }
            },
            "api_info": {
                "version": "1.0.0",
                "endpoints": {
                    "predictions": 4,
                    "planning": 2,
                    "data": 6,
                    "analysis": 1
                }
            },
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"System summary error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate system summary: {str(e)}")


# Frontend Integration Endpoints
@app.post("/api/v1/predict/location", response_model=PredictionResults, tags=["Frontend"])
async def predict_for_location(request: UserPredictionRequest):
    """
    Generate top 5 crop-fertilizer combinations for user location and preferences.
    
    This endpoint is designed for frontend integration where users provide their location,
    timezone, and prediction type to receive optimized agricultural recommendations.
    """
    try:
        logger.info(f"Processing location-based prediction for {request.location.latitude}, {request.location.longitude}")
        
        # Process the request and get top 5 combinations
        combinations = process_user_prediction_request(
            location={"latitude": request.location.latitude, "longitude": request.location.longitude},
            timezone=request.timezone,
            prediction_type=request.prediction_type
        )
        
        # Format results for frontend consumption
        results = format_prediction_results(combinations)
        
        # Send images for the predicted crops
        image_send_result = None
        try:
            if combinations:
                logger.info(f"Sending images for location-based prediction (type: {request.prediction_type})")
                # Create a prediction result format for the image service
                prediction_result = {
                    "recommendations": [{"crop_name": combo.get("crop_name")} for combo in combinations],
                    "generated_at": datetime.now().isoformat()
                }
                image_send_result = await process_prediction_and_send_images(
                    prediction_result=prediction_result,
                    prediction_type=request.prediction_type,
                    additional_metadata={
                        "location": {"latitude": request.location.latitude, "longitude": request.location.longitude},
                        "timezone": request.timezone
                    }
                )
        except Exception as e:
            logger.error(f"Failed to send images for location-based prediction: {str(e)}")
            # Don't fail the entire request if image sending fails
            image_send_result = {"success": False, "error": str(e)}
        
        # Create session for individual result access
        session_id = session_manager.create_session(results)
        results['session_id'] = session_id
        
        # Include image sending result if available
        if image_send_result:
            results["image_send_result"] = image_send_result
        
        logger.info(f"Successfully generated {len(combinations)} predictions for location, session: {session_id}")
        return PredictionResults(**results)
        
    except ValueError as ve:
        logger.error(f"Validation error in location prediction: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Location prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate location-based predictions: {str(e)}")


# Individual result endpoints for toggle functionality
@app.get("/api/v1/results/crop/{session_id}/{index}", tags=["Frontend"])
async def get_crop_name(
    session_id: str = Path(..., description="Session ID from prediction request"),
    index: int = Path(..., ge=1, le=5, description="Crop index (1-5)")
):
    """Get individual crop name by session and index."""
    result = session_manager.get_result_by_index(session_id, "cropName", index)
    if result is None:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    return {"cropName": result, "index": index, "session_id": session_id}


@app.get("/api/v1/results/price/{session_id}/{index}", tags=["Frontend"]) 
async def get_crop_price(
    session_id: str = Path(..., description="Session ID from prediction request"),
    index: int = Path(..., ge=1, le=5, description="Crop index (1-5)")
):
    """Get individual crop price by session and index."""
    result = session_manager.get_result_by_index(session_id, "cropPrice", index)
    if result is None:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    return {"cropPrice": result, "index": index, "session_id": session_id}


@app.get("/api/v1/results/fertilizer/{session_id}/{index}", tags=["Frontend"])
async def get_fertilizer_name(
    session_id: str = Path(..., description="Session ID from prediction request"),
    index: int = Path(..., ge=1, le=5, description="Fertilizer index (1-5)")
):
    """Get individual fertilizer name by session and index."""
    result = session_manager.get_result_by_index(session_id, "fertilizerName", index)
    if result is None:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    return {"fertilizerName": result, "index": index, "session_id": session_id}


@app.get("/api/v1/results/fertilizer-price/{session_id}/{index}", tags=["Frontend"])
async def get_fertilizer_price(
    session_id: str = Path(..., description="Session ID from prediction request"),
    index: int = Path(..., ge=1, le=5, description="Fertilizer index (1-5)")
):
    """Get individual fertilizer price by session and index."""
    result = session_manager.get_result_by_index(session_id, "fertilizerPrice", index)
    if result is None:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    return {"fertilizerPrice": result, "index": index, "session_id": session_id}


@app.get("/api/v1/results/image/{session_id}/{index}", tags=["Frontend"])
async def get_crop_image(
    session_id: str = Path(..., description="Session ID from prediction request"),
    index: int = Path(..., ge=1, le=5, description="Image index (1-5)")
):
    """Get individual crop image path by session and index."""
    result = session_manager.get_result_by_index(session_id, "image", index)
    if result is None:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    return {"imagePath": result, "index": index, "session_id": session_id}


# New models for crop advice output
class CropAdviceRequest(BaseModel):
    prediction_type: str = Field(..., pattern="^(short_term|long_term)$", description="Type of prediction")
    parcel_id: str = Field(..., description="Parcel ID for predictions") 
    month: Optional[int] = Field(None, ge=1, le=12, description="Month for short-term predictions")
    start_month: Optional[int] = Field(1, ge=1, le=12, description="Starting month for long-term predictions")

class CropAdviceResponse(BaseModel):
    prediction_type: str
    parcel_id: str
    total_recommendations: int
    crop_advice: Dict[str, Any]
    recommendations: List[Dict[str, Any]]
    generated_at: str


@app.post("/api/v1/output", response_model=CropAdviceResponse, tags=["Output"])
async def generate_crop_output(request: CropAdviceRequest):
    """
    Generate comprehensive crop recommendations with AI-powered advice.
    
    For short-term: Returns 5 crops with AI advice for the specified month
    For long-term: Returns 12 crops with AI advice for annual planning
    """
    try:
        logger.info(f"Generating {request.prediction_type} crop output for parcel {request.parcel_id}")
        
        # Initialize the crop advice wrapper
        advice_wrapper = CropAdviceWrapper()
        
        if request.prediction_type == "short_term":
            if not request.month:
                raise HTTPException(status_code=400, detail="Month is required for short-term predictions")
            
            # Get short-term recommendations
            monthly_request = MonthlyRecommendationRequest(
                parcel_id=request.parcel_id,
                month=request.month,
                top_n=5,
                ranking_method="profit",
                min_confidence=70.0
            )
            
            result = predict_month_recommendations(
                parcel_id=monthly_request.parcel_id,
                month=monthly_request.month,
                top_n=monthly_request.top_n,
                ranking_method=monthly_request.ranking_method,
                min_confidence=monthly_request.min_confidence
            )
            
            # Extract crop names
            crop_names = [rec['crop_name'] for rec in result.get('recommendations', [])]
            
            # Get AI advice for each crop
            crop_advice = advice_wrapper.get_multiple_crop_care(crop_names)
            
            # Format the response
            formatted_advice = {}
            for crop_name, advice in crop_advice.items():
                formatted_advice[crop_name] = advice.model_dump()
            
            return CropAdviceResponse(
                prediction_type=request.prediction_type,
                parcel_id=request.parcel_id,
                total_recommendations=len(crop_names),
                crop_advice=formatted_advice,
                recommendations=result.get('recommendations', []),
                generated_at=datetime.now().isoformat()
            )
            
        else:  # long_term
            # Get long-term recommendations  
            annual_request = AnnualPlanRequest(
                parcel_id=request.parcel_id,
                start_month=request.start_month or 1,
                diversification_bonus=0.1,
                min_profit_threshold=0.0
            )
            
            result = plan_annual_crop_rotation(
                parcel_id=annual_request.parcel_id,
                start_month=annual_request.start_month,
                diversification_bonus=annual_request.diversification_bonus,
                min_profit_threshold=annual_request.min_profit_threshold
            )
            
            # Extract unique crop names from all monthly plans
            all_crops = set()
            monthly_plans = result.get('rotation_sequence', [])
            for month_plan in monthly_plans:
                if 'recommendations' in month_plan:
                    for rec in month_plan['recommendations'][:1]:  # Take top recommendation per month
                        all_crops.add(rec['crop_name'])
            
            crop_names = list(all_crops)[:12]  # Limit to 12 unique crops
            
            # Get AI advice for each crop
            crop_advice = advice_wrapper.get_multiple_crop_care(crop_names)
            
            # Format the response
            formatted_advice = {}
            for crop_name, advice in crop_advice.items():
                formatted_advice[crop_name] = advice.model_dump()
            
            return CropAdviceResponse(
                prediction_type=request.prediction_type,
                parcel_id=request.parcel_id,
                total_recommendations=len(crop_names),
                crop_advice=formatted_advice,
                recommendations=monthly_plans,
                generated_at=datetime.now().isoformat()
            )
            
    except ValueError as ve:
        logger.error(f"Validation error in crop output: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Crop output generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate crop output: {str(e)}")


# Image sending test endpoint
@app.post("/api/v1/test/send-images", tags=["Testing"])
async def test_send_images(
    crop_names: List[str] = Query(..., description="List of crop names to send"),
    prediction_type: str = Query(..., pattern="^(short_term|long_term)$", description="Prediction type")
):
    """Test endpoint for sending crop images to imageSend API."""
    try:
        from src.services.image_service import send_images_to_api
        
        logger.info(f"Testing image sending for {len(crop_names)} crops: {crop_names}")
        
        result = await send_images_to_api(
            crop_names=crop_names,
            prediction_type=prediction_type,
            additional_metadata={
                "test_mode": True,
                "requested_at": datetime.now().isoformat()
            }
        )
        
        return {
            "test_mode": True,
            "requested_crops": crop_names,
            "prediction_type": prediction_type,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Image sending test error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Image sending test failed: {str(e)}")


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Endpoint not found", "timestamp": datetime.now().isoformat()}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal server error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "timestamp": datetime.now().isoformat()}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )
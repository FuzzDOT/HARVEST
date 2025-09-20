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
from datetime import datetime

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
    crop_id: str
    name: str
    growth_window_start: int
    growth_window_end: int
    ideal_temp_min: float
    ideal_temp_max: float
    ideal_rain_min: float
    ideal_rain_max: float
    base_yield_per_acre: float
    cost_per_acre: float

class WeatherConditions(BaseModel):
    temperature: float = Field(..., description="Temperature in Fahrenheit")
    rainfall: float = Field(..., description="Rainfall in inches")
    confidence: Optional[float] = Field(None, description="Forecast confidence percentage")

class ProfitCalculationRequest(BaseModel):
    crop_id: str
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
    crop_id: str
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
        raise HTTPException(status_code=500, detail=f"System health check failed: {str(e)}")

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
@app.post("/api/v1/predict/month", response_model=MonthlyRecommendationResponse, tags=["Predictions"])
async def predict_monthly_recommendations(request: MonthlyRecommendationRequest):
    """Generate crop recommendations for a specific month."""
    try:
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
        
        return result
        
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
        crop = load_crop_by_id(request.crop_id)
        if not crop:
            raise HTTPException(status_code=404, detail=f"Crop {request.crop_id} not found")
        
        # Prepare conditions
        weather_conditions = {
            'temperature': request.weather_conditions.temperature,
            'rainfall': request.weather_conditions.rainfall
        }
        soil_conditions = {'ph': request.soil_ph}
        
        # Calculate profit
        result = calculate_net_profit(
            crop=crop,
            weather_conditions=weather_conditions,
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
        weather_conditions = {
            'temperature': weather_data['temperature'],
            'rainfall': weather_data['rainfall']
        }
        soil_conditions = {'ph': soil_ph}
        
        for crop in eligible_crops:
            try:
                profit_calc = calculate_net_profit(
                    crop=crop,
                    weather_conditions=weather_conditions,
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
        parcels_df = load_parcels()
        crops_df = load_crops()
        fertilizers_df = load_fertilizers()
        prices_df = load_price_history()
        
        return {
            "data_summary": {
                "parcels": {
                    "count": len(parcels_df),
                    "regions": parcels_df['region'].unique().tolist(),
                    "total_acreage": parcels_df['acreage'].sum()
                },
                "crops": {
                    "count": len(crops_df),
                    "crop_types": crops_df['name'].tolist()
                },
                "fertilizers": {
                    "count": len(fertilizers_df),
                    "fertilizer_types": fertilizers_df['name'].tolist()
                },
                "price_history": {
                    "records": len(prices_df),
                    "crops_with_prices": prices_df['crop_id'].unique().tolist()
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
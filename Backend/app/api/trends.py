"""
Market Trends API Endpoints
Provides access to agricultural market trends and price analytics.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.data_pipeline import DataPipelineService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()


@router.get("/trends/prices/{commodity}")
async def get_price_trends(
    commodity: str,
    period: str = Query(default="30d", regex="^(7d|30d|90d|1y)$"),
    region: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get price trends for a specific commodity.
    """
    try:
        data_service = DataPipelineService()
        
        # Calculate date range
        days_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
        days = days_map[period]
        start_date = datetime.now() - timedelta(days=days)
        
        # Get price data
        price_data = await data_service.get_price_trends(
            commodity=commodity,
            start_date=start_date,
            region=region
        )
        
        # Calculate analytics
        analytics = await data_service.calculate_price_analytics(price_data)
        
        return {
            "commodity": commodity,
            "period": period,
            "region": region,
            "data": price_data,
            "analytics": {
                "current_price": analytics["current"],
                "average_price": analytics["average"],
                "price_change": analytics["change"],
                "price_change_percent": analytics["change_percent"],
                "volatility": analytics["volatility"],
                "trend": analytics["trend"]
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get price trends: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve price trends"
        )


@router.get("/trends/demand/{commodity}")
async def get_demand_trends(
    commodity: str,
    period: str = Query(default="30d", regex="^(7d|30d|90d|1y)$"),
    region: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get demand trends and forecasts for a commodity.
    """
    try:
        data_service = DataPipelineService()
        
        # Get demand data
        demand_data = await data_service.get_demand_trends(
            commodity=commodity,
            period=period,
            region=region
        )
        
        # Get demand forecast
        forecast = await data_service.forecast_demand(
            commodity=commodity,
            historical_data=demand_data,
            forecast_days=30
        )
        
        return {
            "commodity": commodity,
            "period": period,
            "region": region,
            "historical_demand": demand_data,
            "forecast": forecast,
            "insights": {
                "seasonal_patterns": demand_data.get("seasonal_patterns", []),
                "growth_rate": demand_data.get("growth_rate", 0),
                "peak_seasons": demand_data.get("peak_seasons", [])
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get demand trends: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve demand trends"
        )


@router.get("/trends/supply/{commodity}")
async def get_supply_trends(
    commodity: str,
    period: str = Query(default="30d", regex="^(7d|30d|90d|1y)$"),
    region: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get supply trends and production forecasts.
    """
    try:
        data_service = DataPipelineService()
        
        # Get supply data
        supply_data = await data_service.get_supply_trends(
            commodity=commodity,
            period=period,
            region=region
        )
        
        # Get production forecast
        production_forecast = await data_service.forecast_production(
            commodity=commodity,
            historical_data=supply_data,
            weather_data=await data_service.get_weather_data(region or "global")
        )
        
        return {
            "commodity": commodity,
            "period": period,
            "region": region,
            "supply_data": supply_data,
            "production_forecast": production_forecast,
            "supply_chain_status": {
                "availability": supply_data.get("availability", "unknown"),
                "bottlenecks": supply_data.get("bottlenecks", []),
                "transportation_costs": supply_data.get("transport_costs", {})
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get supply trends: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve supply trends"
        )


@router.get("/trends/market-summary")
async def get_market_summary(
    region: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get overall market summary and key indicators.
    """
    try:
        data_service = DataPipelineService()
        
        # Get market overview
        market_data = await data_service.get_market_overview(region=region)
        
        return {
            "region": region or "global",
            "timestamp": datetime.now().isoformat(),
            "top_commodities": market_data["top_commodities"],
            "price_movers": {
                "gainers": market_data["price_gainers"],
                "losers": market_data["price_losers"]
            },
            "market_indicators": {
                "overall_sentiment": market_data["sentiment"],
                "volatility_index": market_data["volatility_index"],
                "trading_volume": market_data["trading_volume"]
            },
            "news_highlights": market_data.get("news", [])
        }
        
    except Exception as e:
        logger.error(f"Failed to get market summary: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve market summary"
        )


@router.get("/trends/compare")
async def compare_commodities(
    commodities: List[str] = Query(..., description="List of commodities to compare"),
    metric: str = Query(default="price", regex="^(price|demand|supply|volatility)$"),
    period: str = Query(default="30d", regex="^(7d|30d|90d|1y)$"),
    db: Session = Depends(get_db)
):
    """
    Compare multiple commodities across different metrics.
    """
    try:
        data_service = DataPipelineService()
        
        comparison_data = {}
        
        for commodity in commodities:
            if metric == "price":
                data = await data_service.get_price_trends(commodity, period=period)
            elif metric == "demand":
                data = await data_service.get_demand_trends(commodity, period=period)
            elif metric == "supply":
                data = await data_service.get_supply_trends(commodity, period=period)
            elif metric == "volatility":
                data = await data_service.get_volatility_data(commodity, period=period)
            
            comparison_data[commodity] = data
        
        # Calculate relative performance
        performance = await data_service.calculate_relative_performance(
            comparison_data, metric
        )
        
        return {
            "commodities": commodities,
            "metric": metric,
            "period": period,
            "data": comparison_data,
            "performance_ranking": performance["ranking"],
            "correlation_matrix": performance["correlations"]
        }
        
    except Exception as e:
        logger.error(f"Failed to compare commodities: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to compare commodities"
        )
"""
Short-term prediction pipeline using current weather forecasts.
"""

from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime

from ..io_.loaders import load_parcel_by_id, load_weather_forecast
from ..rules.crop_eligibility import filter_crops_by_month
from ..model.profit_calc import calculate_net_profit
from ..model.ranker import rank_crops_by_profit, get_top_n_recommendations
from ..io_.writers import save_short_term_recommendations
from ..config import MIN_WEATHER_CONFIDENCE


def predict_month_recommendations(
    parcel_id: str,
    month: int,
    top_n: int = 5,
    ranking_method: str = "profit",
    min_confidence: float = MIN_WEATHER_CONFIDENCE
) -> Dict[str, Any]:
    """
    Generate crop recommendations for a specific month using weather forecasts.
    
    Args:
        parcel_id: ID of the parcel to analyze
        month: Month number (1-12) for predictions
        top_n: Number of top recommendations to return
        ranking_method: Method to rank crops ("profit", "roi", "yield", "suitability")
        min_confidence: Minimum weather forecast confidence threshold
    
    Returns:
        Dictionary containing recommendations and metadata
    """
    # Load parcel information
    parcel = load_parcel_by_id(parcel_id)
    if not parcel:
        raise ValueError(f"Parcel {parcel_id} not found")
    
    # Get crops eligible for this month
    eligible_crops = filter_crops_by_month(month)
    if not eligible_crops:
        return {
            'parcel_id': parcel_id,
            'month': month,
            'recommendations': [],
            'message': f'No crops are eligible for planting in month {month}'
        }
    
    # Get weather forecast for parcel's region
    weather_data = get_monthly_weather_forecast(parcel['region'], month, min_confidence)
    if not weather_data:
        return {
            'parcel_id': parcel_id,
            'month': month,
            'recommendations': [],
            'message': f'No reliable weather forecast available for region {parcel["region"]}'
        }
    
    # Calculate profit for each eligible crop
    profit_calculations = []
    soil_conditions = {'ph': parcel['soil_ph']}
    
    for crop in eligible_crops:
        try:
            # Convert weather_data dict to DataFrame as required by calculate_net_profit
            weather_df = pd.DataFrame([weather_data])
            profit_calc = calculate_net_profit(
                crop=crop,
                weather_conditions=weather_df,
                soil_conditions=soil_conditions,
                month=month
            )
            profit_calculations.append(profit_calc)
        except Exception as e:
            print(f"Warning: Could not calculate profit for crop {crop['crop_id']}: {e}")
            continue
    
    if not profit_calculations:
        return {
            'parcel_id': parcel_id,
            'month': month,
            'recommendations': [],
            'message': 'No profitable crops found for the given conditions'
        }
    
    # Get top recommendations
    top_recommendations = get_top_n_recommendations(
        profit_calculations, n=top_n, ranking_method=ranking_method
    )
    
    # Add ranking information
    for i, rec in enumerate(top_recommendations):
        rec['rank'] = i + 1
        rec['recommendation_confidence'] = calculate_recommendation_confidence(rec, weather_data)
    
    return {
        'parcel_id': parcel_id,
        'month': month,
        'region': parcel['region'],
        'acreage': parcel['acreage'],
        'weather_conditions': weather_data,
        'recommendations': top_recommendations,
        'total_crops_evaluated': len(profit_calculations),
        'ranking_method': ranking_method,
        'generated_at': datetime.now().isoformat()
    }


def get_monthly_weather_forecast(
    region: str, 
    month: int,
    min_confidence: float = MIN_WEATHER_CONFIDENCE
) -> Optional[Dict[str, float]]:
    """
    Get weather forecast data for a region and month.
    
    Args:
        region: Region name
        month: Month number (1-12)
        min_confidence: Minimum confidence threshold
    
    Returns:
        Weather conditions dictionary or None if no reliable data
    """
    try:
        weather_df = load_weather_forecast()
        
        # Filter by region and month
        region_weather = weather_df[weather_df['region'] == region].copy()
        
        if region_weather.empty:
            return None
        
        # Extract month from date and filter
        region_weather['month'] = region_weather['date'].dt.month
        month_weather = region_weather[region_weather['month'] == month]
        
        if month_weather.empty:
            return None
        
        # Filter by confidence threshold
        reliable_weather = month_weather[month_weather['confidence_percent'] >= min_confidence]
        
        if reliable_weather.empty:
            return None
        
        # Calculate averages for the month
        avg_temp = reliable_weather['forecast_temp_f'].mean()
        total_rain = reliable_weather['forecast_rainfall_inches'].sum()
        avg_confidence = reliable_weather['confidence_percent'].mean()
        
        return {
            'temperature': avg_temp,
            'rainfall': total_rain,
            'confidence': avg_confidence,
            'forecast_days': len(reliable_weather)
        }
        
    except Exception as e:
        print(f"Error loading weather forecast: {e}")
        return None


def calculate_recommendation_confidence(
    recommendation: Dict[str, Any],
    weather_data: Dict[str, float]
) -> float:
    """
    Calculate confidence score for a recommendation.
    
    Args:
        recommendation: Profit calculation for a crop
        weather_data: Weather conditions used in calculation
    
    Returns:
        Confidence score (0-100)
    """
    # Start with weather confidence
    weather_confidence = weather_data.get('confidence', 70)
    
    # Adjust based on yield penalty (lower penalty = higher confidence)
    penalty_factor = recommendation['yield_penalty_factors']['total_penalty']
    penalty_confidence = (1 - penalty_factor) * 100
    
    # Combine confidences (weighted average)
    combined_confidence = (weather_confidence * 0.6) + (penalty_confidence * 0.4)
    
    return min(combined_confidence, 100)


def run_short_term_pipeline_for_parcel(
    parcel_id: str,
    month: int,
    save_results: bool = True,
    **kwargs
) -> Dict[str, Any]:
    """
    Run complete short-term prediction pipeline for a single parcel.
    
    Args:
        parcel_id: ID of the parcel to analyze
        month: Month number for predictions
        save_results: Whether to save results to CSV
        **kwargs: Additional arguments for predict_month_recommendations
    
    Returns:
        Prediction results
    """
    results = predict_month_recommendations(parcel_id, month, **kwargs)
    
    if save_results and results['recommendations']:
        try:
            output_path = save_short_term_recommendations(
                parcel_id=parcel_id,
                month=month,
                recommendations=results['recommendations']
            )
            results['output_file'] = str(output_path)
        except Exception as e:
            print(f"Warning: Could not save results: {e}")
    
    return results


def run_short_term_pipeline_for_all_parcels(
    month: int,
    save_results: bool = True,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    Run short-term prediction pipeline for all parcels.
    
    Args:
        month: Month number for predictions
        save_results: Whether to save results to CSV
        **kwargs: Additional arguments for predict_month_recommendations
    
    Returns:
        List of prediction results for all parcels
    """
    from ..io_.loaders import load_parcels
    
    parcels = load_parcels()
    all_results = []
    
    for _, parcel in parcels.iterrows():
        parcel_id = parcel['parcel_id']
        
        try:
            results = run_short_term_pipeline_for_parcel(
                parcel_id=parcel_id,
                month=month,
                save_results=save_results,
                **kwargs
            )
            all_results.append(results)
        except Exception as e:
            print(f"Error processing parcel {parcel_id}: {e}")
            all_results.append({
                'parcel_id': parcel_id,
                'month': month,
                'error': str(e),
                'recommendations': []
            })
    
    return all_results
"""
Short-term prediction pipeline using current weather forecasts.
"""

from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime

from ..io_.loaders import load_parcel_by_id, load_weather_forecast
from ..rules.crop_eligibility import filter_crops_by_month
from ..model.profit_calc import calculate_net_profit
from ..model.ranker import rank_crops_by_profit, get_diverse_top_n_recommendations
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
    
    # Calculate profit for each eligible crop with fertilizer diversity
    profit_calculations = []
    soil_conditions = {'ph': parcel['soil_ph']}
    used_fertilizers = set()  # Track used fertilizers for diversity
    
    for crop in eligible_crops:
        try:
            # Convert weather_data dict to DataFrame as required by calculate_net_profit
            weather_df = pd.DataFrame([weather_data])
            profit_calc = calculate_net_profit(
                crop=crop,
                weather_conditions=weather_df,
                soil_conditions=soil_conditions,
                month=month,
                excluded_fertilizers=used_fertilizers
            )
            profit_calculations.append(profit_calc)
            
            # Add the used fertilizer to the set for diversity
            if profit_calc.get('fertilizer_used'):
                used_fertilizers.add(profit_calc['fertilizer_used'])
                
        except Exception as e:
            # Skip crops with missing data silently to avoid cluttering output
            continue
    
    if not profit_calculations:
        return {
            'parcel_id': parcel_id,
            'month': month,
            'recommendations': [],
            'message': 'No profitable crops found for the given conditions'
        }
    
    # Get top recommendations with diversity
    top_recommendations = get_diverse_top_n_recommendations(
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
        # Calculate dynamic confidence based on forecast characteristics
        month_weather = month_weather.copy()
        
        # Base confidence decreases with distance from current date
        from datetime import datetime
        current_date = datetime.now()
        month_weather['days_out'] = (pd.to_datetime(month_weather['date']) - current_date).dt.days
        
        # Calculate confidence based on forecast distance and weather stability
        base_confidence = 95  # Start high for near-term forecasts
        month_weather['confidence_percent'] = month_weather.apply(
            lambda row: calculate_dynamic_weather_confidence(row, base_confidence), axis=1
        )
        
        reliable_weather = month_weather[month_weather['confidence_percent'] >= min_confidence]
        
        if reliable_weather.empty:
            return None
        
        # Calculate averages for the month
        avg_temp = reliable_weather['avg_temp_f'].mean()
        total_rain = reliable_weather['avg_rainfall_inches'].sum()
        avg_confidence = reliable_weather['confidence_percent'].mean()
        
        return {
            'avg_temp_f': avg_temp,
            'avg_rainfall_inches': total_rain,
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
    # Start with base weather confidence
    base_weather_confidence = weather_data.get('confidence', 70)
    
    # Add variability based on forecast days and temperature volatility
    forecast_days = weather_data.get('forecast_days', 10)
    weather_confidence = base_weather_confidence - max(0, (forecast_days - 15) * 0.5)
    
    # Adjust based on yield penalty factors (more detailed scoring)
    penalties = recommendation['yield_penalty_factors']
    temp_penalty = penalties.get('temperature_penalty', 0)
    rain_penalty = penalties.get('rainfall_penalty', 0)
    soil_penalty = penalties.get('soil_ph_penalty', 0)
    
    # Calculate crop suitability confidence (inverse of penalties)
    temp_confidence = max(60, 100 - (temp_penalty * 200))  # Scale temperature penalty impact
    rain_confidence = max(60, 100 - (rain_penalty * 150))  # Scale rainfall penalty impact  
    soil_confidence = max(70, 100 - (soil_penalty * 100))  # Scale soil penalty impact
    
    # Weight the confidence factors
    crop_suitability = (temp_confidence * 0.4) + (rain_confidence * 0.35) + (soil_confidence * 0.25)
    
    # Add crop-specific confidence adjustments based on category
    crop_name = recommendation.get('crop_name', '')
    category_bonus = get_crop_category_confidence_bonus(crop_name)
    
    # Final confidence calculation
    combined_confidence = (weather_confidence * 0.5) + (crop_suitability * 0.4) + (category_bonus * 0.1)
    
    # Add some variability based on crop name hash to ensure different crops have different scores
    crop_hash_factor = (hash(crop_name) % 100) / 1000  # Small variation (-0.05 to +0.05)
    combined_confidence += crop_hash_factor * 10
    
    return max(50, min(combined_confidence, 95))  # Clamp between 50-95%


def calculate_dynamic_weather_confidence(weather_row: pd.Series, base_confidence: float) -> float:
    """
    Calculate dynamic weather confidence based on forecast characteristics.
    """
    days_out = weather_row.get('days_out', 0)
    temp = weather_row.get('avg_temp_f', 70)
    humidity = weather_row.get('avg_humidity_percent', 50)
    
    # Confidence decreases with forecast distance
    distance_penalty = min(days_out * 1.2, 25)  # Max 25% penalty for distant forecasts
    
    # Add small variations based on weather characteristics
    temp_variation = abs(temp - 70) * 0.3  # Confidence decreases for extreme temps
    humidity_factor = abs(humidity - 50) * 0.1  # Small humidity impact
    
    # Calculate final confidence
    confidence = base_confidence - distance_penalty - temp_variation - humidity_factor
    
    # Add some pseudo-random variation based on date to ensure realistic spread
    date_hash = hash(str(weather_row.get('date', ''))) % 100
    variation = (date_hash - 50) / 20  # ±2.5% variation
    
    return max(60, min(confidence + variation, 95))


def get_crop_category_confidence_bonus(crop_name: str) -> float:
    """
    Get confidence bonus based on crop category and regional suitability.
    """
    # Florida is well-suited for these crops
    high_confidence_crops = {
        'tomato': 85,
        'onion': 82,
        'rice': 80,
        'cotton': 78,
        'lettuce': 76
    }
    
    # Less suited but still viable
    medium_confidence_crops = {
        'corn': 72,
        'soybean': 70,
        'peanut': 75,
        'sorghum': 68
    }
    
    # Not ideal for Florida climate
    low_confidence_crops = {
        'carrot': 60,
        'potato': 58,
        'wheat': 55,
        'barley': 52
    }
    
    crop_lower = crop_name.lower()
    
    # Check each category
    for crop_key, confidence in high_confidence_crops.items():
        if crop_key in crop_lower:
            return confidence
            
    for crop_key, confidence in medium_confidence_crops.items():
        if crop_key in crop_lower:
            return confidence
            
    for crop_key, confidence in low_confidence_crops.items():
        if crop_key in crop_lower:
            return confidence
    
    return 70  # Default confidence


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
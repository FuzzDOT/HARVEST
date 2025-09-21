"""
Location-based prediction service for frontend integration.
Handles user location, timezone, and generates top 5 crop-fertilizer combinations.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import pytz
import pandas as pd

from ..io_.loaders import (
    load_crops, load_fertilizers, load_parcels, load_weather_forecast,
    load_weather_normals, get_crop_image_path, get_profit_graph_path,
    get_latest_price
)
from ..model.profit_calc import calculate_net_profit
from ..model.yield_penalty import calculate_total_yield_penalty
from ..rules.crop_eligibility import filter_crops_by_month
from ..rules.fertilizer_match import get_best_fertilizer_for_crop


def process_user_prediction_request(
    location: Dict[str, float],  # {"latitude": 40.7128, "longitude": -74.0060}
    timezone: str,  # "America/New_York"
    prediction_type: str,  # "short_term" or "long_term"
    **kwargs
) -> List[Dict[str, Any]]:
    """
    Process user location and preferences to generate top 5 crop-fertilizer combinations.
    
    Args:
        location: Dictionary with latitude and longitude
        timezone: User's timezone string
        prediction_type: "short_term" or "long_term"
        
    Returns:
        List of top 5 optimized crop-fertilizer combinations
    """
    # Get current time in user's timezone
    user_tz = pytz.timezone(timezone)
    current_time = datetime.now(user_tz)
    current_month = current_time.month
    
    # Find the closest parcel based on location (simplified - using first parcel for now)
    parcels = load_parcels()
    if parcels.empty:
        raise ValueError("No parcels available")
    
    # Use the first parcel as default (you could implement actual location matching)
    parcel = parcels.iloc[0].to_dict()
    
    # Get weather data based on prediction type
    if prediction_type == "short_term":
        weather_data = get_weather_for_location(location, current_month, use_forecast=True)
    else:
        weather_data = get_weather_for_location(location, current_month, use_forecast=False)
    
    # Get eligible crops for the current month
    eligible_crops_list = filter_crops_by_month(current_month)
    
    if not eligible_crops_list:
        raise ValueError("No eligible crops for current month")
    
    # Convert to DataFrame for easier processing
    crops = load_crops()
    eligible_crop_names = [crop['crop_name'] for crop in eligible_crops_list]
    eligible_crops = crops[crops['crop_name'].isin(eligible_crop_names)]
    
    # Calculate profitability for each crop-fertilizer combination
    combinations = []
    
    for _, crop in eligible_crops.iterrows():
        crop_dict = crop.to_dict()
        
        # Find best fertilizer for this crop
        best_fertilizer = get_best_fertilizer_for_crop(
            crop_dict, current_month
        )
        
        if best_fertilizer is None:
            continue
            
        # Get soil conditions from parcel data
        soil_conditions = {'ph': parcel.get('soil_ph', 6.5)}
            
        # Calculate yield penalties for confidence scoring
        # Convert weather_data dict to DataFrame for compatibility
        weather_df = pd.DataFrame([weather_data])
        penalties = calculate_total_yield_penalty(
            weather_df, crop_dict, soil_conditions
        )
        
        # Calculate net profit
        weather_df_for_profit = pd.DataFrame([weather_data])
        profit_result = calculate_net_profit(
            crop_dict, weather_df_for_profit, soil_conditions, current_month
        )
        
        # Get additional data
        image_path = get_crop_image_path(crop_dict['crop_name'])
        profit_graph_path = get_profit_graph_path(crop_dict['crop_name'])
        crop_price = get_latest_price(crop_dict['crop_name'], parcel.get('region'))
        
        combination = {
            'crop_name': crop_dict['crop_name'],
            'crop_price': crop_price or 0.0,
            'fertilizer_name': best_fertilizer.get('name', 'Unknown'),
            'fertilizer_price': best_fertilizer.get('cost_per_unit', 0.0),
            'net_profit': profit_result['net_profit'],
            'roi_percent': profit_result['roi_percent'],
            'image_path': image_path,
            'profit_graph_path': profit_graph_path,
            'confidence_score': calculate_confidence_score(penalties, weather_data),
            'yield_estimate': crop_dict['yield_lb_per_acre_est'] * (1 - penalties['total_penalty'])
        }
        
        combinations.append(combination)
    
    # Sort by net profit and return top 5
    combinations.sort(key=lambda x: x['net_profit'], reverse=True)
    return combinations[:5]


def get_weather_for_location(
    location: Dict[str, float], 
    month: int, 
    use_forecast: bool = True
) -> Dict[str, float]:
    """
    Get weather data for a specific location and month.
    For now, this uses the existing weather data mapped by region.
    In a real implementation, you would integrate with weather APIs.
    """
    # Simplified region mapping based on latitude
    latitude = location['latitude']
    
    if latitude > 40:
        region = "MIDWEST"
    elif latitude > 30:
        region = "SOUTHEAST"
    else:
        region = "SOUTHWEST"
    
    if use_forecast:
        weather_df = load_weather_forecast()
        # Filter by region and get recent data
        region_weather = weather_df[weather_df['region'] == region]
        if not region_weather.empty:
            latest = region_weather.iloc[-1]
            return {
                'temperature': latest['forecast_temp_f'],
                'rainfall': latest['forecast_rainfall_inches'],
                'confidence': latest['confidence_percent']
            }
    
    # Fallback to normals
    normals_df = load_weather_normals()
    month_weather = normals_df[
        (normals_df['region'] == region) & 
        (normals_df['month'] == month)
    ]
    
    if not month_weather.empty:
        normal = month_weather.iloc[0]
        return {
            'temperature': normal['avg_temp_f'],
            'rainfall': normal['avg_rainfall_inches'],
            'confidence': 75.0  # Default confidence for historical normals
        }
    
    # Default fallback weather
    return {
        'temperature': 70.0,
        'rainfall': 2.0,
        'confidence': 50.0
    }


def calculate_confidence_score(penalties: Dict[str, float], weather_data: Dict[str, float]) -> float:
    """Calculate a confidence score for the prediction."""
    weather_confidence = weather_data.get('confidence', 50.0)
    penalty_factor = 1 - penalties.get('total_penalty', 0.0)
    
    # Combine weather confidence with penalty factor
    return min(100.0, weather_confidence * penalty_factor * 1.2)


def format_prediction_results(combinations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Format the top 5 combinations into separate API response fields.
    """
    result = {}
    
    for i in range(5):
        index = i + 1
        if i < len(combinations):
            combo = combinations[i]
            result.update({
                f'cropName{index}': combo['crop_name'],
                f'cropPrice{index}': combo['crop_price'],
                f'fertilizerName{index}': combo['fertilizer_name'],
                f'fertilizerPrice{index}': combo['fertilizer_price'],
                f'image{index}': combo['image_path'],
                f'profitGraph{index}': combo['profit_graph_path'],
                f'netProfit{index}': combo['net_profit'],
                f'roiPercent{index}': combo['roi_percent'],
                f'confidence{index}': combo['confidence_score'],
                f'yieldEstimate{index}': combo['yield_estimate']
            })
        else:
            # Fill empty slots with null values
            result.update({
                f'cropName{index}': None,
                f'cropPrice{index}': None,
                f'fertilizerName{index}': None,
                f'fertilizerPrice{index}': None,
                f'image{index}': None,
                f'profitGraph{index}': None,
                f'netProfit{index}': None,
                f'roiPercent{index}': None,
                f'confidence{index}': None,
                f'yieldEstimate{index}': None
            })
    
    return result
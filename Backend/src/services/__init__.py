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
from ..rules.crop_eligibility import filter_crops_by_month, filter_crops_by_month_and_region
from ..rules.fertilizer_match import get_best_fertilizer_for_crop
from ..utils.dates import get_month_name


def determine_region_from_location(location: Dict[str, float]) -> Optional[str]:
    """
    Determine region/state code from latitude/longitude coordinates.
    Simplified mapping for demo purposes.
    """
    latitude = location['latitude']
    longitude = location['longitude']
    
    # Very simplified US region mapping based on coordinates
    # In production, this would use a proper geographic lookup service
    if latitude > 45:
        return "AK"  # Alaska region
    elif latitude > 40:
        if longitude > -100:
            return "IL"  # Midwest region
        else:
            return "WA"  # Pacific Northwest
    elif latitude > 35:
        if longitude > -100:
            return "VA"  # Mid-Atlantic
        else:
            return "CA"  # California
    elif latitude > 30:
        if longitude > -100:
            return "FL"  # Southeast
        else:
            return "AZ"  # Southwest
    else:
        return "TX"  # South


def create_no_crops_available_response(reason: str = "unsuitable growing conditions") -> Dict[str, Any]:
    """
    Create a constant response when no crops are available due to environmental conditions.
    
    Args:
        reason: Reason why no crops are available
        
    Returns:
        Standardized "no crops available" response
    """
    return {
        'cropName1': 'No crops available',
        'cropPrice1': 0.0,
        'fertilizerName1': 'N/A',
        'fertilizerPrice1': 0.0,
        'image1': '/static/images/no_crops.png',
        'profitGraph1': None,
        'netProfit1': 0.0,
        'roiPercent1': 0.0,
        'confidence1': 100.0,  # High confidence in the "no crops" determination
        'yieldEstimate1': 0.0,
        
        'cropName2': f'Reason: {reason}',
        'cropPrice2': 0.0,
        'fertilizerName2': 'N/A',
        'fertilizerPrice2': 0.0,
        'image2': '/static/images/weather_warning.png',
        'profitGraph2': None,
        'netProfit2': 0.0,
        'roiPercent2': 0.0,
        'confidence2': 100.0,
        'yieldEstimate2': 0.0,
        
        # Empty slots for remaining positions
        'cropName3': None,
        'cropPrice3': None,
        'fertilizerName3': None,
        'fertilizerPrice3': None,
        'image3': None,
        'profitGraph3': None,
        'netProfit3': None,
        'roiPercent3': None,
        'confidence3': None,
        'yieldEstimate3': None,
        
        'cropName4': None,
        'cropPrice4': None,
        'fertilizerName4': None,
        'fertilizerPrice4': None,
        'image4': None,
        'profitGraph4': None,
        'netProfit4': None,
        'roiPercent4': None,
        'confidence4': None,
        'yieldEstimate4': None,
        
        'cropName5': None,
        'cropPrice5': None,
        'fertilizerName5': None,
        'fertilizerPrice5': None,
        'image5': None,
        'profitGraph5': None,
        'netProfit5': None,
        'roiPercent5': None,
        'confidence5': None,
        'yieldEstimate5': None,
    }


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
    
    # Get eligible crops for the current month and region
    region_code = determine_region_from_location(location)
    if region_code:
        eligible_crops_list = filter_crops_by_month_and_region(current_month, region_code)
    else:
        eligible_crops_list = filter_crops_by_month(current_month)
    
    # If no crops are eligible for this month/region, return constant response
    if not eligible_crops_list:
        no_crops_response = create_no_crops_available_response(
            f"No crops can be grown in {get_month_name(current_month)} for your location due to current growing conditions"
        )
        return [no_crops_response]  # Return as list with single "combination" for consistency
    
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
                'temperature': latest['avg_temp_f'],
                'rainfall': latest['avg_rainfall_inches'],
                'confidence': latest.get('confidence_percent', 85)  # Default confidence if not available
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
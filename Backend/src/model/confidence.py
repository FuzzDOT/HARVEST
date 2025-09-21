"""
Confidence calculation utilities for crop recommendations.
"""

from typing import Dict, Any, Optional
import pandas as pd


def calculate_recommendation_confidence(
    crop_data: Dict[str, Any],
    weather_data: Dict[str, Any],
    soil_data: Dict[str, Any],
    prediction_type: str = "short_term"
) -> float:
    """
    Calculate confidence score for a crop recommendation.
    
    Args:
        crop_data: Crop information and profit calculations
        weather_data: Weather conditions and forecast data
        soil_data: Soil conditions for the parcel
        prediction_type: "short_term" or "long_term"
    
    Returns:
        Confidence score (0-100)
    """
    # 1. Weather Confidence Component (40% weight)
    weather_confidence = calculate_weather_confidence(weather_data, prediction_type)
    
    # 2. Crop Suitability Confidence (35% weight)
    suitability_confidence = calculate_crop_suitability_confidence(crop_data, soil_data)
    
    # 3. Data Quality Confidence (15% weight)
    data_confidence = calculate_data_quality_confidence(crop_data, weather_data)
    
    # 4. Regional Adaptation Confidence (10% weight)
    regional_confidence = calculate_regional_adaptation_confidence(crop_data, weather_data)
    
    # Weighted combination
    total_confidence = (
        weather_confidence * 0.40 +
        suitability_confidence * 0.35 +
        data_confidence * 0.15 +
        regional_confidence * 0.10
    )
    
    # Clamp to reasonable range and add small variation
    return max(45, min(total_confidence, 95))


def calculate_weather_confidence(
    weather_data: Dict[str, Any],
    prediction_type: str
) -> float:
    """
    Calculate confidence based on weather data quality and forecast reliability.
    """
    if prediction_type == "short_term":
        # For short-term: base on forecast confidence and distance
        base_confidence = weather_data.get('confidence', 70)
        forecast_days = weather_data.get('forecast_days', 10)
        
        # Confidence decreases with forecast distance
        distance_penalty = min(forecast_days * 1.5, 30)
        confidence = base_confidence - distance_penalty
        
        # Add weather stability factor
        temp = weather_data.get('temperature', 70)
        rainfall = weather_data.get('rainfall', 1)
        
        # Penalize extreme conditions slightly
        extreme_temp_penalty = max(0, abs(temp - 70) - 20) * 0.5
        extreme_rain_penalty = max(0, rainfall - 5) * 2
        
        return max(50, confidence - extreme_temp_penalty - extreme_rain_penalty)
    
    else:  # long_term
        # For long-term: historical normals are more reliable but less precise
        temp = weather_data.get('avg_temp_f', 70)
        rainfall = weather_data.get('avg_rainfall_inches', 2)
        
        # Base confidence for historical normals
        base_confidence = 78
        
        # Adjust for seasonal variability (spring/fall less predictable)
        # This would ideally use the month, but we'll estimate from temperature
        if 40 <= temp <= 50 or 75 <= temp <= 85:  # Transition seasons
            seasonal_penalty = 5
        else:
            seasonal_penalty = 0
            
        # Adjust for extreme conditions
        extreme_penalty = max(0, abs(temp - 65) - 25) * 0.3
        drought_penalty = max(0, 3 - rainfall) * 2
        flood_penalty = max(0, rainfall - 8) * 1.5
        
        return max(55, base_confidence - seasonal_penalty - extreme_penalty - drought_penalty - flood_penalty)


def calculate_crop_suitability_confidence(
    crop_data: Dict[str, Any],
    soil_data: Dict[str, Any]
) -> float:
    """
    Calculate confidence based on how well-suited the crop is for the conditions.
    """
    # Get yield penalty factors
    penalty_factors = crop_data.get('yield_penalty_factors', {})
    
    # Convert penalties to confidence scores
    temp_penalty = penalty_factors.get('temperature_penalty', 0)
    rain_penalty = penalty_factors.get('rainfall_penalty', 0)
    soil_penalty = penalty_factors.get('soil_ph_penalty', 0)
    
    # Higher penalties = lower confidence
    temp_confidence = max(40, 100 - (temp_penalty * 150))
    rain_confidence = max(40, 100 - (rain_penalty * 120))
    soil_confidence = max(50, 100 - (soil_penalty * 80))
    
    # Weighted average of suitability factors
    suitability = (temp_confidence * 0.4 + rain_confidence * 0.4 + soil_confidence * 0.2)
    
    # Bonus for high-performing crops (good ROI)
    roi = crop_data.get('roi_percent', 0)
    if roi > 300:
        roi_bonus = 5
    elif roi > 150:
        roi_bonus = 3
    elif roi > 50:
        roi_bonus = 1
    else:
        roi_bonus = -2  # Penalty for low ROI crops
    
    return max(35, min(suitability + roi_bonus, 95))


def calculate_data_quality_confidence(
    crop_data: Dict[str, Any],
    weather_data: Dict[str, Any]
) -> float:
    """
    Calculate confidence based on data completeness and quality.
    """
    confidence = 85  # Base data quality score
    
    # Check for missing crop data
    required_crop_fields = ['yield_lb_per_acre_est', 'price_usd_per_lb_est', 'category']
    missing_crop_data = sum(1 for field in required_crop_fields if not crop_data.get(field))
    confidence -= missing_crop_data * 5
    
    # Check for missing weather data
    if weather_data.get('temperature') is None:
        confidence -= 10
    if weather_data.get('rainfall') is None:
        confidence -= 8
    
    # Check yield estimate quality (very high or very low yields might be unreliable)
    base_yield = crop_data.get('base_yield', 0)
    if base_yield > 50000 or base_yield < 500:  # Extreme yields
        confidence -= 5
    
    return max(60, confidence)


def calculate_regional_adaptation_confidence(
    crop_data: Dict[str, Any],
    weather_data: Dict[str, Any]
) -> float:
    """
    Calculate confidence based on how well the crop is adapted to the region.
    """
    crop_name = crop_data.get('crop_name', '').lower()
    temp = weather_data.get('temperature', weather_data.get('avg_temp_f', 70))
    
    # Regional adaptation scores based on typical growing regions
    if temp >= 75:  # Hot regions (South)
        hot_region_crops = {
            'rice': 90, 'cotton': 88, 'peanut': 85, 'sorghum': 83,
            'tomato': 80, 'onion': 78, 'sweet potato': 85
        }
        base_confidence = 75
        for crop_key, confidence in hot_region_crops.items():
            if crop_key in crop_name:
                return confidence
                
    elif temp >= 60:  # Moderate regions (Midwest)
        moderate_region_crops = {
            'corn': 90, 'soybean': 88, 'wheat': 85, 'potato': 82,
            'tomato': 80, 'onion': 78
        }
        base_confidence = 80
        for crop_key, confidence in moderate_region_crops.items():
            if crop_key in crop_name:
                return confidence
                
    else:  # Cool regions (North)
        cool_region_crops = {
            'wheat': 85, 'barley': 82, 'potato': 88, 'carrot': 80,
            'lettuce': 83
        }
        base_confidence = 70
        for crop_key, confidence in cool_region_crops.items():
            if crop_key in crop_name:
                return confidence
    
    return base_confidence


def get_confidence_level_description(confidence: float) -> str:
    """
    Get a descriptive label for the confidence level.
    
    Args:
        confidence: Confidence score (0-100)
    
    Returns:
        Descriptive string
    """
    if confidence >= 85:
        return "Very High"
    elif confidence >= 75:
        return "High"
    elif confidence >= 65:
        return "Moderate"
    elif confidence >= 55:
        return "Low"
    else:
        return "Very Low"
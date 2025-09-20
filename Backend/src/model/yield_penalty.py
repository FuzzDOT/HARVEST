"""
Yield penalty calculations based on weather and soil deviations from ideal conditions.
"""

from typing import Dict, Any
from ..config import (
    TEMP_PENALTY_FACTOR, RAIN_PENALTY_FACTOR, SOIL_PH_PENALTY_FACTOR,
    MAX_TEMP_PENALTY, MAX_RAIN_PENALTY,
    IDEAL_SOIL_PH_MIN, IDEAL_SOIL_PH_MAX
)


def calculate_temperature_penalty(
    actual_temp: float,
    ideal_temp_min: float,
    ideal_temp_max: float
) -> float:
    """
    Calculate yield penalty factor based on temperature deviation from ideal range.
    
    Args:
        actual_temp: Actual temperature (°F)
        ideal_temp_min: Minimum ideal temperature for crop (°F)
        ideal_temp_max: Maximum ideal temperature for crop (°F)
    
    Returns:
        Penalty factor (0.0 = no penalty, 1.0 = total yield loss)
    """
    if ideal_temp_min <= actual_temp <= ideal_temp_max:
        return 0.0  # No penalty within ideal range
    
    # Calculate deviation from nearest boundary
    if actual_temp < ideal_temp_min:
        deviation = ideal_temp_min - actual_temp
    else:
        deviation = actual_temp - ideal_temp_max
    
    # Calculate penalty based on deviation
    penalty = deviation * TEMP_PENALTY_FACTOR
    
    # Cap penalty at maximum
    return min(penalty, MAX_TEMP_PENALTY)


def calculate_rainfall_penalty(
    actual_rain: float,
    ideal_rain_min: float,
    ideal_rain_max: float
) -> float:
    """
    Calculate yield penalty factor based on rainfall deviation from ideal range.
    
    Args:
        actual_rain: Actual rainfall (inches)
        ideal_rain_min: Minimum ideal rainfall for crop (inches)
        ideal_rain_max: Maximum ideal rainfall for crop (inches)
    
    Returns:
        Penalty factor (0.0 = no penalty, 1.0 = total yield loss)
    """
    if ideal_rain_min <= actual_rain <= ideal_rain_max:
        return 0.0  # No penalty within ideal range
    
    # Calculate deviation from nearest boundary
    if actual_rain < ideal_rain_min:
        deviation = ideal_rain_min - actual_rain
    else:
        deviation = actual_rain - ideal_rain_max
    
    # Calculate penalty based on deviation
    penalty = deviation * RAIN_PENALTY_FACTOR
    
    # Cap penalty at maximum
    return min(penalty, MAX_RAIN_PENALTY)


def calculate_soil_ph_penalty(actual_ph: float) -> float:
    """
    Calculate yield penalty factor based on soil pH deviation from ideal range.
    
    Args:
        actual_ph: Actual soil pH
    
    Returns:
        Penalty factor (0.0 = no penalty, higher = more penalty)
    """
    if IDEAL_SOIL_PH_MIN <= actual_ph <= IDEAL_SOIL_PH_MAX:
        return 0.0  # No penalty within ideal range
    
    # Calculate deviation from nearest boundary
    if actual_ph < IDEAL_SOIL_PH_MIN:
        deviation = IDEAL_SOIL_PH_MIN - actual_ph
    else:
        deviation = actual_ph - IDEAL_SOIL_PH_MAX
    
    # Calculate penalty based on deviation
    penalty = deviation * SOIL_PH_PENALTY_FACTOR
    
    # Cap penalty at 30% maximum for pH
    return min(penalty, 0.3)


def calculate_total_yield_penalty(
    weather_conditions: Dict[str, float],
    crop_requirements: Dict[str, Any],
    soil_conditions: Dict[str, float]
) -> Dict[str, float]:
    """
    Calculate total yield penalty from all environmental factors.
    
    Args:
        weather_conditions: Dict with 'temperature' and 'rainfall' keys
        crop_requirements: Crop specification dictionary
        soil_conditions: Dict with 'ph' key
    
    Returns:
        Dictionary with individual penalties and total penalty
    """
    # Calculate individual penalties
    temp_penalty = calculate_temperature_penalty(
        weather_conditions['temperature'],
        crop_requirements['ideal_temp_min'],
        crop_requirements['ideal_temp_max']
    )
    
    rain_penalty = calculate_rainfall_penalty(
        weather_conditions['rainfall'],
        crop_requirements['ideal_rain_min'],
        crop_requirements['ideal_rain_max']
    )
    
    ph_penalty = calculate_soil_ph_penalty(soil_conditions['ph'])
    
    # Total penalty is not additive to avoid over-penalization
    # Use compound penalty: 1 - (1-p1)(1-p2)(1-p3)
    total_penalty = 1 - ((1 - temp_penalty) * (1 - rain_penalty) * (1 - ph_penalty))
    
    return {
        'temperature_penalty': temp_penalty,
        'rainfall_penalty': rain_penalty,
        'soil_ph_penalty': ph_penalty,
        'total_penalty': total_penalty
    }


def calculate_adjusted_yield(
    base_yield: float,
    penalty_factors: Dict[str, float]
) -> float:
    """
    Calculate adjusted yield after applying penalty factors.
    
    Args:
        base_yield: Base yield per acre under ideal conditions
        penalty_factors: Dictionary of penalty factors from calculate_total_yield_penalty
    
    Returns:
        Adjusted yield per acre
    """
    total_penalty = penalty_factors['total_penalty']
    return base_yield * (1 - total_penalty)


def get_yield_multiplier(penalty_factors: Dict[str, float]) -> float:
    """
    Get the yield multiplier (0.0 to 1.0) based on penalty factors.
    
    Args:
        penalty_factors: Dictionary of penalty factors
    
    Returns:
        Yield multiplier (1.0 = no penalty, 0.0 = total loss)
    """
    return 1 - penalty_factors['total_penalty']


def calculate_weather_suitability_score(
    weather_conditions: Dict[str, float],
    crop_requirements: Dict[str, Any]
) -> float:
    """
    Calculate a suitability score (0-100) based on weather conditions.
    
    Args:
        weather_conditions: Dict with 'temperature' and 'rainfall' keys
        crop_requirements: Crop specification dictionary
    
    Returns:
        Suitability score (100 = perfect conditions, 0 = completely unsuitable)
    """
    temp_penalty = calculate_temperature_penalty(
        weather_conditions['temperature'],
        crop_requirements['ideal_temp_min'],
        crop_requirements['ideal_temp_max']
    )
    
    rain_penalty = calculate_rainfall_penalty(
        weather_conditions['rainfall'],
        crop_requirements['ideal_rain_min'],
        crop_requirements['ideal_rain_max']
    )
    
    # Convert penalties to suitability score
    temp_score = (1 - temp_penalty) * 50  # Temperature contributes 50 points max
    rain_score = (1 - rain_penalty) * 50  # Rainfall contributes 50 points max
    
    return temp_score + rain_score
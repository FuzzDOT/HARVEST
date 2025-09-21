"""
Fertilizer matching rules based on crop requirements and availability.
"""

from typing import List, Dict, Any, Optional
import pandas as pd
from ..io_.loaders import load_fertilizers


def find_suitable_fertilizers(crop: Dict[str, Any], month: int) -> List[Dict[str, Any]]:
    """
    Find fertilizers suitable for a crop in a given month.
    
    Args:
        crop: Crop specification dictionary
        month: Month number (1-12)
    
    Returns:
        List of suitable fertilizer records
    """
    fertilizers = load_fertilizers()
    suitable_fertilizers = []
    
    for _, fertilizer in fertilizers.iterrows():
        fertilizer_dict = fertilizer.to_dict()
        if is_fertilizer_available_in_month(fertilizer_dict, month):
            suitable_fertilizers.append(fertilizer_dict)
    
    return suitable_fertilizers


def is_fertilizer_available_in_month(fertilizer: Dict[str, Any], month: int) -> bool:
    """
    Check if a fertilizer is available for application in the given month.
    
    Args:
        fertilizer: Fertilizer specification dictionary
        month: Month number (1-12)
    
    Returns:
        True if fertilizer can be applied in this month
    """
    valid_months = fertilizer['valid_months']
    return month in valid_months


def get_best_fertilizer_for_crop(
    crop: Dict[str, Any], 
    month: int,
    preference: str = "balanced",
    excluded_fertilizers: Optional[set] = None
) -> Optional[Dict[str, Any]]:
    """
    Get the best fertilizer for a crop based on preference criteria.
    
    Args:
        crop: Crop specification dictionary
        month: Month number (1-12)
        preference: Selection criteria ("balanced", "nitrogen", "phosphorus", "potassium", "cost")
        excluded_fertilizers: Set of fertilizer names to exclude for diversity
    
    Returns:
        Best fertilizer record or None if no suitable fertilizer found
    """
    if excluded_fertilizers is None:
        excluded_fertilizers = set()
        
    suitable_fertilizers = find_suitable_fertilizers(crop, month)
    
    # Filter out excluded fertilizers for diversity
    suitable_fertilizers = [f for f in suitable_fertilizers 
                          if f.get('fertilizer_name') not in excluded_fertilizers]
    
    if not suitable_fertilizers:
        # If all fertilizers are excluded, fall back to any suitable fertilizer
        suitable_fertilizers = find_suitable_fertilizers(crop, month)
        if not suitable_fertilizers:
            return None
    
    if preference == "balanced":
        # Prefer fertilizers with balanced NPK ratios
        return min(suitable_fertilizers, key=lambda f: npk_variance(f))
    elif preference == "nitrogen":
        # Prefer high nitrogen content
        return max(suitable_fertilizers, key=lambda f: f['nitrogen_percent'])
    elif preference == "phosphorus":
        # Prefer high phosphorus content
        return max(suitable_fertilizers, key=lambda f: f['phosphorus_percent'])
    elif preference == "potassium":
        # Prefer high potassium content
        return max(suitable_fertilizers, key=lambda f: f['potassium_percent'])
    elif preference == "cost":
        # Prefer lowest cost
        return min(suitable_fertilizers, key=lambda f: f['cost_usd_per_lb'])
    else:
        # Default to first available
        return suitable_fertilizers[0]


def get_diverse_fertilizer_for_crop(
    crop: Dict[str, Any], 
    month: int,
    used_fertilizers: set,
    preference: str = "balanced"
) -> Optional[Dict[str, Any]]:
    """
    Get a fertilizer for a crop ensuring diversity from previously used fertilizers.
    
    Args:
        crop: Crop specification dictionary
        month: Month number (1-12)
        used_fertilizers: Set of already used fertilizer names
        preference: Selection criteria ("balanced", "nitrogen", "phosphorus", "potassium", "cost")
    
    Returns:
        Diverse fertilizer record or None if no suitable fertilizer found
    """
    return get_best_fertilizer_for_crop(crop, month, preference, used_fertilizers)


def npk_variance(fertilizer: Dict[str, Any]) -> float:
    """
    Calculate the variance in NPK ratios (lower = more balanced).
    Extract NPK values from fertilizer name if available.
    
    Args:
        fertilizer: Fertilizer specification dictionary
    
    Returns:
        Variance in NPK percentages (or 0 if NPK not extractable)
    """
    import re
    
    # Try to extract NPK from fertilizer name (e.g., "Urea 46-0-0")
    name = fertilizer.get('fertilizer_name', '')
    npk_match = re.search(r'(\d+)-(\d+)-(\d+)', name)
    
    if npk_match:
        n, p, k = map(int, npk_match.groups())
        npk_values = [n, p, k]
        
        mean_npk = sum(npk_values) / len(npk_values)
        variance = sum((x - mean_npk) ** 2 for x in npk_values) / len(npk_values)
        return variance
    else:
        # If no NPK pattern found, use cost as fallback metric
        return fertilizer.get('cost_usd_per_lb', 1.0)


def calculate_fertilizer_cost_per_acre(
    fertilizer: Dict[str, Any],
    application_rate_lbs: float = 100.0
) -> float:
    """
    Calculate the cost of fertilizer per acre at a given application rate.
    
    Args:
        fertilizer: Fertilizer specification dictionary
        application_rate_lbs: Pounds of fertilizer per acre
    
    Returns:
        Cost per acre in dollars
    """
    return fertilizer['cost_usd_per_lb'] * application_rate_lbs


def get_fertilizer_recommendations_for_season(
    crop: Dict[str, Any],
    planting_month: int,
    growing_months: List[int]
) -> List[Dict[str, Any]]:
    """
    Get fertilizer recommendations for an entire growing season.
    
    Args:
        crop: Crop specification dictionary
        planting_month: Month when crop is planted
        growing_months: List of months during crop growth
    
    Returns:
        List of fertilizer application recommendations
    """
    recommendations = []
    
    # Pre-plant fertilizer (if available)
    pre_plant_fertilizers = find_suitable_fertilizers(crop, planting_month)
    if pre_plant_fertilizers:
        best_pre_plant = get_best_fertilizer_for_crop(crop, planting_month, "balanced")
        if best_pre_plant:
            recommendations.append({
                "timing": "pre-plant",
                "month": planting_month,
                "fertilizer": best_pre_plant,
                "application_rate": 100.0,
                "cost_per_acre": calculate_fertilizer_cost_per_acre(best_pre_plant, 100.0)
            })
    
    # Mid-season fertilizer applications
    for month in growing_months[1:-1]:  # Skip first and last month
        mid_season_fertilizers = find_suitable_fertilizers(crop, month)
        if mid_season_fertilizers:
            best_mid_season = get_best_fertilizer_for_crop(crop, month, "nitrogen")
            if best_mid_season:
                recommendations.append({
                    "timing": "mid-season",
                    "month": month,
                    "fertilizer": best_mid_season,
                    "application_rate": 50.0,
                    "cost_per_acre": calculate_fertilizer_cost_per_acre(best_mid_season, 50.0)
                })
    
    return recommendations


def get_organic_fertilizers(month: int) -> List[Dict[str, Any]]:
    """
    Get available organic fertilizers for a given month.
    
    Args:
        month: Month number (1-12)
    
    Returns:
        List of organic fertilizer records
    """
    fertilizers = load_fertilizers()
    organic_fertilizers = []
    
    for _, fertilizer in fertilizers.iterrows():
        fertilizer_dict = fertilizer.to_dict()
        if (is_fertilizer_available_in_month(fertilizer_dict, month) and 
            "organic" in fertilizer_dict['name'].lower()):
            organic_fertilizers.append(fertilizer_dict)
    
    return organic_fertilizers
"""
Crop eligibility rules based on planting and harvest windows.
"""

from typing import List, Dict, Any
import pandas as pd
from ..io_.loaders import load_crops


def filter_crops_by_month(month: int) -> List[Dict[str, Any]]:
    """
    Filter crops that can be planted or harvested in the given month.
    
    Args:
        month: Month number (1-12)
    
    Returns:
        List of eligible crop records
    """
    crops = load_crops()
    eligible_crops = []
    
    for _, crop in crops.iterrows():
        if is_crop_eligible_for_month(crop.to_dict(), month):
            eligible_crops.append(crop.to_dict())
    
    return eligible_crops


def is_crop_eligible_for_month(crop: Dict[str, Any], month: int) -> bool:
    """
    Check if a crop can be planted in the given month.
    Since real data doesn't have growth windows, use category-based defaults.
    
    Args:
        crop: Crop specification dictionary
        month: Month number (1-12)
    
    Returns:
        True if crop can be planted in this month
    """
    # Default planting windows by crop category for real data
    category_windows = {
        'grain': (3, 10),      # March to October (corn, wheat, etc)
        'fiber': (4, 6),       # April to June (cotton)
        'legume': (4, 8),      # April to August (soybeans, peanuts)
        'vegetable': (3, 10),  # March to October (most vegetables)
        'fruit': (3, 5),       # March to May (berry crops, etc)
        'tuber': (3, 8),       # March to August (potatoes, sweet potatoes)
        'cash_crop': (4, 7),   # April to July (tobacco, etc)
    }
    
    # Get crop category, default to grain if not specified
    category = crop.get('category', 'grain')
    start_month, end_month = category_windows.get(category, (3, 10))
    
    # Handle year-wrapping windows
    if start_month <= end_month:
        # Normal case: within same year
        return start_month <= month <= end_month
    else:
        # Year-wrapping case: crosses into next year
        return month >= start_month or month <= end_month


def get_eligible_crops_for_season(start_month: int, end_month: int) -> List[Dict[str, Any]]:
    """
    Get crops that can be planted within a season range.
    
    Args:
        start_month: Season start month (1-12)
        end_month: Season end month (1-12)
    
    Returns:
        List of eligible crop records
    """
    crops = load_crops()
    eligible_crops = []
    
    for _, crop in crops.iterrows():
        crop_dict = crop.to_dict()
        
        # Use category-based defaults since real data doesn't have growth windows
        category = crop_dict.get('category', 'grain')
        category_windows = {
            'grain': (3, 10),      # March to October (corn, wheat, etc)
            'fiber': (4, 6),       # April to June (cotton)
            'legume': (4, 8),      # April to August (soybeans, peanuts)
            'vegetable': (3, 10),  # March to October (most vegetables)
            'fruit': (3, 5),       # March to May (berry crops, etc)
            'tuber': (3, 8),       # March to August (potatoes, sweet potatoes)
            'cash_crop': (4, 7),   # April to July (tobacco, etc)
            'oilseed': (4, 8),     # April to August (sunflower, etc)
        }
        
        crop_start, crop_end = category_windows.get(category, (3, 10))
        
        # Check if crop window overlaps with season
        if seasons_overlap(crop_start, crop_end, start_month, end_month):
            eligible_crops.append(crop_dict)
    
    return eligible_crops


def seasons_overlap(crop_start: int, crop_end: int, season_start: int, season_end: int) -> bool:
    """
    Check if crop growing window overlaps with a season.
    
    Args:
        crop_start: Crop planting month
        crop_end: Crop harvest month
        season_start: Season start month
        season_end: Season end month
    
    Returns:
        True if windows overlap
    """
    # Convert to sets of months for easier overlap checking
    crop_months = get_month_range(crop_start, crop_end)
    season_months = get_month_range(season_start, season_end)
    
    # Check for any overlap
    return bool(crop_months.intersection(season_months))


def get_month_range(start: int, end: int) -> set:
    """
    Get set of months in a range, handling year wrapping.
    
    Args:
        start: Start month (1-12)
        end: End month (1-12)
    
    Returns:
        Set of month numbers
    """
    if start <= end:
        return set(range(start, end + 1))
    else:
        # Year-wrapping case
        return set(range(start, 13)) | set(range(1, end + 1))


def is_month_in_harvest_window(crop: Dict[str, Any], month: int) -> bool:
    """
    Check if a month is within the crop's harvest window.
    Assumes harvest occurs in the last month of the growth window.
    
    Args:
        crop: Crop specification dictionary
        month: Month number (1-12)
    
    Returns:
        True if month is in harvest window
    """
    # Use category-based defaults since real data doesn't have growth windows
    category = crop.get('category', 'grain')
    category_windows = {
        'grain': (3, 10),      # March to October (corn, wheat, etc)
        'fiber': (4, 6),       # April to June (cotton)
        'legume': (4, 8),      # April to August (soybeans, peanuts)
        'vegetable': (3, 10),  # March to October (most vegetables)
        'fruit': (3, 5),       # March to May (berry crops, etc)
        'tuber': (3, 8),       # March to August (potatoes, sweet potatoes)
        'cash_crop': (4, 7),   # April to July (tobacco, etc)
        'oilseed': (4, 8),     # April to August (sunflower, etc)
    }
    
    _, harvest_month = category_windows.get(category, (3, 10))
    return month == harvest_month


def get_crops_harvestable_in_month(month: int) -> List[Dict[str, Any]]:
    """
    Get crops that can be harvested in the given month.
    
    Args:
        month: Month number (1-12)
    
    Returns:
        List of crops ready for harvest
    """
    crops = load_crops()
    harvestable_crops = []
    
    for _, crop in crops.iterrows():
        crop_dict = crop.to_dict()
        if is_month_in_harvest_window(crop_dict, month):
            harvestable_crops.append(crop_dict)
    
    return harvestable_crops
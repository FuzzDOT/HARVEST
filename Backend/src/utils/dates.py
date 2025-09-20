"""
Date utility functions for checking planting/harvest windows and seasonal calculations.
"""

from datetime import datetime, date
from typing import List, Tuple, Optional
from ..config import MONTH_NAMES


def is_month_in_range(month: int, start_month: int, end_month: int) -> bool:
    """
    Check if a month falls within a range, handling year wrapping.
    
    Args:
        month: Month to check (1-12)
        start_month: Start of range (1-12)
        end_month: End of range (1-12)
    
    Returns:
        True if month is in range
    """
    if start_month <= end_month:
        # Normal range within same year
        return start_month <= month <= end_month
    else:
        # Range wraps around year end (e.g., Oct-Feb = 10-2)
        return month >= start_month or month <= end_month


def get_months_in_range(start_month: int, end_month: int) -> List[int]:
    """
    Get list of months in a range, handling year wrapping.
    
    Args:
        start_month: Start of range (1-12)
        end_month: End of range (1-12)
    
    Returns:
        List of month numbers
    """
    if start_month <= end_month:
        return list(range(start_month, end_month + 1))
    else:
        # Year wrapping case
        return list(range(start_month, 13)) + list(range(1, end_month + 1))


def get_season_from_month(month: int) -> str:
    """
    Get season name from month number.
    
    Args:
        month: Month number (1-12)
    
    Returns:
        Season name
    """
    seasons = {
        (12, 1, 2): "Winter",
        (3, 4, 5): "Spring", 
        (6, 7, 8): "Summer",
        (9, 10, 11): "Fall"
    }
    
    for months, season in seasons.items():
        if month in months:
            return season
    
    return "Unknown"


def get_month_name(month: int) -> str:
    """
    Get month name from month number.
    
    Args:
        month: Month number (1-12)
    
    Returns:
        Month name
    """
    if 1 <= month <= 12:
        return MONTH_NAMES[month - 1]
    return "Invalid Month"


def get_current_month() -> int:
    """Get current month number."""
    return datetime.now().month


def get_current_year() -> int:
    """Get current year."""
    return datetime.now().year


def months_between_dates(start_date: date, end_date: date) -> int:
    """
    Calculate number of months between two dates.
    
    Args:
        start_date: Start date
        end_date: End date
    
    Returns:
        Number of months between dates
    """
    return (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)


def add_months_to_date(base_date: date, months: int) -> date:
    """
    Add months to a date.
    
    Args:
        base_date: Starting date
        months: Number of months to add
    
    Returns:
        New date with months added
    """
    year = base_date.year
    month = base_date.month + months
    
    # Handle year overflow
    while month > 12:
        month -= 12
        year += 1
    
    # Handle year underflow
    while month < 1:
        month += 12
        year -= 1
    
    # Handle day overflow (e.g., Jan 31 + 1 month = Feb 28/29)
    try:
        return date(year, month, base_date.day)
    except ValueError:
        # Day doesn't exist in target month, use last day of month
        import calendar
        last_day = calendar.monthrange(year, month)[1]
        return date(year, month, min(base_date.day, last_day))


def get_planting_window_months(growth_window_start: int, growth_window_end: int) -> List[int]:
    """
    Get all months in a crop's planting window.
    
    Args:
        growth_window_start: Start month of growth window
        growth_window_end: End month of growth window
    
    Returns:
        List of months when crop can be planted
    """
    return get_months_in_range(growth_window_start, growth_window_end)


def is_harvest_month(crop_growth_window_end: int, current_month: int) -> bool:
    """
    Check if current month is harvest time for a crop.
    
    Args:
        crop_growth_window_end: End month of crop growth window
        current_month: Current month to check
    
    Returns:
        True if it's harvest time
    """
    return current_month == crop_growth_window_end


def calculate_growing_season_length(start_month: int, end_month: int) -> int:
    """
    Calculate length of growing season in months.
    
    Args:
        start_month: Start of growing season
        end_month: End of growing season
    
    Returns:
        Number of months in growing season
    """
    if start_month <= end_month:
        return end_month - start_month + 1
    else:
        # Year-wrapping season
        return (12 - start_month + 1) + end_month


def get_next_planting_months(current_month: int, num_months: int = 3) -> List[Tuple[int, str]]:
    """
    Get the next N months for potential planting.
    
    Args:
        current_month: Current month (1-12)
        num_months: Number of future months to return
    
    Returns:
        List of (month_number, month_name) tuples
    """
    next_months = []
    
    for i in range(1, num_months + 1):
        month = ((current_month + i - 1) % 12) + 1
        month_name = get_month_name(month)
        next_months.append((month, month_name))
    
    return next_months


def is_growing_season_viable(
    planting_month: int, 
    harvest_month: int, 
    current_month: int
) -> bool:
    """
    Check if a growing season is still viable given current month.
    
    Args:
        planting_month: When crop should be planted
        harvest_month: When crop should be harvested
        current_month: Current month
    
    Returns:
        True if growing season is still viable
    """
    # If we're past the planting window, not viable
    if planting_month <= harvest_month:
        # Normal season within same year
        return current_month <= planting_month
    else:
        # Year-wrapping season
        return current_month <= planting_month or current_month >= harvest_month


def format_date_range(start_month: int, end_month: int) -> str:
    """
    Format a month range as human-readable string.
    
    Args:
        start_month: Start month (1-12)
        end_month: End month (1-12)
    
    Returns:
        Formatted date range string
    """
    start_name = get_month_name(start_month)
    end_name = get_month_name(end_month)
    
    if start_month == end_month:
        return start_name
    else:
        return f"{start_name} - {end_name}"


def get_days_in_month(month: int, year: Optional[int] = None) -> int:
    """
    Get number of days in a month.
    
    Args:
        month: Month number (1-12)
        year: Year (if None, uses current year)
    
    Returns:
        Number of days in the month
    """
    if year is None:
        year = get_current_year()
    
    import calendar
    return calendar.monthrange(year, month)[1]
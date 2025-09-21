"""
Profit calculations for crop recommendations.
"""

import pandas as pd
from typing import Dict, Any, Optional
from .yield_penalty import calculate_adjusted_yield, calculate_total_yield_penalty
from ..io_.loaders import get_latest_price
from ..rules.fertilizer_match import get_best_fertilizer_for_crop, calculate_fertilizer_cost_per_acre
from ..config import FERTILIZER_APPLICATION_RATE


def calculate_gross_revenue(
    crop: Dict[str, Any],
    adjusted_yield: float,
    price_per_unit: Optional[float] = None
) -> float:
    """
    Calculate gross revenue from crop sales.
    
    Args:
        crop: Crop specification dictionary
        adjusted_yield: Yield per acre after penalties
        price_per_unit: Price per unit (if None, uses latest price from history)
    
    Returns:
        Gross revenue per acre
    """
    if price_per_unit is None:
        price_per_unit = get_latest_price(crop['crop_name'])
        if price_per_unit is None:
            raise ValueError(f"No price data available for crop {crop['crop_name']}")
    
    return adjusted_yield * price_per_unit


def calculate_production_costs(
    crop: Dict[str, Any],
    fertilizer: Optional[Dict[str, Any]] = None,
    fertilizer_rate: float = FERTILIZER_APPLICATION_RATE
) -> Dict[str, float]:
    """
    Calculate total production costs per acre.
    
    Args:
        crop: Crop specification dictionary
        fertilizer: Fertilizer specification (if None, no fertilizer cost)
        fertilizer_rate: Fertilizer application rate in lbs per acre
    
    Returns:
        Dictionary with cost breakdown
    """
    # Estimate base cost per acre if not provided
    # Use category-based estimates (these could be made more sophisticated)
    if 'cost_per_acre' in crop:
        base_cost = crop['cost_per_acre']
    else:
        # Default cost estimates by crop category (USD per acre)
        cost_estimates = {
            'grain': 500,     # corn, wheat, rice
            'legume': 400,    # peanuts, soybeans
            'fiber': 600,     # cotton
            'vegetable': 800  # general vegetables
        }
        category = crop.get('category', 'grain')
        base_cost = cost_estimates.get(category, 500)
    
    fertilizer_cost = 0.0
    if fertilizer:
        fertilizer_cost = calculate_fertilizer_cost_per_acre(fertilizer, fertilizer_rate)
    
    total_cost = base_cost + fertilizer_cost
    
    return {
        'base_cost': base_cost,
        'fertilizer_cost': fertilizer_cost,
        'total_cost': total_cost
    }


def calculate_net_profit(
    crop: Dict[str, Any],
    weather_conditions: pd.DataFrame,
    soil_conditions: Dict[str, float],
    month: int,
    price_per_unit: Optional[float] = None,
    fertilizer_preference: str = "balanced"
) -> Dict[str, Any]:
    """
    Calculate net profit per acre for a crop under given conditions.
    
    Args:
        crop: Crop specification dictionary
        weather_conditions: Dict with 'temperature' and 'rainfall' keys
        soil_conditions: Dict with 'ph' key
        month: Month for fertilizer availability
        price_per_unit: Override price (if None, uses latest price)
        fertilizer_preference: Fertilizer selection preference
    
    Returns:
        Dictionary with profit calculation breakdown
    """
    # Calculate yield penalties and adjusted yield
    penalty_factors = calculate_total_yield_penalty(
        weather_conditions, crop, soil_conditions
    )
    
    adjusted_yield = calculate_adjusted_yield(
        crop['yield_lb_per_acre_est'], penalty_factors
    )
    
    # Get best fertilizer for this crop and month
    fertilizer = get_best_fertilizer_for_crop(crop, month, fertilizer_preference)
    
    # Calculate costs
    costs = calculate_production_costs(crop, fertilizer)
    
    # Calculate revenue
    revenue = calculate_gross_revenue(crop, adjusted_yield, price_per_unit)
    
    # Calculate net profit
    net_profit = revenue - costs['total_cost']
    
    return {
        'crop_name': crop['crop_name'],
        'base_yield': crop['yield_lb_per_acre_est'],
        'adjusted_yield': adjusted_yield,
        'yield_penalty_factors': penalty_factors,
        'gross_revenue': revenue,
        'production_costs': costs,
        'net_profit': net_profit,
        'profit_per_acre': net_profit,
        'roi_percent': (net_profit / costs['total_cost']) * 100 if costs['total_cost'] > 0 else 0,
        'fertilizer_used': fertilizer['fertilizer_name'] if fertilizer else None,
        'price_per_unit': price_per_unit or get_latest_price(crop['crop_name'])
    }


def calculate_profit_margin(revenue: float, costs: float) -> float:
    """
    Calculate profit margin as percentage.
    
    Args:
        revenue: Gross revenue
        costs: Total costs
    
    Returns:
        Profit margin percentage
    """
    if revenue == 0:
        return 0.0
    
    return ((revenue - costs) / revenue) * 100


def calculate_break_even_yield(
    crop: Dict[str, Any],
    price_per_unit: Optional[float] = None
) -> float:
    """
    Calculate the minimum yield needed to break even.
    
    Args:
        crop: Crop specification dictionary
        price_per_unit: Price per unit (if None, uses latest price)
    
    Returns:
        Break-even yield per acre
    """
    if price_per_unit is None:
        price_per_unit = get_latest_price(crop['crop_name'])
        if price_per_unit is None:
            raise ValueError(f"No price data available for crop {crop['crop_name']}")
    
    # Use estimated cost per acre based on category if not available
    if 'cost_per_acre' in crop:
        base_cost = crop['cost_per_acre']
    else:
        # Estimate cost per acre based on crop category
        cost_estimates = {
            'grain': 400,
            'vegetable': 600, 
            'fruit': 800,
            'cash_crop': 500,
            'legume': 300
        }
        base_cost = cost_estimates.get(crop.get('category', 'grain'), 400)
    
    return base_cost / price_per_unit


def calculate_profit_sensitivity(
    base_profit: Dict[str, Any],
    price_variation: float = 0.1
) -> Dict[str, float]:
    """
    Calculate profit sensitivity to price changes.
    
    Args:
        base_profit: Base profit calculation from calculate_net_profit
        price_variation: Percentage variation to test (0.1 = ±10%)
    
    Returns:
        Dictionary with profit under different price scenarios
    """
    base_price = base_profit['price_per_unit']
    adjusted_yield = base_profit['adjusted_yield']
    total_costs = base_profit['production_costs']['total_cost']
    
    price_low = base_price * (1 - price_variation)
    price_high = base_price * (1 + price_variation)
    
    profit_low = (adjusted_yield * price_low) - total_costs
    profit_high = (adjusted_yield * price_high) - total_costs
    
    return {
        'base_profit': base_profit['net_profit'],
        'profit_at_low_price': profit_low,
        'profit_at_high_price': profit_high,
        'price_sensitivity': (profit_high - profit_low) / (2 * price_variation * base_price)
    }


def calculate_annual_profit_potential(
    monthly_profits: list,
    acreage: float
) -> Dict[str, float]:
    """
    Calculate annual profit potential from monthly recommendations.
    
    Args:
        monthly_profits: List of monthly profit calculations
        acreage: Total acreage available
    
    Returns:
        Dictionary with annual profit summary
    """
    total_annual_profit = sum(profit['net_profit'] for profit in monthly_profits)
    total_farm_profit = total_annual_profit * acreage
    
    average_monthly_profit = total_annual_profit / len(monthly_profits) if monthly_profits else 0
    
    best_month = max(monthly_profits, key=lambda x: x['net_profit']) if monthly_profits else None
    worst_month = min(monthly_profits, key=lambda x: x['net_profit']) if monthly_profits else None
    
    return {
        'total_annual_profit_per_acre': float(total_annual_profit),
        'total_farm_profit': float(total_farm_profit),
        'average_monthly_profit': float(average_monthly_profit),
        'best_month_profit': float(best_month['net_profit']) if best_month else 0.0,
        'worst_month_profit': float(worst_month['net_profit']) if worst_month else 0.0
    }
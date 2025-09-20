"""
Long-term prediction pipeline using historical weather normals for annual planning.
"""

from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime

from ..io_.loaders import load_parcel_by_id, load_weather_normals
from ..rules.crop_eligibility import filter_crops_by_month
from ..model.profit_calc import calculate_net_profit, calculate_annual_profit_potential
from ..model.ranker import rank_crops_by_profit, apply_diversification_scoring
from ..io_.writers import save_long_term_plan
from ..config import MONTH_NAMES


def plan_annual_crop_rotation(
    parcel_id: str,
    start_month: int = 1,
    diversification_bonus: float = 0.1,
    min_profit_threshold: float = 0.0
) -> Dict[str, Any]:
    """
    Generate a 12-month crop rotation plan using historical weather normals.
    
    Args:
        parcel_id: ID of the parcel to analyze
        start_month: Starting month for the annual plan (1-12)
        diversification_bonus: Bonus factor for crop diversification
        min_profit_threshold: Minimum profit per acre to consider a crop
    
    Returns:
        Dictionary containing annual plan and analysis
    """
    # Load parcel information
    parcel = load_parcel_by_id(parcel_id)
    if not parcel:
        raise ValueError(f"Parcel {parcel_id} not found")
    
    # Generate monthly recommendations for the year
    monthly_plans = []
    all_monthly_profits = []
    
    for i in range(12):
        month = ((start_month + i - 1) % 12) + 1
        month_plan = generate_monthly_plan_with_normals(
            parcel=parcel,
            month=month,
            min_profit_threshold=min_profit_threshold
        )
        
        if month_plan['best_crop']:
            monthly_plans.append(month_plan)
            all_monthly_profits.append(month_plan['best_crop'])
    
    # Apply diversification scoring to encourage variety
    if all_monthly_profits:
        diversified_profits = apply_diversification_scoring(
            all_monthly_profits, diversification_bonus
        )
        
        # Update monthly plans with diversification scores
        for i, plan in enumerate(monthly_plans):
            if i < len(diversified_profits):
                plan['best_crop'] = diversified_profits[i]
    
    # Calculate annual summary
    annual_summary = calculate_annual_profit_potential(
        all_monthly_profits, parcel['acreage']
    )
    
    # Identify optimal rotation sequence
    rotation_sequence = optimize_rotation_sequence(monthly_plans)
    
    return {
        'parcel_id': parcel_id,
        'parcel_info': parcel,
        'plan_start_month': start_month,
        'monthly_plans': monthly_plans,
        'rotation_sequence': rotation_sequence,
        'annual_summary': annual_summary,
        'diversification_bonus': diversification_bonus,
        'total_months_planned': len(monthly_plans),
        'generated_at': datetime.now().isoformat()
    }


def generate_monthly_plan_with_normals(
    parcel: Dict[str, Any],
    month: int,
    min_profit_threshold: float = 0.0
) -> Dict[str, Any]:
    """
    Generate crop recommendations for a month using historical weather normals.
    
    Args:
        parcel: Parcel information dictionary
        month: Month number (1-12)
        min_profit_threshold: Minimum profit threshold
    
    Returns:
        Monthly plan dictionary
    """
    # Get crops eligible for this month
    eligible_crops = filter_crops_by_month(month)
    
    if not eligible_crops:
        return {
            'month': month,
            'month_name': MONTH_NAMES[month - 1],
            'eligible_crops': 0,
            'best_crop': None,
            'alternatives': [],
            'weather_conditions': None
        }
    
    # Get historical weather normals for the region and month
    weather_normals = get_weather_normals_for_month(parcel['region'], month)
    
    if not weather_normals:
        return {
            'month': month,
            'month_name': MONTH_NAMES[month - 1],
            'eligible_crops': len(eligible_crops),
            'best_crop': None,
            'alternatives': [],
            'weather_conditions': None,
            'error': f'No weather normals available for region {parcel["region"]}'
        }
    
    # Calculate profit for each eligible crop
    profit_calculations = []
    soil_conditions = {'ph': parcel['soil_ph']}
    
    for crop in eligible_crops:
        try:
            profit_calc = calculate_net_profit(
                crop=crop,
                weather_conditions=weather_normals,
                soil_conditions=soil_conditions,
                month=month
            )
            
            # Only include crops meeting profit threshold
            if profit_calc['net_profit'] >= min_profit_threshold:
                profit_calculations.append(profit_calc)
                
        except Exception as e:
            print(f"Warning: Could not calculate profit for crop {crop['crop_id']}: {e}")
            continue
    
    # Rank by profit
    ranked_crops = rank_crops_by_profit(profit_calculations)
    
    best_crop = ranked_crops[0] if ranked_crops else None
    alternatives = ranked_crops[1:4] if len(ranked_crops) > 1 else []  # Top 3 alternatives
    
    return {
        'month': month,
        'month_name': MONTH_NAMES[month - 1],
        'eligible_crops': len(eligible_crops),
        'profitable_crops': len(profit_calculations),
        'best_crop': best_crop,
        'alternatives': alternatives,
        'weather_conditions': weather_normals
    }


def get_weather_normals_for_month(region: str, month: int) -> Optional[Dict[str, float]]:
    """
    Get historical weather normals for a region and month.
    
    Args:
        region: Region name
        month: Month number (1-12)
    
    Returns:
        Weather normals dictionary or None if not found
    """
    try:
        normals_df = load_weather_normals()
        
        # Filter by region and month
        region_month = normals_df[
            (normals_df['region'] == region) & 
            (normals_df['month'] == month)
        ]
        
        if region_month.empty:
            return None
        
        row = region_month.iloc[0]
        
        return {
            'temperature': row['avg_temp_f'],
            'rainfall': row['avg_rainfall_inches'],
            'humidity': row.get('avg_humidity_percent', 65),  # Default if not available
        }
        
    except Exception as e:
        print(f"Error loading weather normals: {e}")
        return None


def optimize_rotation_sequence(monthly_plans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Optimize crop rotation sequence to maximize benefits and minimize conflicts.
    
    Args:
        monthly_plans: List of monthly plan dictionaries
    
    Returns:
        Optimized rotation sequence with additional analysis
    """
    rotation_sequence = []
    
    for i, plan in enumerate(monthly_plans):
        if not plan['best_crop']:
            continue
            
        crop_info = {
            'month': plan['month'],
            'month_name': plan['month_name'],
            'crop_id': plan['best_crop']['crop_id'],
            'crop_name': plan['best_crop']['crop_name'],
            'profit_per_acre': plan['best_crop']['net_profit'],
            'roi_percent': plan['best_crop']['roi_percent']
        }
        
        # Add rotation benefits/concerns
        if i > 0:
            prev_crop = rotation_sequence[-1]
            crop_info['rotation_notes'] = analyze_crop_succession(
                prev_crop['crop_id'], 
                crop_info['crop_id']
            )
        
        rotation_sequence.append(crop_info)
    
    return rotation_sequence


def analyze_crop_succession(prev_crop_id: str, current_crop_id: str) -> str:
    """
    Analyze the benefits or concerns of crop succession.
    
    Args:
        prev_crop_id: Previous crop ID
        current_crop_id: Current crop ID
    
    Returns:
        Analysis note about the succession
    """
    # Simple rotation rules (can be expanded)
    rotation_benefits = {
        ('CORN', 'SOYBEAN'): 'Good rotation: soybeans fix nitrogen for corn',
        ('SOYBEAN', 'CORN'): 'Excellent rotation: corn utilizes nitrogen from soybeans',
        ('WHEAT', 'SOYBEAN'): 'Good rotation: different nutrient requirements',
        ('POTATO', 'WHEAT'): 'Good rotation: breaks disease cycles'
    }
    
    rotation_concerns = {
        ('CORN', 'CORN'): 'Concern: consecutive corn may deplete soil nutrients',
        ('POTATO', 'POTATO'): 'Concern: consecutive potatoes increase disease risk',
        ('TOMATO', 'POTATO'): 'Concern: both are nightshades, may share diseases'
    }
    
    succession = (prev_crop_id, current_crop_id)
    
    if succession in rotation_benefits:
        return rotation_benefits[succession]
    elif succession in rotation_concerns:
        return rotation_concerns[succession]
    else:
        return 'Neutral rotation: no significant interactions identified'


def run_long_term_pipeline_for_parcel(
    parcel_id: str,
    start_month: int = 1,
    save_results: bool = True,
    **kwargs
) -> Dict[str, Any]:
    """
    Run complete long-term planning pipeline for a single parcel.
    
    Args:
        parcel_id: ID of the parcel to analyze
        start_month: Starting month for annual plan
        save_results: Whether to save results to CSV
        **kwargs: Additional arguments for plan_annual_crop_rotation
    
    Returns:
        Annual planning results
    """
    results = plan_annual_crop_rotation(parcel_id, start_month, **kwargs)
    
    if save_results and results['monthly_plans']:
        try:
            # Prepare data for saving
            plan_data = []
            for plan in results['monthly_plans']:
                if plan['best_crop']:
                    plan_record = {
                        'month': plan['month'],
                        'month_name': plan['month_name'],
                        'crop_id': plan['best_crop']['crop_id'],
                        'crop_name': plan['best_crop']['crop_name'],
                        'profit_per_acre': plan['best_crop']['net_profit'],
                        'roi_percent': plan['best_crop']['roi_percent'],
                        'adjusted_yield': plan['best_crop']['adjusted_yield']
                    }
                    plan_data.append(plan_record)
            
            output_path = save_long_term_plan(parcel_id, plan_data)
            results['output_file'] = str(output_path)
            
        except Exception as e:
            print(f"Warning: Could not save results: {e}")
    
    return results


def run_long_term_pipeline_for_all_parcels(
    start_month: int = 1,
    save_results: bool = True,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    Run long-term planning pipeline for all parcels.
    
    Args:
        start_month: Starting month for annual plans
        save_results: Whether to save results to CSV
        **kwargs: Additional arguments for plan_annual_crop_rotation
    
    Returns:
        List of annual planning results for all parcels
    """
    from ..io_.loaders import load_parcels
    
    parcels = load_parcels()
    all_results = []
    
    for _, parcel in parcels.iterrows():
        parcel_id = parcel['parcel_id']
        
        try:
            results = run_long_term_pipeline_for_parcel(
                parcel_id=parcel_id,
                start_month=start_month,
                save_results=save_results,
                **kwargs
            )
            all_results.append(results)
            
        except Exception as e:
            print(f"Error processing parcel {parcel_id}: {e}")
            all_results.append({
                'parcel_id': parcel_id,
                'error': str(e),
                'monthly_plans': []
            })
    
    return all_results
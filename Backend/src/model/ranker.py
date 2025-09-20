"""
Ranking and sorting utilities for crop recommendations.
"""

from typing import List, Dict, Any, Callable
import operator


def rank_crops_by_profit(profit_calculations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Rank crops by net profit per acre in descending order.
    
    Args:
        profit_calculations: List of profit calculation dictionaries
    
    Returns:
        Sorted list of profit calculations (highest profit first)
    """
    return sorted(profit_calculations, key=lambda x: x['net_profit'], reverse=True)


def rank_crops_by_roi(profit_calculations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Rank crops by return on investment (ROI) percentage in descending order.
    
    Args:
        profit_calculations: List of profit calculation dictionaries
    
    Returns:
        Sorted list of profit calculations (highest ROI first)
    """
    return sorted(profit_calculations, key=lambda x: x['roi_percent'], reverse=True)


def rank_crops_by_yield(profit_calculations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Rank crops by adjusted yield per acre in descending order.
    
    Args:
        profit_calculations: List of profit calculation dictionaries
    
    Returns:
        Sorted list of profit calculations (highest yield first)
    """
    return sorted(profit_calculations, key=lambda x: x['adjusted_yield'], reverse=True)


def rank_crops_by_suitability(
    profit_calculations: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Rank crops by weather/soil suitability (lowest total penalty).
    
    Args:
        profit_calculations: List of profit calculation dictionaries
    
    Returns:
        Sorted list of profit calculations (most suitable first)
    """
    return sorted(
        profit_calculations, 
        key=lambda x: x['yield_penalty_factors']['total_penalty']
    )


def filter_profitable_crops(
    profit_calculations: List[Dict[str, Any]], 
    min_profit: float = 0.0
) -> List[Dict[str, Any]]:
    """
    Filter crops that meet minimum profit threshold.
    
    Args:
        profit_calculations: List of profit calculation dictionaries
        min_profit: Minimum profit per acre threshold
    
    Returns:
        Filtered list of profitable crops
    """
    return [crop for crop in profit_calculations if crop['net_profit'] >= min_profit]


def filter_by_roi_threshold(
    profit_calculations: List[Dict[str, Any]], 
    min_roi: float = 10.0
) -> List[Dict[str, Any]]:
    """
    Filter crops that meet minimum ROI threshold.
    
    Args:
        profit_calculations: List of profit calculation dictionaries
        min_roi: Minimum ROI percentage threshold
    
    Returns:
        Filtered list of crops meeting ROI threshold
    """
    return [crop for crop in profit_calculations if crop['roi_percent'] >= min_roi]


def get_top_n_recommendations(
    profit_calculations: List[Dict[str, Any]],
    n: int = 3,
    ranking_method: str = "profit"
) -> List[Dict[str, Any]]:
    """
    Get top N crop recommendations based on ranking method.
    
    Args:
        profit_calculations: List of profit calculation dictionaries
        n: Number of top recommendations to return
        ranking_method: Method to rank crops ("profit", "roi", "yield", "suitability")
    
    Returns:
        Top N recommendations
    """
    if ranking_method == "profit":
        ranked = rank_crops_by_profit(profit_calculations)
    elif ranking_method == "roi":
        ranked = rank_crops_by_roi(profit_calculations)
    elif ranking_method == "yield":
        ranked = rank_crops_by_yield(profit_calculations)
    elif ranking_method == "suitability":
        ranked = rank_crops_by_suitability(profit_calculations)
    else:
        raise ValueError(f"Unknown ranking method: {ranking_method}")
    
    return ranked[:n]


def create_recommendation_summary(
    profit_calculations: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Create a summary of all crop recommendations.
    
    Args:
        profit_calculations: List of profit calculation dictionaries
    
    Returns:
        Summary dictionary with key metrics
    """
    if not profit_calculations:
        return {
            'total_crops_evaluated': 0,
            'profitable_crops': 0,
            'avg_profit': 0.0,
            'best_crop': None,
            'worst_crop': None
        }
    
    profitable_crops = filter_profitable_crops(profit_calculations)
    
    profits = [crop['net_profit'] for crop in profit_calculations]
    avg_profit = sum(profits) / len(profits)
    
    best_crop = max(profit_calculations, key=lambda x: x['net_profit'])
    worst_crop = min(profit_calculations, key=lambda x: x['net_profit'])
    
    return {
        'total_crops_evaluated': len(profit_calculations),
        'profitable_crops': len(profitable_crops),
        'avg_profit': avg_profit,
        'best_crop': {
            'name': best_crop['crop_name'],
            'profit': best_crop['net_profit'],
            'roi': best_crop['roi_percent']
        },
        'worst_crop': {
            'name': worst_crop['crop_name'],
            'profit': worst_crop['net_profit'],
            'roi': worst_crop['roi_percent']
        }
    }


def apply_diversification_scoring(
    profit_calculations: List[Dict[str, Any]],
    diversification_bonus: float = 0.1
) -> List[Dict[str, Any]]:
    """
    Apply diversification scoring to encourage crop variety.
    
    Args:
        profit_calculations: List of profit calculation dictionaries
        diversification_bonus: Bonus factor for less common crops
    
    Returns:
        List with diversification scores added
    """
    # Count how many times each crop appears (for multi-parcel scenarios)
    crop_counts = {}
    for calc in profit_calculations:
        crop_id = calc['crop_id']
        crop_counts[crop_id] = crop_counts.get(crop_id, 0) + 1
    
    # Apply diversification bonus (lower count = higher bonus)
    max_count = max(crop_counts.values()) if crop_counts else 1
    
    for calc in profit_calculations:
        crop_id = calc['crop_id']
        crop_frequency = crop_counts[crop_id]
        
        # Calculate diversification multiplier (rare crops get bonus)
        diversification_multiplier = 1 + (diversification_bonus * (max_count - crop_frequency) / max_count)
        
        # Apply to profit
        calc['diversified_profit'] = calc['net_profit'] * diversification_multiplier
        calc['diversification_bonus'] = diversification_multiplier - 1
    
    return profit_calculations


def rank_by_composite_score(
    profit_calculations: List[Dict[str, Any]],
    profit_weight: float = 0.4,
    roi_weight: float = 0.3,
    suitability_weight: float = 0.3
) -> List[Dict[str, Any]]:
    """
    Rank crops by composite score combining multiple factors.
    
    Args:
        profit_calculations: List of profit calculation dictionaries
        profit_weight: Weight for profit component (0-1)
        roi_weight: Weight for ROI component (0-1)
        suitability_weight: Weight for suitability component (0-1)
    
    Returns:
        Sorted list by composite score (highest first)
    """
    if not profit_calculations:
        return []
    
    # Normalize weights
    total_weight = profit_weight + roi_weight + suitability_weight
    profit_weight /= total_weight
    roi_weight /= total_weight
    suitability_weight /= total_weight
    
    # Get min/max values for normalization
    profits = [calc['net_profit'] for calc in profit_calculations]
    rois = [calc['roi_percent'] for calc in profit_calculations]
    penalties = [calc['yield_penalty_factors']['total_penalty'] for calc in profit_calculations]
    
    min_profit, max_profit = min(profits), max(profits)
    min_roi, max_roi = min(rois), max(rois)
    min_penalty, max_penalty = min(penalties), max(penalties)
    
    # Calculate composite scores
    for calc in profit_calculations:
        # Normalize components to 0-1 scale
        profit_norm = (calc['net_profit'] - min_profit) / (max_profit - min_profit) if max_profit != min_profit else 0
        roi_norm = (calc['roi_percent'] - min_roi) / (max_roi - min_roi) if max_roi != min_roi else 0
        suitability_norm = 1 - ((calc['yield_penalty_factors']['total_penalty'] - min_penalty) / 
                               (max_penalty - min_penalty)) if max_penalty != min_penalty else 1
        
        # Calculate weighted composite score
        composite_score = (profit_norm * profit_weight + 
                          roi_norm * roi_weight + 
                          suitability_norm * suitability_weight)
        
        calc['composite_score'] = composite_score
    
    return sorted(profit_calculations, key=lambda x: x['composite_score'], reverse=True)
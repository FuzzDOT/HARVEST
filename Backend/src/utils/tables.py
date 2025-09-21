"""
Table formatting utilities for pretty-printing results as ASCII/Markdown tables.
"""

from typing import List, Dict, Any, Optional
from tabulate import tabulate


def format_recommendations_table(recommendations: List[Dict[str, Any]]) -> str:
    """
    Format crop recommendations as a pretty table.
    
    Args:
        recommendations: List of recommendation dictionaries
    
    Returns:
        Formatted table string
    """
    if not recommendations:
        return "No recommendations available."
    
    # Prepare table data
    headers = ["Rank", "Crop", "Profit/Acre", "ROI %", "Yield", "Fertilizer", "Confidence %"]
    rows = []
    
    for rec in recommendations:
        fertilizer = rec.get('fertilizer_used', 'None')
        # Truncate long fertilizer names for better table formatting
        if fertilizer and len(fertilizer) > 20:
            fertilizer = fertilizer[:17] + "..."
        
        rows.append([
            rec.get('rank', '?'),
            rec.get('crop_name', 'Unknown'),
            f"${rec.get('net_profit', 0):.2f}",
            f"{rec.get('roi_percent', 0):.1f}%",
            f"{rec.get('adjusted_yield', 0):.1f}",
            fertilizer or 'None',
            f"{rec.get('recommendation_confidence', 0):.1f}%"
        ])
    
    return tabulate(rows, headers=headers, tablefmt="grid")


def format_annual_plan_table(rotation_sequence: List[Dict[str, Any]]) -> str:
    """
    Format annual crop rotation plan as a table.
    
    Args:
        rotation_sequence: List of monthly crop plans
    
    Returns:
        Formatted table string
    """
    if not rotation_sequence:
        return "No rotation plan available."
    
    headers = ["Month", "Crop", "Profit/Acre", "ROI %", "Fertilizer", "Notes"]
    rows = []
    
    for plan in rotation_sequence:
        fertilizer = plan.get('fertilizer_used', 'None')
        # Truncate long fertilizer names for better table formatting
        if fertilizer and len(fertilizer) > 15:
            fertilizer = fertilizer[:12] + "..."
            
        notes = plan.get('rotation_notes', '')
        # Truncate long notes
        if len(notes) > 25:
            notes = notes[:22] + "..."
            
        rows.append([
            f"{plan['month']:2d} - {plan['month_name'][:3]}",
            plan.get('crop_name', 'None'),
            f"${plan.get('profit_per_acre', 0):.2f}",
            f"{plan.get('roi_percent', 0):.1f}%",
            fertilizer,
            notes
        ])
    
    return tabulate(rows, headers=headers, tablefmt="grid")


def format_crop_comparison_table(crops: List[Dict[str, Any]]) -> str:
    """
    Format crop comparison table showing key metrics.
    
    Args:
        crops: List of crop dictionaries with profit calculations
    
    Returns:
        Formatted table string
    """
    if not crops:
        return "No crops to compare."
    
    headers = ["Crop", "Base Yield", "Adj. Yield", "Profit/Acre", "ROI %", "Suitability"]
    rows = []
    
    for crop in crops:
        penalty_factors = crop.get('yield_penalty_factors', {})
        suitability = (1 - penalty_factors.get('total_penalty', 0)) * 100
        
        rows.append([
            crop.get('crop_name', 'Unknown'),
            f"{crop.get('base_yield', 0):.1f}",
            f"{crop.get('adjusted_yield', 0):.1f}",
            f"${crop.get('net_profit', 0):.2f}",
            f"{crop.get('roi_percent', 0):.1f}%",
            f"{suitability:.1f}%"
        ])
    
    return tabulate(rows, headers=headers, tablefmt="grid")


def format_weather_conditions_table(weather_data: Dict[str, Any]) -> str:
    """
    Format weather conditions as a simple table.
    
    Args:
        weather_data: Weather conditions dictionary
    
    Returns:
        Formatted table string
    """
    if not weather_data:
        return "No weather data available."
    
    rows = [
        ["Temperature", f"{weather_data.get('temperature', 'N/A')}°F"],
        ["Rainfall", f"{weather_data.get('rainfall', 'N/A')} inches"],
        ["Confidence", f"{weather_data.get('confidence', 'N/A')}%"],
        ["Forecast Days", f"{weather_data.get('forecast_days', 'N/A')}"]
    ]
    
    return tabulate(rows, headers=["Metric", "Value"], tablefmt="simple")


def format_parcel_summary_table(parcels_data: List[Dict[str, Any]]) -> str:
    """
    Format parcel summary information as a table.
    
    Args:
        parcels_data: List of parcel information dictionaries
    
    Returns:
        Formatted table string
    """
    if not parcels_data:
        return "No parcel data available."
    
    headers = ["Parcel ID", "Region", "Acreage", "Soil pH", "Soil Type"]
    rows = []
    
    for parcel in parcels_data:
        rows.append([
            parcel.get('parcel_id', 'Unknown'),
            parcel.get('region', 'Unknown'),
            f"{parcel.get('acreage', 0):.1f}",
            f"{parcel.get('soil_ph', 0):.1f}",
            parcel.get('soil_type', 'Unknown')
        ])
    
    return tabulate(rows, headers=headers, tablefmt="grid")


def format_profit_breakdown_table(profit_calc: Dict[str, Any]) -> str:
    """
    Format detailed profit breakdown as a table.
    
    Args:
        profit_calc: Profit calculation dictionary
    
    Returns:
        Formatted table string
    """
    if not profit_calc:
        return "No profit calculation available."
    
    costs = profit_calc.get('production_costs', {})
    penalties = profit_calc.get('yield_penalty_factors', {})
    
    rows = [
        ["Revenue", f"${profit_calc.get('gross_revenue', 0):.2f}"],
        ["Base Costs", f"${costs.get('base_cost', 0):.2f}"],
        ["Fertilizer Costs", f"${costs.get('fertilizer_cost', 0):.2f}"],
        ["Total Costs", f"${costs.get('total_cost', 0):.2f}"],
        ["Net Profit", f"${profit_calc.get('net_profit', 0):.2f}"],
        ["", ""],  # Separator
        ["Base Yield", f"{profit_calc.get('base_yield', 0):.1f}"],
        ["Adjusted Yield", f"{profit_calc.get('adjusted_yield', 0):.1f}"],
        ["Temperature Penalty", f"{penalties.get('temperature_penalty', 0)*100:.1f}%"],
        ["Rainfall Penalty", f"{penalties.get('rainfall_penalty', 0)*100:.1f}%"],
        ["Soil pH Penalty", f"{penalties.get('soil_ph_penalty', 0)*100:.1f}%"],
        ["Total Penalty", f"{penalties.get('total_penalty', 0)*100:.1f}%"]
    ]
    
    return tabulate(rows, headers=["Metric", "Value"], tablefmt="simple")


def format_fertilizer_recommendations_table(fertilizers: List[Dict[str, Any]]) -> str:
    """
    Format fertilizer recommendations as a table.
    
    Args:
        fertilizers: List of fertilizer recommendation dictionaries
    
    Returns:
        Formatted table string
    """
    if not fertilizers:
        return "No fertilizer recommendations available."
    
    headers = ["Timing", "Month", "Fertilizer", "N-P-K", "Rate (lbs)", "Cost/Acre"]
    rows = []
    
    for fert in fertilizers:
        fertilizer_info = fert.get('fertilizer', {})
        npk = f"{fertilizer_info.get('nitrogen_percent', 0)}-{fertilizer_info.get('phosphorus_percent', 0)}-{fertilizer_info.get('potassium_percent', 0)}"
        
        rows.append([
            fert.get('timing', 'Unknown'),
            fert.get('month', '?'),
            fertilizer_info.get('name', 'Unknown'),
            npk,
            f"{fert.get('application_rate', 0):.1f}",
            f"${fert.get('cost_per_acre', 0):.2f}"
        ])
    
    return tabulate(rows, headers=headers, tablefmt="grid")


def format_markdown_table(data: List[Dict[str, Any]], headers: List[str]) -> str:
    """
    Format data as a Markdown table.
    
    Args:
        data: List of data dictionaries
        headers: List of column headers
    
    Returns:
        Markdown formatted table string
    """
    if not data or not headers:
        return "No data available."
    
    # Extract rows based on headers
    rows = []
    for item in data:
        row = [str(item.get(header.lower().replace(' ', '_'), '')) for header in headers]
        rows.append(row)
    
    return tabulate(rows, headers=headers, tablefmt="pipe")


def format_csv_output(data: List[Dict[str, Any]], headers: Optional[List[str]] = None) -> str:
    """
    Format data as CSV output.
    
    Args:
        data: List of data dictionaries
        headers: Optional list of headers (if None, uses keys from first item)
    
    Returns:
        CSV formatted string
    """
    if not data:
        return ""
    
    if headers is None:
        headers = list(data[0].keys())
    
    # Create CSV content
    csv_lines = [','.join(headers)]
    
    for item in data:
        row_values = [str(item.get(header, '')) for header in headers]
        csv_lines.append(','.join(row_values))
    
    return '\n'.join(csv_lines)


def format_summary_statistics(data: List[Dict[str, Any]], metric_key: str) -> str:
    """
    Format summary statistics for a numeric metric.
    
    Args:
        data: List of data dictionaries
        metric_key: Key for the numeric metric to summarize
    
    Returns:
        Formatted summary statistics string
    """
    if not data:
        return "No data available for statistics."
    
    values = [item.get(metric_key, 0) for item in data if metric_key in item]
    
    if not values:
        return f"No values found for metric: {metric_key}"
    
    stats = {
        'Count': len(values),
        'Mean': sum(values) / len(values),
        'Min': min(values),
        'Max': max(values),
        'Range': max(values) - min(values)
    }
    
    rows = [[key, f"{value:.2f}" if isinstance(value, float) else str(value)] 
            for key, value in stats.items()]
    
    return tabulate(rows, headers=["Statistic", "Value"], tablefmt="simple")
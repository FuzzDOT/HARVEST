"""
Data loading utilities for CSV files.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional
from ..config import (
    CROPS_CSV, FERTILIZERS_CSV, PRICE_HISTORY_CSV,
    WEATHER_NORMALS_CSV, WEATHER_FORECAST_CSV, PARCELS_CSV,
    CROP_IMAGES_CSV, PROFIT_GRAPHS_CSV
)


def load_crops() -> pd.DataFrame:
    """Load crop specifications from CSV."""
    return pd.read_csv(CROPS_CSV)


def load_fertilizers() -> pd.DataFrame:
    """Load fertilizer specifications from CSV."""
    df = pd.read_csv(FERTILIZERS_CSV)
    # Add valid_months column (assume all fertilizers can be used year-round for now)
    # This can be updated based on fertilizer type and compatibility
    df['valid_months'] = df.apply(lambda x: list(range(1, 13)), axis=1)  # All months 1-12
    return df


def load_price_history() -> pd.DataFrame:
    """Load historical crop prices from CSV."""
    return pd.read_csv(PRICE_HISTORY_CSV)


def load_weather_normals() -> pd.DataFrame:
    """Load 10-year weather averages from CSV."""
    return pd.read_csv(WEATHER_NORMALS_CSV)


def load_weather_forecast() -> pd.DataFrame:
    """Load current weather forecast from CSV."""
    df = pd.read_csv(WEATHER_FORECAST_CSV)
    df['date'] = pd.to_datetime(df['date'])
    return df


def load_parcels() -> pd.DataFrame:
    """Load parcel specifications from CSV."""
    return pd.read_csv(PARCELS_CSV)


def load_parcel_by_id(parcel_id: str) -> Optional[Dict[str, Any]]:
    """Load a specific parcel by ID."""
    parcels = load_parcels()
    parcel_row = parcels[parcels['parcel_id'] == parcel_id]
    
    if parcel_row.empty:
        return None
    
    return parcel_row.iloc[0].to_dict()


def load_crop_by_id(crop_name: str) -> Optional[Dict[str, Any]]:
    """Load a specific crop by name (updated to use crop_name instead of crop_id)."""
    crops = load_crops()
    crop_row = crops[crops['crop_name'] == crop_name]
    
    if crop_row.empty:
        return None
    
    return crop_row.iloc[0].to_dict()


def get_latest_price(crop_name: str, state: Optional[str] = None) -> Optional[float]:
    """Get the most recent price for a crop (updated to use crop_name and handle date format)."""
    prices = load_price_history()
    crop_prices = prices[prices['crop_name'] == crop_name]
    
    # Filter by state if provided
    if state:
        crop_prices = crop_prices[crop_prices['state'] == state]
    
    if crop_prices.empty:
        return None
    
    # Convert date to datetime and get the most recent price
    crop_prices = crop_prices.copy()
    crop_prices['date'] = pd.to_datetime(crop_prices['date'])
    latest = crop_prices.sort_values('date').iloc[-1]
    return latest['price_usd_per_lb']


def load_crop_images() -> pd.DataFrame:
    """Load crop image paths from CSV. Returns empty DataFrame if file doesn't exist."""
    try:
        return pd.read_csv(CROP_IMAGES_CSV)
    except FileNotFoundError:
        # Return empty DataFrame with expected columns if file doesn't exist
        return pd.DataFrame(columns=['crop_name', 'image_path'])


def load_profit_graphs() -> pd.DataFrame:
    """Load profit graph paths from CSV. Returns empty DataFrame if file doesn't exist."""
    try:
        return pd.read_csv(PROFIT_GRAPHS_CSV)
    except FileNotFoundError:
        # Return empty DataFrame with expected columns if file doesn't exist
        return pd.DataFrame(columns=['crop_name', 'profit_graph_path'])


def get_crop_image_path(crop_name: str) -> Optional[str]:
    """Get the image path for a specific crop (updated to use crop_name)."""
    try:
        images = load_crop_images()
        crop_image = images[images['crop_name'] == crop_name]
        
        if crop_image.empty:
            return None
        
        return crop_image.iloc[0]['image_path']
    except (FileNotFoundError, KeyError):
        return None


def get_profit_graph_path(crop_name: str) -> Optional[str]:
    """Get the profit graph path for a specific crop (updated to use crop_name)."""
    try:
        graphs = load_profit_graphs()
        crop_graph = graphs[graphs['crop_name'] == crop_name]
        
        if crop_graph.empty:
            return None
        
        return crop_graph.iloc[0]['profit_graph_path']
    except (FileNotFoundError, KeyError):
        return None
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
    # Convert comma-separated valid_months to list
    df['valid_months'] = df['valid_months'].apply(
        lambda x: [int(m) for m in x.split(',')]
    )
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


def load_crop_by_id(crop_id: str) -> Optional[Dict[str, Any]]:
    """Load a specific crop by ID."""
    crops = load_crops()
    crop_row = crops[crops['crop_id'] == crop_id]
    
    if crop_row.empty:
        return None
    
    return crop_row.iloc[0].to_dict()


def get_latest_price(crop_id: str) -> Optional[float]:
    """Get the most recent price for a crop."""
    prices = load_price_history()
    crop_prices = prices[prices['crop_id'] == crop_id]
    
    if crop_prices.empty:
        return None
    
    # Get the most recent price
    latest = crop_prices.sort_values(['year', 'month']).iloc[-1]
    return latest['price_per_unit']


def load_crop_images() -> pd.DataFrame:
    """Load crop image paths from CSV."""
    return pd.read_csv(CROP_IMAGES_CSV)


def load_profit_graphs() -> pd.DataFrame:
    """Load profit graph paths from CSV."""
    return pd.read_csv(PROFIT_GRAPHS_CSV)


def get_crop_image_path(crop_id: str) -> Optional[str]:
    """Get the image path for a specific crop."""
    images = load_crop_images()
    crop_image = images[images['crop_id'] == crop_id]
    
    if crop_image.empty:
        return None
    
    return crop_image.iloc[0]['image_path']


def get_profit_graph_path(crop_id: str) -> Optional[str]:
    """Get the profit graph path for a specific crop."""
    graphs = load_profit_graphs()
    crop_graph = graphs[graphs['crop_id'] == crop_id]
    
    if crop_graph.empty:
        return None
    
    return crop_graph.iloc[0]['profit_graph_path']
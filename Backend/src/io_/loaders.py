"""
Data loading utilities for CSV files.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional
from ..config import (
    CROPS_CSV, FERTILIZERS_CSV, PRICE_HISTORY_CSV,
    WEATHER_NORMALS_CSV, WEATHER_FORECAST_CSV, PARCELS_CSV
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
"""
Data writing utilities for saving results to CSV files.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from ..config import SHORT_TERM_OUTPUT_DIR, LONG_TERM_OUTPUT_DIR


def ensure_output_dirs():
    """Ensure output directories exist."""
    SHORT_TERM_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    LONG_TERM_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def save_short_term_recommendations(
    parcel_id: str,
    month: int,
    recommendations: List[Dict[str, Any]]
) -> Path:
    """Save monthly crop recommendations to CSV."""
    ensure_output_dirs()
    
    # Create DataFrame from recommendations
    df = pd.DataFrame(recommendations)
    
    # Add metadata columns
    df['parcel_id'] = parcel_id
    df['prediction_month'] = month
    df['generated_at'] = datetime.now().isoformat()
    
    # Create filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{parcel_id}_month_{month:02d}_{timestamp}.csv"
    output_path = SHORT_TERM_OUTPUT_DIR / filename
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    
    return output_path


def save_long_term_plan(
    parcel_id: str,
    annual_plan: List[Dict[str, Any]]
) -> Path:
    """Save annual crop rotation plan to CSV."""
    ensure_output_dirs()
    
    # Create DataFrame from annual plan
    df = pd.DataFrame(annual_plan)
    
    # Add metadata columns
    df['parcel_id'] = parcel_id
    df['generated_at'] = datetime.now().isoformat()
    
    # Create filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{parcel_id}_annual_plan_{timestamp}.csv"
    output_path = LONG_TERM_OUTPUT_DIR / filename
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    
    return output_path


def save_summary_report(
    data: Dict[str, Any],
    report_type: str = "summary"
) -> Path:
    """Save a summary report across multiple parcels."""
    ensure_output_dirs()
    
    # Determine output directory based on report type
    if "long_term" in report_type.lower():
        output_dir = LONG_TERM_OUTPUT_DIR
    else:
        output_dir = SHORT_TERM_OUTPUT_DIR
    
    # Create filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{report_type}_{timestamp}.csv"
    output_path = output_dir / filename
    
    # Convert dict to DataFrame (assuming it's structured appropriately)
    if isinstance(data, dict) and all(isinstance(v, list) for v in data.values()):
        df = pd.DataFrame(data)
    else:
        # Handle single record
        df = pd.DataFrame([data])
    
    # Add generation timestamp
    df['generated_at'] = datetime.now().isoformat()
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    
    return output_path
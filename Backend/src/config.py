"""
Configuration constants, paths, and thresholds for the HARVEST system.
"""

import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUTS_DIR = BASE_DIR / "outputs"

# Data file paths
CROPS_CSV = DATA_DIR / "crops.csv"
FERTILIZERS_CSV = DATA_DIR / "fertilizers.csv"
PRICE_HISTORY_CSV = DATA_DIR / "price_history.csv"
WEATHER_NORMALS_CSV = DATA_DIR / "weather_monthly_normals.csv"
WEATHER_FORECAST_CSV = DATA_DIR / "weather_forecast.csv"
PARCELS_CSV = DATA_DIR / "parcels.csv"

# Output directories
SHORT_TERM_OUTPUT_DIR = OUTPUTS_DIR / "short_term"
LONG_TERM_OUTPUT_DIR = OUTPUTS_DIR / "long_term"

# Agricultural thresholds and constants
IDEAL_TEMP_TOLERANCE = 5.0  # degrees F tolerance from ideal range
IDEAL_RAIN_TOLERANCE = 5.0  # inches tolerance from ideal range

# Penalty factors for deviations from ideal conditions
TEMP_PENALTY_FACTOR = 0.02  # 2% yield reduction per degree outside ideal range
RAIN_PENALTY_FACTOR = 0.03  # 3% yield reduction per inch outside ideal range

# Maximum penalty caps (to prevent negative yields)
MAX_TEMP_PENALTY = 0.5  # Maximum 50% yield reduction from temperature
MAX_RAIN_PENALTY = 0.4  # Maximum 40% yield reduction from rainfall

# Soil pH preferences
IDEAL_SOIL_PH_MIN = 6.0
IDEAL_SOIL_PH_MAX = 7.0
SOIL_PH_PENALTY_FACTOR = 0.05  # 5% yield reduction per pH unit outside ideal range

# Economic factors
PROFIT_THRESHOLD = 0.0  # Minimum profit per acre to recommend a crop
FERTILIZER_APPLICATION_RATE = 100  # lbs per acre (default)

# Weather confidence thresholds
MIN_WEATHER_CONFIDENCE = 70  # Only use forecasts with 70%+ confidence

# Date formatting
DATE_FORMAT = "%Y-%m-%d"
MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]
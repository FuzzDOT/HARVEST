# HARVEST Backend

Agricultural yield prediction and crop recommendation system for precision farming.

## Overview

This backend system provides data-driven crop recommendations based on:

- Weather forecasts and historical patterns
- Soil conditions and parcel characteristics
- Crop specifications and growth requirements
- Fertilizer availability and pricing
- Market price history

## Installation

1. Install Python dependencies:

```bash
pip install -r requirements.txt
```

## Quick Start

### FastAPI Web Server

Start the REST API server:

```bash
# Start the FastAPI server
python main.py

# Or using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:

- **API Base URL**: <http://localhost:8000>
- **Interactive Docs**: <http://localhost:8000/docs>
- **ReDoc**: <http://localhost:8000/redoc>

### Monthly Predictions (Short-term)

Get crop recommendations for a specific month using current weather forecasts:

```bash
# Via API (POST request)
curl -X POST "http://localhost:8000/api/v1/predict/month" \
  -H "Content-Type: application/json" \
  -d '{
    "parcel_id": "P1",
    "month": 9,
    "top_n": 5,
    "ranking_method": "profit"
  }'

# Via CLI
python -m src.cli.predict_month --parcel P1 --month 9

# Predict for multiple parcels
python -m src.cli.predict_month --parcel P2 --month 10
```

### Annual Planning (Long-term)

Generate a 12-month crop rotation plan using historical weather averages:

```bash
# Via API (POST request)
curl -X POST "http://localhost:8000/api/v1/plan/annual" \
  -H "Content-Type: application/json" \
  -d '{
    "parcel_id": "P1",
    "start_month": 1,
    "diversification_bonus": 0.1
  }'

# Via CLI
python -m src.cli.plan_year --parcel P1

# Generate plans for all parcels
python -m src.cli.plan_year --all
```

## Data Requirements

Place your CSV files in the `data/` directory:

- `crops.csv` - Crop specifications and requirements
- `fertilizers.csv` - Available fertilizers and pricing
- `price_history.csv` - Historical crop market prices
- `weather_monthly_normals.csv` - 10-year weather averages
- `weather_forecast.csv` - Current month weather forecast
- `parcels.csv` - Farm parcel characteristics

## Output

Results are saved to the `outputs/` directory:

- `short_term/` - Monthly recommendations
- `long_term/` - Annual planning results

## Sample Commands

```bash
# Get recommendations for current month
python -m src.cli.predict_month --parcel P1 --month $(date +%m)

# Plan next growing season
python -m src.cli.plan_year --parcel P1 --start-month 3

# Generate reports for all parcels
python -m src.cli.predict_month --all --month 9
```

## Development

Run tests:

```bash
python -m pytest tests/
```

## Architecture

- `src/io_/` - Data loading and saving utilities
- `src/rules/` - Agricultural business rules
- `src/model/` - Yield prediction and profit calculations
- `src/pipelines/` - Main prediction workflows
- `src/cli/` - Command-line interfaces
- `src/utils/` - Helper functions

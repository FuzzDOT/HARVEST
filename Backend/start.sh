#!/bin/bash

# HARVEST Backend Startup Script
echo "🌾 Starting HARVEST Agricultural Prediction API..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    echo "Loading environment variables from .env file..."
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "⚠️  No .env file found. Create one with your OPENAI_API_KEY"
fi

# Create output directories if they don't exist
mkdir -p outputs/short_term
mkdir -p outputs/long_term

echo "✅ Setup complete!"
echo ""
echo "🚀 Starting FastAPI server..."
echo "📊 API Documentation: http://localhost:8000/docs"
echo "📈 API Base URL: http://localhost:8000"
echo ""

# Start the server
python main.py
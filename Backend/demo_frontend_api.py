#!/usr/bin/env python3
"""
Demo script for the new HARVEST frontend integration APIs.
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_location_prediction():
    """Test the main location-based prediction endpoint."""
    print("🌾 Testing Location-Based Prediction API")
    print("=" * 50)
    
    # Sample request data
    request_data = {
        "location": {
            "latitude": 40.7128,
            "longitude": -74.0060
        },
        "timezone": "America/New_York",
        "prediction_type": "short_term"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/predict/location",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            session_id = result.get('session_id')
            
            print(f"✅ Prediction successful! Session ID: {session_id}")
            print("\n📊 Top 5 Crop Recommendations:")
            
            for i in range(1, 6):
                crop_name = result.get(f'cropName{i}')
                crop_price = result.get(f'cropPrice{i}')
                fertilizer_name = result.get(f'fertilizerName{i}')
                fertilizer_price = result.get(f'fertilizerPrice{i}')
                net_profit = result.get(f'netProfit{i}')
                
                if crop_name:
                    print(f"  {i}. {crop_name} (${crop_price:.2f}/unit)")
                    print(f"     Fertilizer: {fertilizer_name} (${fertilizer_price:.2f})")
                    print(f"     Net Profit: ${net_profit:.2f}/acre")
                    print()
            
            return session_id
            
        else:
            print(f"❌ Prediction failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server. Is it running?")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_individual_apis(session_id):
    """Test the individual result APIs."""
    if not session_id:
        print("⚠️ No session ID available for individual API tests")
        return
        
    print("\n🔍 Testing Individual Result APIs")
    print("=" * 50)
    
    # Test different individual endpoints
    endpoints = [
        ("crop", f"/api/v1/results/crop/{session_id}/1"),
        ("price", f"/api/v1/results/price/{session_id}/1"),
        ("fertilizer", f"/api/v1/results/fertilizer/{session_id}/1"),
        ("fertilizer-price", f"/api/v1/results/fertilizer-price/{session_id}/1"),
        ("image", f"/api/v1/results/image/{session_id}/1")
    ]
    
    for name, endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}")
            if response.status_code == 200:
                result = response.json()
                print(f"✅ {name}: {result}")
            else:
                print(f"❌ {name} failed: {response.status_code}")
        except Exception as e:
            print(f"❌ {name} error: {e}")


def main():
    """Run all tests."""
    print("🌾 HARVEST Frontend Integration API Demo")
    print("=" * 60)
    
    # Test main prediction endpoint
    session_id = test_location_prediction()
    
    # Test individual result endpoints
    test_individual_apis(session_id)
    
    print("\n" + "=" * 60)
    print("Demo complete! Check the API documentation at:")
    print("📖 http://localhost:8000/docs")


if __name__ == "__main__":
    main()
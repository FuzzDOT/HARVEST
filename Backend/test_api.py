#!/usr/bin/env python3
"""
Test script for HARVEST FastAPI endpoints.
Run this script to test the API functionality.
"""

import requests
import json
import sys
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test the health check endpoint."""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server. Is it running?")
        return False

def test_get_parcels():
    """Test getting all parcels."""
    print("🔍 Testing get parcels...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/parcels")
        if response.status_code == 200:
            parcels = response.json()
            print(f"✅ Retrieved {len(parcels)} parcels")
            return True
        else:
            print(f"❌ Get parcels failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Get parcels error: {e}")
        return False

def test_get_crops():
    """Test getting all crops."""
    print("🔍 Testing get crops...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/crops")
        if response.status_code == 200:
            crops = response.json()
            print(f"✅ Retrieved {len(crops)} crops")
            return True
        else:
            print(f"❌ Get crops failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Get crops error: {e}")
        return False

def test_monthly_prediction():
    """Test monthly crop prediction."""
    print("🔍 Testing monthly prediction...")
    try:
        payload = {
            "parcel_id": "P1",
            "month": 9,
            "top_n": 3,
            "ranking_method": "profit",
            "min_confidence": 70.0
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/predict/month",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            recommendations = result.get('recommendations', [])
            print(f"✅ Monthly prediction returned {len(recommendations)} recommendations")
            if recommendations:
                best = recommendations[0]
                print(f"   Best crop: {best.get('crop_name')} (${best.get('net_profit', 0):.2f}/acre)")
            return True
        else:
            print(f"❌ Monthly prediction failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Monthly prediction error: {e}")
        return False

def test_annual_planning():
    """Test annual crop planning."""
    print("🔍 Testing annual planning...")
    try:
        payload = {
            "parcel_id": "P1",
            "start_month": 1,
            "diversification_bonus": 0.1,
            "min_profit_threshold": 0.0
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/plan/annual",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            months_planned = result.get('total_months_planned', 0)
            annual_profit = result.get('annual_summary', {}).get('total_annual_profit_per_acre', 0)
            print(f"✅ Annual planning returned {months_planned} months planned")
            print(f"   Annual profit potential: ${annual_profit:.2f}/acre")
            return True
        else:
            print(f"❌ Annual planning failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Annual planning error: {e}")
        return False

def test_profit_calculation():
    """Test profit calculation."""
    print("🔍 Testing profit calculation...")
    try:
        payload = {
            "crop_id": "CORN",
            "weather_conditions": {
                "temperature": 75.0,
                "rainfall": 25.0,
                "confidence": 85.0
            },
            "soil_ph": 6.5,
            "month": 6
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/calculate/profit",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            profit = result.get('net_profit', 0)
            roi = result.get('roi_percent', 0)
            print(f"✅ Profit calculation successful")
            print(f"   Profit: ${profit:.2f}/acre, ROI: {roi:.1f}%")
            return True
        else:
            print(f"❌ Profit calculation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Profit calculation error: {e}")
        return False

def test_system_summary():
    """Test system summary."""
    print("🔍 Testing system summary...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/summary/system")
        if response.status_code == 200:
            result = response.json()
            data_summary = result.get('data_summary', {})
            parcels_count = data_summary.get('parcels', {}).get('count', 0)
            crops_count = data_summary.get('crops', {}).get('count', 0)
            print(f"✅ System summary retrieved")
            print(f"   {parcels_count} parcels, {crops_count} crops available")
            return True
        else:
            print(f"❌ System summary failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ System summary error: {e}")
        return False

def main():
    """Run all tests."""
    print("🌾 HARVEST API Test Suite")
    print("=" * 50)
    
    tests = [
        test_health_check,
        test_get_parcels,
        test_get_crops,
        test_monthly_prediction,
        test_annual_planning,
        test_profit_calculation,
        test_system_summary
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! API is working correctly.")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed. Check the API server and data files.")
        sys.exit(1)

if __name__ == "__main__":
    main()
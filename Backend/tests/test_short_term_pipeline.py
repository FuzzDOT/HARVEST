"""
Unit tests for short-term prediction pipeline.
"""

import unittest
from unittest.mock import patch, MagicMock
from src.pipelines.predict_short_term import (
    predict_month_recommendations,
    get_monthly_weather_forecast,
    calculate_recommendation_confidence
)


class TestShortTermPipeline(unittest.TestCase):
    """Test cases for short-term prediction pipeline."""
    
    def setUp(self):
        """Set up test data."""
        self.parcel = {
            'parcel_id': 'P1',
            'region': 'MIDWEST',
            'acreage': 150,
            'soil_ph': 6.5,
            'soil_type': 'loam'
        }
        
        self.crop = {
            'crop_id': 'CORN',
            'name': 'Corn',
            'growth_window_start': 3,
            'growth_window_end': 6,
            'ideal_temp_min': 60,
            'ideal_temp_max': 80,
            'ideal_rain_min': 20,
            'ideal_rain_max': 30,
            'base_yield_per_acre': 150,
            'cost_per_acre': 300
        }
        
        self.weather_forecast = {
            'temperature': 70.0,
            'rainfall': 25.0,
            'confidence': 85.0,
            'forecast_days': 10
        }
        
        self.profit_calculation = {
            'crop_id': 'CORN',
            'crop_name': 'Corn',
            'net_profit': 400.0,
            'roi_percent': 80.0,
            'adjusted_yield': 140.0,
            'yield_penalty_factors': {
                'temperature_penalty': 0.0,
                'rainfall_penalty': 0.0,
                'soil_ph_penalty': 0.0,
                'total_penalty': 0.0
            }
        }
    
    @patch('src.pipelines.predict_short_term.load_parcel_by_id')
    @patch('src.pipelines.predict_short_term.filter_crops_by_month')
    @patch('src.pipelines.predict_short_term.get_monthly_weather_forecast')
    @patch('src.pipelines.predict_short_term.calculate_net_profit')
    @patch('src.pipelines.predict_short_term.get_top_n_recommendations')
    def test_predict_month_recommendations_success(self, mock_top_n, mock_calc_profit,
                                                 mock_weather, mock_filter_crops, mock_load_parcel):
        """Test successful month recommendations prediction."""
        # Mock dependencies
        mock_load_parcel.return_value = self.parcel
        mock_filter_crops.return_value = [self.crop]
        mock_weather.return_value = self.weather_forecast
        mock_calc_profit.return_value = self.profit_calculation
        mock_top_n.return_value = [self.profit_calculation]
        
        result = predict_month_recommendations(
            parcel_id='P1',
            month=5,
            top_n=3
        )
        
        # Verify function calls
        mock_load_parcel.assert_called_once_with('P1')
        mock_filter_crops.assert_called_once_with(5)
        mock_weather.assert_called_once_with('MIDWEST', 5, 70.0)
        mock_calc_profit.assert_called_once()
        mock_top_n.assert_called_once()
        
        # Verify result structure
        self.assertEqual(result['parcel_id'], 'P1')
        self.assertEqual(result['month'], 5)
        self.assertEqual(result['region'], 'MIDWEST')
        self.assertEqual(len(result['recommendations']), 1)
        self.assertEqual(result['total_crops_evaluated'], 1)
        self.assertIn('generated_at', result)
    
    @patch('src.pipelines.predict_short_term.load_parcel_by_id')
    def test_predict_month_recommendations_parcel_not_found(self, mock_load_parcel):
        """Test prediction when parcel is not found."""
        mock_load_parcel.return_value = None
        
        with self.assertRaises(ValueError) as context:
            predict_month_recommendations('INVALID', 5)
        
        self.assertIn("Parcel INVALID not found", str(context.exception))
    
    @patch('src.pipelines.predict_short_term.load_parcel_by_id')
    @patch('src.pipelines.predict_short_term.filter_crops_by_month')
    def test_predict_month_recommendations_no_eligible_crops(self, mock_filter_crops, mock_load_parcel):
        """Test prediction when no crops are eligible."""
        mock_load_parcel.return_value = self.parcel
        mock_filter_crops.return_value = []
        
        result = predict_month_recommendations('P1', 12)  # Month with no crops
        
        self.assertEqual(result['parcel_id'], 'P1')
        self.assertEqual(result['month'], 12)
        self.assertEqual(result['recommendations'], [])
        self.assertIn('No crops are eligible', result['message'])
    
    @patch('src.pipelines.predict_short_term.load_parcel_by_id')
    @patch('src.pipelines.predict_short_term.filter_crops_by_month')
    @patch('src.pipelines.predict_short_term.get_monthly_weather_forecast')
    def test_predict_month_recommendations_no_weather_data(self, mock_weather, mock_filter_crops, mock_load_parcel):
        """Test prediction when no weather data is available."""
        mock_load_parcel.return_value = self.parcel
        mock_filter_crops.return_value = [self.crop]
        mock_weather.return_value = None
        
        result = predict_month_recommendations('P1', 5)
        
        self.assertEqual(result['recommendations'], [])
        self.assertIn('No reliable weather forecast', result['message'])
    
    @patch('src.pipelines.predict_short_term.load_weather_forecast')
    def test_get_monthly_weather_forecast_success(self, mock_load_forecast):
        """Test successful weather forecast retrieval."""
        import pandas as pd
        from datetime import datetime
        
        # Mock weather data
        mock_weather_df = pd.DataFrame([
            {
                'region': 'MIDWEST',
                'date': datetime(2025, 5, 1),
                'forecast_temp_f': 68,
                'forecast_rainfall_inches': 0.2,
                'confidence_percent': 85
            },
            {
                'region': 'MIDWEST',
                'date': datetime(2025, 5, 2),
                'forecast_temp_f': 72,
                'forecast_rainfall_inches': 0.3,
                'confidence_percent': 80
            }
        ])
        mock_load_forecast.return_value = mock_weather_df
        
        result = get_monthly_weather_forecast('MIDWEST', 5, min_confidence=75)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['temperature'], 70.0)  # Average of 68, 72
        self.assertEqual(result['rainfall'], 0.5)  # Sum of 0.2, 0.3
        self.assertEqual(result['confidence'], 82.5)  # Average of 85, 80
        self.assertEqual(result['forecast_days'], 2)
    
    @patch('src.pipelines.predict_short_term.load_weather_forecast')
    def test_get_monthly_weather_forecast_no_data(self, mock_load_forecast):
        """Test weather forecast retrieval with no data."""
        import pandas as pd
        
        mock_load_forecast.return_value = pd.DataFrame()  # Empty DataFrame
        
        result = get_monthly_weather_forecast('UNKNOWN_REGION', 5)
        
        self.assertIsNone(result)
    
    @patch('src.pipelines.predict_short_term.load_weather_forecast')
    def test_get_monthly_weather_forecast_low_confidence(self, mock_load_forecast):
        """Test weather forecast retrieval with low confidence data."""
        import pandas as pd
        from datetime import datetime
        
        # Mock low confidence weather data
        mock_weather_df = pd.DataFrame([
            {
                'region': 'MIDWEST',
                'date': datetime(2025, 5, 1),
                'forecast_temp_f': 68,
                'forecast_rainfall_inches': 0.2,
                'confidence_percent': 50  # Below threshold
            }
        ])
        mock_load_forecast.return_value = mock_weather_df
        
        result = get_monthly_weather_forecast('MIDWEST', 5, min_confidence=70)
        
        self.assertIsNone(result)  # Should return None due to low confidence
    
    def test_calculate_recommendation_confidence(self):
        """Test recommendation confidence calculation."""
        weather_data = {
            'confidence': 85.0
        }
        
        recommendation = {
            'yield_penalty_factors': {
                'total_penalty': 0.1  # 10% penalty
            }
        }
        
        confidence = calculate_recommendation_confidence(recommendation, weather_data)
        
        # Expected: (85 * 0.6) + (90 * 0.4) = 51 + 36 = 87
        # Where 90 = (1 - 0.1) * 100
        expected_confidence = (85 * 0.6) + (90 * 0.4)
        self.assertAlmostEqual(confidence, expected_confidence, places=1)
    
    def test_calculate_recommendation_confidence_high_penalty(self):
        """Test recommendation confidence with high yield penalty."""
        weather_data = {
            'confidence': 80.0
        }
        
        recommendation = {
            'yield_penalty_factors': {
                'total_penalty': 0.4  # 40% penalty
            }
        }
        
        confidence = calculate_recommendation_confidence(recommendation, weather_data)
        
        # Should be lower due to high penalty
        expected_confidence = (80 * 0.6) + (60 * 0.4)  # 60 = (1 - 0.4) * 100
        self.assertAlmostEqual(confidence, expected_confidence, places=1)


if __name__ == '__main__':
    unittest.main()
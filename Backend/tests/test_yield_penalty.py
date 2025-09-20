"""
Unit tests for yield penalty calculations.
"""

import unittest
from src.model.yield_penalty import (
    calculate_temperature_penalty,
    calculate_rainfall_penalty,
    calculate_soil_ph_penalty,
    calculate_total_yield_penalty,
    calculate_adjusted_yield,
    calculate_weather_suitability_score
)


class TestYieldPenalty(unittest.TestCase):
    """Test cases for yield penalty calculations."""
    
    def setUp(self):
        """Set up test data."""
        self.crop_requirements = {
            'ideal_temp_min': 60,
            'ideal_temp_max': 80,
            'ideal_rain_min': 20,
            'ideal_rain_max': 30,
            'base_yield_per_acre': 150
        }
        
        self.ideal_weather = {
            'temperature': 70.0,
            'rainfall': 25.0
        }
        
        self.ideal_soil = {
            'ph': 6.5
        }
    
    def test_temperature_penalty_ideal_conditions(self):
        """Test temperature penalty with ideal conditions."""
        penalty = calculate_temperature_penalty(
            actual_temp=70,
            ideal_temp_min=60,
            ideal_temp_max=80
        )
        self.assertEqual(penalty, 0.0)
    
    def test_temperature_penalty_too_cold(self):
        """Test temperature penalty when too cold."""
        penalty = calculate_temperature_penalty(
            actual_temp=50,  # 10 degrees below minimum
            ideal_temp_min=60,
            ideal_temp_max=80
        )
        self.assertEqual(penalty, 0.2)  # 10 * 0.02 = 0.2
    
    def test_temperature_penalty_too_hot(self):
        """Test temperature penalty when too hot."""
        penalty = calculate_temperature_penalty(
            actual_temp=90,  # 10 degrees above maximum
            ideal_temp_min=60,
            ideal_temp_max=80
        )
        self.assertEqual(penalty, 0.2)  # 10 * 0.02 = 0.2
    
    def test_temperature_penalty_capped(self):
        """Test temperature penalty is capped at maximum."""
        penalty = calculate_temperature_penalty(
            actual_temp=120,  # Extremely hot
            ideal_temp_min=60,
            ideal_temp_max=80
        )
        self.assertEqual(penalty, 0.5)  # Capped at MAX_TEMP_PENALTY
    
    def test_rainfall_penalty_ideal_conditions(self):
        """Test rainfall penalty with ideal conditions."""
        penalty = calculate_rainfall_penalty(
            actual_rain=25,
            ideal_rain_min=20,
            ideal_rain_max=30
        )
        self.assertEqual(penalty, 0.0)
    
    def test_rainfall_penalty_too_dry(self):
        """Test rainfall penalty when too dry."""
        penalty = calculate_rainfall_penalty(
            actual_rain=15,  # 5 inches below minimum
            ideal_rain_min=20,
            ideal_rain_max=30
        )
        self.assertEqual(penalty, 0.15)  # 5 * 0.03 = 0.15
    
    def test_rainfall_penalty_too_wet(self):
        """Test rainfall penalty when too wet."""
        penalty = calculate_rainfall_penalty(
            actual_rain=35,  # 5 inches above maximum
            ideal_rain_min=20,
            ideal_rain_max=30
        )
        self.assertEqual(penalty, 0.15)  # 5 * 0.03 = 0.15
    
    def test_soil_ph_penalty_ideal(self):
        """Test soil pH penalty with ideal pH."""
        penalty = calculate_soil_ph_penalty(6.5)
        self.assertEqual(penalty, 0.0)
    
    def test_soil_ph_penalty_acidic(self):
        """Test soil pH penalty with acidic soil."""
        penalty = calculate_soil_ph_penalty(5.5)  # 0.5 below minimum
        self.assertEqual(penalty, 0.025)  # 0.5 * 0.05 = 0.025
    
    def test_soil_ph_penalty_alkaline(self):
        """Test soil pH penalty with alkaline soil."""
        penalty = calculate_soil_ph_penalty(7.5)  # 0.5 above maximum
        self.assertEqual(penalty, 0.025)  # 0.5 * 0.05 = 0.025
    
    def test_total_yield_penalty_ideal_conditions(self):
        """Test total yield penalty with ideal conditions."""
        penalties = calculate_total_yield_penalty(
            self.ideal_weather,
            self.crop_requirements,
            self.ideal_soil
        )
        
        self.assertEqual(penalties['temperature_penalty'], 0.0)
        self.assertEqual(penalties['rainfall_penalty'], 0.0)
        self.assertEqual(penalties['soil_ph_penalty'], 0.0)
        self.assertEqual(penalties['total_penalty'], 0.0)
    
    def test_total_yield_penalty_compound(self):
        """Test total yield penalty with multiple factors."""
        poor_weather = {'temperature': 50.0, 'rainfall': 15.0}  # Both suboptimal
        poor_soil = {'ph': 5.5}  # Acidic
        
        penalties = calculate_total_yield_penalty(
            poor_weather,
            self.crop_requirements,
            poor_soil
        )
        
        # Individual penalties should be non-zero
        self.assertGreater(penalties['temperature_penalty'], 0)
        self.assertGreater(penalties['rainfall_penalty'], 0)
        self.assertGreater(penalties['soil_ph_penalty'], 0)
        
        # Total penalty should be compound, not additive
        expected_total = 1 - ((1 - penalties['temperature_penalty']) * 
                             (1 - penalties['rainfall_penalty']) * 
                             (1 - penalties['soil_ph_penalty']))
        self.assertAlmostEqual(penalties['total_penalty'], expected_total, places=5)
    
    def test_adjusted_yield_calculation(self):
        """Test adjusted yield calculation."""
        penalty_factors = {
            'total_penalty': 0.2  # 20% penalty
        }
        
        adjusted_yield = calculate_adjusted_yield(150, penalty_factors)
        self.assertEqual(adjusted_yield, 120)  # 150 * (1 - 0.2) = 120
    
    def test_weather_suitability_score_perfect(self):
        """Test weather suitability score with perfect conditions."""
        score = calculate_weather_suitability_score(
            self.ideal_weather,
            self.crop_requirements
        )
        self.assertEqual(score, 100.0)
    
    def test_weather_suitability_score_poor(self):
        """Test weather suitability score with poor conditions."""
        poor_weather = {'temperature': 40.0, 'rainfall': 10.0}  # Very poor
        
        score = calculate_weather_suitability_score(
            poor_weather,
            self.crop_requirements
        )
        self.assertLess(score, 70.0)  # Should be low score (adjusted from 50 to 70)


if __name__ == '__main__':
    unittest.main()
"""
Unit tests for profit calculations.
"""

import unittest
from unittest.mock import patch, MagicMock
from src.model.profit_calc import (
    calculate_gross_revenue,
    calculate_production_costs,
    calculate_net_profit,
    calculate_profit_margin,
    calculate_break_even_yield
)


class TestProfitCalc(unittest.TestCase):
    """Test cases for profit calculations."""
    
    def setUp(self):
        """Set up test data."""
        self.crop = {
            'crop_id': 'CORN',
            'name': 'Corn',
            'cost_per_acre': 300,
            'base_yield_per_acre': 150,
            'ideal_temp_min': 60,
            'ideal_temp_max': 80,
            'ideal_rain_min': 20,
            'ideal_rain_max': 30
        }
        
        self.fertilizer = {
            'name': 'Balanced NPK',
            'price_per_lb': 0.50,
            'nitrogen_percent': 10,
            'phosphorus_percent': 10,
            'potassium_percent': 10
        }
        
        self.weather_conditions = {
            'temperature': 70.0,
            'rainfall': 25.0
        }
        
        self.soil_conditions = {
            'ph': 6.5
        }
    
    def test_calculate_gross_revenue(self):
        """Test gross revenue calculation."""
        revenue = calculate_gross_revenue(
            crop=self.crop,
            adjusted_yield=120,
            price_per_unit=5.50
        )
        self.assertEqual(revenue, 660.0)  # 120 * 5.50 = 660
    
    @patch('src.model.profit_calc.get_latest_price')
    def test_calculate_gross_revenue_with_price_lookup(self, mock_get_price):
        """Test gross revenue calculation with price lookup."""
        mock_get_price.return_value = 6.00
        
        revenue = calculate_gross_revenue(
            crop=self.crop,
            adjusted_yield=100
        )
        
        mock_get_price.assert_called_once_with('CORN')
        self.assertEqual(revenue, 600.0)  # 100 * 6.00 = 600
    
    @patch('src.model.profit_calc.get_latest_price')
    def test_calculate_gross_revenue_no_price_data(self, mock_get_price):
        """Test gross revenue calculation when no price data available."""
        mock_get_price.return_value = None
        
        with self.assertRaises(ValueError) as context:
            calculate_gross_revenue(
                crop=self.crop,
                adjusted_yield=100
            )
        
        self.assertIn("No price data available", str(context.exception))
    
    def test_calculate_production_costs_no_fertilizer(self):
        """Test production costs calculation without fertilizer."""
        costs = calculate_production_costs(self.crop)
        
        expected = {
            'base_cost': 300,
            'fertilizer_cost': 0.0,
            'total_cost': 300
        }
        self.assertEqual(costs, expected)
    
    def test_calculate_production_costs_with_fertilizer(self):
        """Test production costs calculation with fertilizer."""
        costs = calculate_production_costs(
            self.crop,
            self.fertilizer,
            fertilizer_rate=100
        )
        
        expected = {
            'base_cost': 300,
            'fertilizer_cost': 50.0,  # 100 lbs * $0.50/lb = $50
            'total_cost': 350
        }
        self.assertEqual(costs, expected)
    
    @patch('src.model.profit_calc.calculate_total_yield_penalty')
    @patch('src.model.profit_calc.calculate_adjusted_yield')
    @patch('src.model.profit_calc.get_best_fertilizer_for_crop')
    @patch('src.model.profit_calc.get_latest_price')
    def test_calculate_net_profit(self, mock_get_price, mock_get_fertilizer, 
                                 mock_adjusted_yield, mock_yield_penalty):
        """Test complete net profit calculation."""
        # Mock dependencies
        mock_yield_penalty.return_value = {
            'temperature_penalty': 0.0,
            'rainfall_penalty': 0.0,
            'soil_ph_penalty': 0.0,
            'total_penalty': 0.0
        }
        mock_adjusted_yield.return_value = 150  # No penalty
        mock_get_fertilizer.return_value = self.fertilizer
        mock_get_price.return_value = 5.50
        
        result = calculate_net_profit(
            crop=self.crop,
            weather_conditions=self.weather_conditions,
            soil_conditions=self.soil_conditions,
            month=6
        )
        
        # Verify calculations
        expected_revenue = 150 * 5.50  # 825
        expected_total_cost = 300 + 50  # 350 (base + fertilizer)
        expected_profit = expected_revenue - expected_total_cost  # 475
        
        self.assertEqual(result['crop_id'], 'CORN')
        self.assertEqual(result['gross_revenue'], expected_revenue)
        self.assertEqual(result['production_costs']['total_cost'], expected_total_cost)
        self.assertEqual(result['net_profit'], expected_profit)
        self.assertAlmostEqual(result['roi_percent'], (expected_profit / expected_total_cost) * 100, places=2)
    
    def test_calculate_profit_margin(self):
        """Test profit margin calculation."""
        margin = calculate_profit_margin(revenue=1000, costs=600)
        self.assertEqual(margin, 40.0)  # (1000-600)/1000 * 100 = 40%
    
    def test_calculate_profit_margin_zero_revenue(self):
        """Test profit margin calculation with zero revenue."""
        margin = calculate_profit_margin(revenue=0, costs=600)
        self.assertEqual(margin, 0.0)
    
    @patch('src.model.profit_calc.get_latest_price')
    def test_calculate_break_even_yield(self, mock_get_price):
        """Test break-even yield calculation."""
        mock_get_price.return_value = 5.00
        
        break_even = calculate_break_even_yield(self.crop)
        self.assertEqual(break_even, 60.0)  # 300 / 5.00 = 60
    
    @patch('src.model.profit_calc.get_latest_price')
    def test_calculate_break_even_yield_no_price(self, mock_get_price):
        """Test break-even yield calculation with no price data."""
        mock_get_price.return_value = None
        
        with self.assertRaises(ValueError):
            calculate_break_even_yield(self.crop)
    
    def test_profit_calculation_with_penalties(self):
        """Test profit calculation with yield penalties."""
        # This would require more complex mocking or integration testing
        # For now, we'll test the individual components
        pass


if __name__ == '__main__':
    unittest.main()
"""
CLI for monthly crop predictions using weather forecasts.

Usage:
    python -m src.cli.predict_month --parcel P1 --month 9
    python -m src.cli.predict_month --all --month 10
"""

import argparse
import sys
from typing import Optional

from ..pipelines.predict_short_term import (
    run_short_term_pipeline_for_parcel,
    run_short_term_pipeline_for_all_parcels
)
from ..utils.tables import format_recommendations_table
from ..io_.loaders import load_parcels


def main():
    """Main CLI entry point for monthly predictions."""
    parser = argparse.ArgumentParser(
        description='Generate monthly crop recommendations using weather forecasts'
    )
    
    # Parcel selection
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--parcel', type=str, help='Specific parcel ID to analyze')
    group.add_argument('--all', action='store_true', help='Analyze all parcels')
    
    # Required arguments
    parser.add_argument('--month', type=int, required=True, choices=range(1, 13),
                       help='Month number (1-12) for predictions')
    
    # Optional arguments
    parser.add_argument('--top-n', type=int, default=5,
                       help='Number of top recommendations to show (default: 5)')
    parser.add_argument('--ranking', choices=['profit', 'roi', 'yield', 'suitability'],
                       default='profit', help='Ranking method (default: profit)')
    parser.add_argument('--min-confidence', type=float, default=70.0,
                       help='Minimum weather forecast confidence (default: 70)')
    parser.add_argument('--save', action='store_true', default=True,
                       help='Save results to CSV files (default: True)')
    parser.add_argument('--no-save', dest='save', action='store_false',
                       help='Do not save results to CSV files')
    parser.add_argument('--format', choices=['table', 'json', 'csv'], default='table',
                       help='Output format (default: table)')
    parser.add_argument('--quiet', action='store_true',
                       help='Suppress detailed output, show only results')
    
    args = parser.parse_args()
    
    try:
        if args.parcel:
            # Single parcel analysis
            results = run_single_parcel_prediction(args)
            display_results(results, args)
        else:
            # All parcels analysis
            results = run_all_parcels_prediction(args)
            display_all_results(results, args)
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def run_single_parcel_prediction(args) -> dict:
    """Run prediction for a single parcel."""
    if not args.quiet:
        print(f"Analyzing parcel {args.parcel} for month {args.month}...")
    
    results = run_short_term_pipeline_for_parcel(
        parcel_id=args.parcel,
        month=args.month,
        top_n=args.top_n,
        ranking_method=args.ranking,
        min_confidence=args.min_confidence,
        save_results=args.save
    )
    
    return results


def run_all_parcels_prediction(args) -> list:
    """Run prediction for all parcels."""
    if not args.quiet:
        print(f"Analyzing all parcels for month {args.month}...")
    
    results = run_short_term_pipeline_for_all_parcels(
        month=args.month,
        top_n=args.top_n,
        ranking_method=args.ranking,
        min_confidence=args.min_confidence,
        save_results=args.save
    )
    
    return results


def display_results(results: dict, args):
    """Display results for a single parcel."""
    if args.format == 'json':
        import json
        print(json.dumps(results, indent=2, default=str))
        return
    
    if args.format == 'csv':
        display_csv_format(results)
        return
    
    # Table format (default)
    print(f"\n🌾 HARVEST - Monthly Crop Recommendations")
    print(f"═══════════════════════════════════════════")
    print(f"Parcel: {results['parcel_id']} | Month: {results['month']} | Region: {results.get('region', 'Unknown')}")
    
    if 'message' in results:
        print(f"\n⚠️  {results['message']}")
        return
    
    if not results['recommendations']:
        print("\n❌ No profitable crop recommendations found.")
        return
    
    print(f"\n📊 Weather Conditions:")
    weather = results.get('weather_conditions', {})
    print(f"   Temperature: {weather.get('temperature', 'N/A')}°F")
    print(f"   Rainfall: {weather.get('rainfall', 'N/A')} inches")
    print(f"   Confidence: {weather.get('confidence', 'N/A')}%")
    
    print(f"\n🎯 Top {len(results['recommendations'])} Recommendations (ranked by {args.ranking}):")
    table = format_recommendations_table(results['recommendations'])
    print(table)
    
    if args.save and 'output_file' in results:
        print(f"\n💾 Results saved to: {results['output_file']}")


def display_all_results(results: list, args):
    """Display results for all parcels."""
    if args.format == 'json':
        import json
        print(json.dumps(results, indent=2, default=str))
        return
    
    print(f"\n🌾 HARVEST - All Parcels Analysis (Month {args.month})")
    print(f"═══════════════════════════════════════════════════════")
    
    successful_analyses = [r for r in results if 'error' not in r and r['recommendations']]
    failed_analyses = [r for r in results if 'error' in r or not r['recommendations']]
    
    print(f"\n📈 Summary:")
    print(f"   Total parcels: {len(results)}")
    print(f"   Successful analyses: {len(successful_analyses)}")
    print(f"   Failed/No recommendations: {len(failed_analyses)}")
    
    if successful_analyses:
        print(f"\n🎯 Best Recommendations by Parcel:")
        for result in successful_analyses:
            if result['recommendations']:
                best = result['recommendations'][0]
                print(f"   {result['parcel_id']}: {best['crop_name']} (${best['net_profit']:.2f}/acre)")
    
    if failed_analyses and not args.quiet:
        print(f"\n⚠️  Issues:")
        for result in failed_analyses:
            if 'error' in result:
                print(f"   {result['parcel_id']}: {result['error']}")
            elif 'message' in result:
                print(f"   {result['parcel_id']}: {result['message']}")


def display_csv_format(results: dict):
    """Display results in CSV format."""
    if not results['recommendations']:
        return
    
    # Print CSV header
    print("rank,crop_id,crop_name,profit_per_acre,roi_percent,adjusted_yield,confidence")
    
    # Print each recommendation
    for rec in results['recommendations']:
        print(f"{rec['rank']},{rec['crop_id']},{rec['crop_name']},"
              f"{rec['net_profit']:.2f},{rec['roi_percent']:.1f},"
              f"{rec['adjusted_yield']:.1f},{rec.get('recommendation_confidence', 0):.1f}")


def validate_parcel_exists(parcel_id: str) -> bool:
    """Validate that a parcel ID exists."""
    try:
        parcels = load_parcels()
        return parcel_id in parcels['parcel_id'].values
    except Exception:
        return False


if __name__ == '__main__':
    main()
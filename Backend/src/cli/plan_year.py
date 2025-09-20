"""
CLI for annual crop planning using historical weather normals.

Usage:
    python -m src.cli.plan_year --parcel P1
    python -m src.cli.plan_year --all --start-month 3
"""

import argparse
import sys
from typing import Optional

from ..pipelines.predict_long_term import (
    run_long_term_pipeline_for_parcel,
    run_long_term_pipeline_for_all_parcels
)
from ..utils.tables import format_annual_plan_table
from ..io_.loaders import load_parcels


def main():
    """Main CLI entry point for annual planning."""
    parser = argparse.ArgumentParser(
        description='Generate annual crop rotation plans using historical weather normals'
    )
    
    # Parcel selection
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--parcel', type=str, help='Specific parcel ID to analyze')
    group.add_argument('--all', action='store_true', help='Analyze all parcels')
    
    # Optional arguments
    parser.add_argument('--start-month', type=int, default=1, choices=range(1, 13),
                       help='Starting month for annual plan (default: 1)')
    parser.add_argument('--diversification-bonus', type=float, default=0.1,
                       help='Diversification bonus factor (default: 0.1)')
    parser.add_argument('--min-profit', type=float, default=0.0,
                       help='Minimum profit threshold per acre (default: 0.0)')
    parser.add_argument('--save', action='store_true', default=True,
                       help='Save results to CSV files (default: True)')
    parser.add_argument('--no-save', dest='save', action='store_false',
                       help='Do not save results to CSV files')
    parser.add_argument('--format', choices=['table', 'json', 'summary'], default='table',
                       help='Output format (default: table)')
    parser.add_argument('--quiet', action='store_true',
                       help='Suppress detailed output, show only results')
    parser.add_argument('--show-alternatives', action='store_true',
                       help='Show alternative crop options for each month')
    
    args = parser.parse_args()
    
    try:
        if args.parcel:
            # Single parcel analysis
            results = run_single_parcel_planning(args)
            display_plan_results(results, args)
        else:
            # All parcels analysis
            results = run_all_parcels_planning(args)
            display_all_plan_results(results, args)
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def run_single_parcel_planning(args) -> dict:
    """Run annual planning for a single parcel."""
    if not args.quiet:
        print(f"Generating annual plan for parcel {args.parcel}...")
    
    results = run_long_term_pipeline_for_parcel(
        parcel_id=args.parcel,
        start_month=args.start_month,
        diversification_bonus=args.diversification_bonus,
        min_profit_threshold=args.min_profit,
        save_results=args.save
    )
    
    return results


def run_all_parcels_planning(args) -> list:
    """Run annual planning for all parcels."""
    if not args.quiet:
        print(f"Generating annual plans for all parcels...")
    
    results = run_long_term_pipeline_for_all_parcels(
        start_month=args.start_month,
        diversification_bonus=args.diversification_bonus,
        min_profit_threshold=args.min_profit,
        save_results=args.save
    )
    
    return results


def display_plan_results(results: dict, args):
    """Display annual plan results for a single parcel."""
    if args.format == 'json':
        import json
        print(json.dumps(results, indent=2, default=str))
        return
    
    if args.format == 'summary':
        display_summary_format(results)
        return
    
    # Table format (default)
    print(f"\n🌾 HARVEST - Annual Crop Rotation Plan")
    print(f"════════════════════════════════════════════")
    print(f"Parcel: {results['parcel_id']} | Acreage: {results['parcel_info']['acreage']} | Region: {results['parcel_info']['region']}")
    
    if 'error' in results:
        print(f"\n❌ Error: {results['error']}")
        return
    
    if not results['monthly_plans']:
        print("\n❌ No profitable crop plans found for any month.")
        return
    
    # Display annual summary
    annual_summary = results['annual_summary']
    print(f"\n📊 Annual Summary:")
    print(f"   Total Annual Profit: ${annual_summary['total_annual_profit_per_acre']:.2f}/acre")
    print(f"   Total Farm Profit: ${annual_summary['total_farm_profit']:.2f}")
    print(f"   Best Month: {annual_summary.get('best_month_crop', 'N/A')} (${annual_summary.get('best_month_profit', 0):.2f}/acre)")
    print(f"   Months Planned: {results['total_months_planned']}/12")
    
    # Display rotation sequence
    if results['rotation_sequence']:
        print(f"\n🔄 Recommended Rotation Sequence:")
        table = format_annual_plan_table(results['rotation_sequence'])
        print(table)
    
    # Show alternatives if requested
    if args.show_alternatives:
        display_alternatives(results['monthly_plans'])
    
    if args.save and 'output_file' in results:
        print(f"\n💾 Plan saved to: {results['output_file']}")


def display_all_plan_results(results: list, args):
    """Display annual plan results for all parcels."""
    if args.format == 'json':
        import json
        print(json.dumps(results, indent=2, default=str))
        return
    
    print(f"\n🌾 HARVEST - All Parcels Annual Planning")
    print(f"══════════════════════════════════════════════")
    
    successful_plans = [r for r in results if 'error' not in r and r['monthly_plans']]
    failed_plans = [r for r in results if 'error' in r or not r['monthly_plans']]
    
    print(f"\n📈 Summary:")
    print(f"   Total parcels: {len(results)}")
    print(f"   Successful plans: {len(successful_plans)}")
    print(f"   Failed plans: {len(failed_plans)}")
    
    if successful_plans:
        print(f"\n🎯 Annual Profit Potential by Parcel:")
        for result in successful_plans:
            annual_profit = result['annual_summary']['total_annual_profit_per_acre']
            farm_profit = result['annual_summary']['total_farm_profit']
            months_planned = result['total_months_planned']
            print(f"   {result['parcel_id']}: ${annual_profit:.2f}/acre/year (${farm_profit:.2f} total, {months_planned} months)")
    
    if failed_plans and not args.quiet:
        print(f"\n⚠️  Issues:")
        for result in failed_plans:
            if 'error' in result:
                print(f"   {result['parcel_id']}: {result['error']}")
            else:
                print(f"   {result['parcel_id']}: No profitable crops found")


def display_summary_format(results: dict):
    """Display results in summary format."""
    print(f"Parcel {results['parcel_id']} Annual Summary:")
    print(f"Total Profit: ${results['annual_summary']['total_annual_profit_per_acre']:.2f}/acre")
    print(f"Months Planned: {results['total_months_planned']}/12")
    
    if results['rotation_sequence']:
        print("\nRotation Sequence:")
        for month_plan in results['rotation_sequence']:
            print(f"  Month {month_plan['month']:2d}: {month_plan['crop_name']} (${month_plan['profit_per_acre']:.2f}/acre)")


def display_alternatives(monthly_plans: list):
    """Display alternative crop options for each month."""
    print(f"\n🔄 Alternative Options by Month:")
    
    for plan in monthly_plans:
        if plan['alternatives']:
            print(f"\n   {plan['month_name']} (Month {plan['month']}):")
            print(f"     Best: {plan['best_crop']['crop_name']} (${plan['best_crop']['net_profit']:.2f}/acre)")
            
            for i, alt in enumerate(plan['alternatives'][:3], 1):  # Show top 3 alternatives
                print(f"     Alt {i}: {alt['crop_name']} (${alt['net_profit']:.2f}/acre)")


def validate_month_range(start_month: int) -> bool:
    """Validate that start month is in valid range."""
    return 1 <= start_month <= 12


if __name__ == '__main__':
    main()
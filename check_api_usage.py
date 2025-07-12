#!/usr/bin/env python3
"""
Calculate RapidAPI usage and estimate free plan limits.
"""

import json
from pathlib import Path

def analyze_api_usage():
    """Analyze current API usage and estimate total needed."""
    
    print("📊 RapidAPI Free Plan Usage Analysis")
    print("=" * 50)
    
    # From our import progress, calculate usage so far
    cities_completed = 3  # Los Angeles, New York, Chicago
    records_so_far = 1098
    api_calls_so_far = 58  # From the progress output
    
    print(f"📈 CURRENT USAGE:")
    print(f"  Cities processed: {cities_completed}")
    print(f"  API calls made: {api_calls_so_far}")
    print(f"  Records fetched: {records_so_far:,}")
    
    # Calculate average API calls per city
    avg_calls_per_city = api_calls_so_far / cities_completed
    avg_records_per_city = records_so_far / cities_completed
    
    print(f"\n📊 AVERAGES:")
    print(f"  API calls per city: {avg_calls_per_city:.1f}")
    print(f"  Records per city: {avg_records_per_city:.1f}")
    
    # Our full city list for estimation
    total_cities_planned = 70  # Rough estimate of major US cities
    
    # Estimate total API calls needed
    estimated_total_calls = avg_calls_per_city * total_cities_planned
    estimated_total_records = avg_records_per_city * total_cities_planned
    
    print(f"\n🎯 FULL IMPORT ESTIMATES:")
    print(f"  Total cities planned: {total_cities_planned}")
    print(f"  Estimated API calls: {estimated_total_calls:.0f}")
    print(f"  Estimated records: {estimated_total_records:,.0f}")
    
    # RapidAPI Free Plan Limits (typical)
    free_plan_limits = {
        "Basic Free": 100,
        "Extended Free": 500,
        "Premium Free": 1000
    }
    
    print(f"\n🚨 FREE PLAN ANALYSIS:")
    for plan_name, limit in free_plan_limits.items():
        if estimated_total_calls <= limit:
            remaining = limit - api_calls_so_far
            cities_remaining = remaining / avg_calls_per_city
            print(f"  {plan_name} ({limit} calls): ✅ SUFFICIENT")
            print(f"    Remaining calls: {remaining}")
            print(f"    Cities possible: {cities_remaining:.1f}")
        else:
            print(f"  {plan_name} ({limit} calls): ❌ INSUFFICIENT")
            print(f"    Would need: {estimated_total_calls - limit:.0f} extra calls")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    
    if estimated_total_calls <= 100:
        print("  ✅ Continue with full import - well within free limits")
    elif estimated_total_calls <= 500:
        print("  ⚠️ May hit basic free limit - check your specific plan")
        print("  🎯 Consider importing top 20-30 cities for now")
    else:
        print("  🛑 Will likely exceed free limits")
        print("  🎯 Strategic options:")
        print("     • Import top 25 cities (~500 calls)")
        print("     • Pause and check if you have extended free plan")
        print("     • Consider $5-10/month paid plan for one month")
    
    # Current strategy assessment
    cities_within_100_calls = 100 / avg_calls_per_city
    cities_within_500_calls = 500 / avg_calls_per_city
    
    print(f"\n🎯 STRATEGIC CITY LIMITS:")
    print(f"  Within 100 calls: ~{cities_within_100_calls:.0f} cities")
    print(f"  Within 500 calls: ~{cities_within_500_calls:.0f} cities")
    
    # Suggested city prioritization
    priority_cities = [
        "losangeles", "newyork", "chicago", "houston", "phoenix",
        "philadelphia", "seattle", "denver", "miami", "atlanta",
        "dallas", "sanfrancisco", "boston", "detroit", "portland",
        "lasvegas", "austin", "nashville", "charlotte", "milwaukee"
    ]
    
    print(f"\n🏆 SUGGESTED TOP 20 CITIES:")
    for i, city in enumerate(priority_cities[:20], 1):
        print(f"  {i:2d}. {city}")
    
    estimated_calls_top_20 = 20 * avg_calls_per_city
    estimated_records_top_20 = 20 * avg_records_per_city
    
    print(f"\nTop 20 cities would use:")
    print(f"  API calls: ~{estimated_calls_top_20:.0f}")
    print(f"  Records: ~{estimated_records_top_20:,.0f}")
    
    return {
        "current_calls": api_calls_so_far,
        "estimated_total": estimated_total_calls,
        "avg_per_city": avg_calls_per_city,
        "safe_city_count": cities_within_100_calls
    }

if __name__ == "__main__":
    analyze_api_usage()
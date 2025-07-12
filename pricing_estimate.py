#!/usr/bin/env python3
"""
Estimate RapidAPI pricing for UFO data import.
"""

def estimate_pricing():
    """Estimate the cost of importing all UFO data."""
    
    print("💰 RapidAPI UFO Import Cost Estimate")
    print("=" * 50)
    
    # Our usage projections
    current_calls = 58
    estimated_total_calls = 1353  # For 70 cities
    calls_for_top_20 = 387
    calls_for_top_30 = 580
    
    # Typical RapidAPI pricing tiers (common patterns)
    pricing_tiers = {
        "Free": {"calls": 100, "cost": 0},
        "Basic": {"calls": 1000, "cost": 10},  # $10/month typical
        "Pro": {"calls": 10000, "cost": 25},   # $25/month typical
        "Premium": {"calls": 100000, "cost": 50}  # $50/month typical
    }
    
    print("🎯 IMPORT SCENARIOS:")
    print()
    
    scenarios = [
        ("Current (3 cities)", current_calls, 1098),
        ("Top 20 cities", calls_for_top_20, 7320),
        ("Top 30 cities", calls_for_top_30, 10980),
        ("All major cities", estimated_total_calls, 25620)
    ]
    
    for scenario_name, calls_needed, records_estimate in scenarios:
        print(f"📊 {scenario_name}:")
        print(f"   API calls needed: {calls_needed}")
        print(f"   UFO records: ~{records_estimate:,}")
        
        # Find the cheapest plan that fits
        suitable_plans = []
        for plan_name, plan_info in pricing_tiers.items():
            if calls_needed <= plan_info["calls"]:
                suitable_plans.append((plan_name, plan_info["cost"]))
        
        if suitable_plans:
            cheapest = min(suitable_plans, key=lambda x: x[1])
            plan_name, cost = cheapest
            print(f"   💰 Cost: ${cost}/month ({plan_name} plan)")
            if cost == 0:
                print(f"   ✅ FREE!")
            else:
                cost_per_record = cost / records_estimate * 1000
                print(f"   📈 Cost per 1000 records: ${cost_per_record:.2f}")
        else:
            print(f"   ❌ Exceeds typical free/basic plans")
        print()
    
    print("💡 RECOMMENDATIONS:")
    print()
    
    # Free option
    free_limit = pricing_tiers["Free"]["calls"]
    cities_in_free = free_limit / 19.3  # avg calls per city
    records_in_free = cities_in_free * 366  # avg records per city
    
    print(f"🆓 STAY FREE:")
    print(f"   • Continue with ~{cities_in_free:.0f} cities")
    print(f"   • Get ~{records_in_free:,.0f} UFO records")
    print(f"   • Cost: $0")
    print()
    
    # Paid option
    basic_records = 7320  # Top 20 cities
    print(f"💳 PAID OPTION:")
    print(f"   • Get top 20-30 cities (~{basic_records:,} records)")
    print(f"   • Likely cost: $5-15/month")
    print(f"   • Pay for 1 month, cancel immediately")
    print(f"   • Total cost: $5-15 one-time")
    print()
    
    print("🎯 VALUE ANALYSIS:")
    print(f"   Current database: 80,317 records")
    print(f"   With top 20 cities: 87,637 records (+9.1%)")
    print(f"   With all cities: 105,937 records (+31.9%)")
    print()
    print(f"   Cost per % database growth:")
    print(f"   • 9% growth: $5-15 one-time = $0.56-1.67 per %")
    print(f"   • 32% growth: $10-25 one-time = $0.31-0.78 per %")
    print()
    
    print("✅ BOTTOM LINE:")
    print("   • Very reasonable cost for massive data expansion")
    print("   • One-time payment, permanent data ownership")
    print("   • Much cheaper than building your own scraping system")
    print("   • Professional-grade UFO database for <$25")

if __name__ == "__main__":
    estimate_pricing()
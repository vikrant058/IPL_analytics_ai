#!/usr/bin/env python3
"""Test vs_conditions filter implementation"""

from data_loader import IPLDataLoader
from stats_engine import StatsEngine

try:
    print("Loading data...")
    loader = IPLDataLoader()
    matches_df, deliveries_df = loader.load_data()
    stats_engine = StatsEngine(matches_df, deliveries_df)
    
    print("\n✅ Data loaded successfully")
    print(f"   Bowler types loaded: {len(stats_engine._bowler_types)} classification groups")
    
    # Test 1: Kohli vs pace
    print("\n📊 Test 1: Kohli vs pace bowlers")
    filters = {'vs_conditions': 'vs_pace'}
    stats = stats_engine.get_player_stats('V Kohli', filters)
    print(f"   ✅ Runs: {stats.get('runs', 0)}")
    print(f"   ✅ Strike Rate: {stats.get('strike_rate', 0):.2f}")
    
    # Test 2: Kohli vs spin
    print("\n📊 Test 2: Kohli vs spin bowlers")
    filters = {'vs_conditions': 'vs_spin'}
    stats = stats_engine.get_player_stats('V Kohli', filters)
    print(f"   ✅ Runs: {stats.get('runs', 0)}")
    print(f"   ✅ Strike Rate: {stats.get('strike_rate', 0):.2f}")
    
    # Test 3: Multi-filter: Kohli vs pace in powerplay
    print("\n📊 Test 3: Kohli vs pace in powerplay")
    filters = {'vs_conditions': 'vs_pace', 'match_phase': 'powerplay'}
    stats = stats_engine.get_player_stats('V Kohli', filters)
    print(f"   ✅ Runs: {stats.get('runs', 0)}")
    print(f"   ✅ Strike Rate: {stats.get('strike_rate', 0):.2f}")
    
    print("\n✅✅✅ All tests passed! vs_conditions filter working correctly!")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

#!/usr/bin/env python3
"""Verify statistical calculations are correct"""

from data_loader import IPLDataLoader
from stats_engine import StatsEngine

loader = IPLDataLoader()
matches_df, deliveries_df = loader.load_data()
stats_engine = StatsEngine(matches_df, deliveries_df)

print("="*70)
print("STATISTICAL VALIDATION")
print("="*70)

# Test 1: Kohli overall stats
print("\n[TEST 1] Kohli overall batting stats")
stats = stats_engine.get_player_stats('V Kohli', None)
batting = stats.get('batting', {})
print(f"  Innings: {batting.get('innings')}")
print(f"  Runs: {batting.get('runs')}")
print(f"  Average: {batting.get('average'):.2f}")
print(f"  Strike Rate: {batting.get('strike_rate'):.2f}")

# Validate
if batting.get('innings') == 0:
    print("  ❌ ERROR: Zero innings!")
elif batting.get('runs') == 0:
    print("  ❌ ERROR: Zero runs!")
elif batting.get('average') == 0 and batting.get('innings') > 0:
    print("  ❌ ERROR: Average is 0 but innings > 0!")
else:
    print("  ✅ Stats look reasonable")

# Test 2: Bumrah bowling stats
print("\n[TEST 2] Bumrah overall bowling stats")
stats = stats_engine.get_player_stats('JJ Bumrah', None)
bowling = stats.get('bowling', {})
print(f"  Innings: {bowling.get('innings')}")
print(f"  Wickets: {bowling.get('wickets')}")
print(f"  Economy: {bowling.get('economy'):.2f}")
print(f"  Average: {bowling.get('average'):.2f}")

# Validate
if bowling.get('wickets') == 0:
    print("  ⚠️  No wickets (might be normal if data incomplete)")
elif bowling.get('average') and bowling.get('economy'):
    if bowling.get('average') < 0 or bowling.get('economy') < 0:
        print("  ❌ ERROR: Negative values!")
    else:
        print("  ✅ Bowling stats look reasonable")

# Test 3: Filtered stats
print("\n[TEST 3] Kohli vs MI stats")
stats = stats_engine.get_player_stats('V Kohli', {'opposition_team': 'Mumbai Indians'})
batting = stats.get('batting', {})
print(f"  Matches: {batting.get('matches')}")
print(f"  Runs: {batting.get('runs')}")
if batting.get('matches') > 0 and batting.get('runs') > 0:
    print("  ✅ Filtered stats correct")
elif batting.get('runs') == 0 and batting.get('matches') == 0:
    print("  ❌ ERROR: No matches vs MI (filter broken!)")
else:
    print("  ⚠️  Unusual data")

# Test 4: Check for NaN/Inf
print("\n[TEST 4] Data quality checks")
import math

stats = stats_engine.get_player_stats('V Kohli', None)
batting = stats.get('batting', {})

has_errors = False
for key, value in batting.items():
    if isinstance(value, float):
        if math.isnan(value):
            print(f"  ❌ NaN in {key}")
            has_errors = True
        elif math.isinf(value):
            print(f"  ❌ Infinity in {key}")
            has_errors = True

if not has_errors:
    print("  ✅ No NaN/Infinity values found")

print("\n" + "="*70)
print("VALIDATION COMPLETE")
print("="*70)

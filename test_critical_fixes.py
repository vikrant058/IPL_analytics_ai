#!/usr/bin/env python3
"""Test all critical fixes"""

from data_loader import IPLDataLoader
from stats_engine import StatsEngine
from openai_handler import CricketChatbot

loader = IPLDataLoader()
matches_df, deliveries_df = loader.load_data()
handler = CricketChatbot(matches_df, deliveries_df)
stats_engine = StatsEngine(matches_df, deliveries_df)

print("="*70)
print("TESTING CRITICAL FIXES")
print("="*70)

# Test 1: kohli vs mi
print("\n[1] 'kohli vs mi'")
parsed = handler.parse_query('kohli vs mi')
print(f"    Opposition team extracted: {parsed.get('opposition_team')}")
stats = stats_engine.get_player_stats('V Kohli', {'opposition_team': 'Mumbai Indians'})
print(f"    Runs: {stats.get('batting', {}).get('runs')}")
if stats.get('batting', {}).get('runs') == 927:
    print("    ✅ CORRECT (927 runs vs MI)")
else:
    print(f"    ❌ WRONG (expected 927, got {stats.get('batting', {}).get('runs')})")

# Test 2: kohli vs left arm spin  
print("\n[2] 'kohli vs left arm spin'")
parsed = handler.parse_query('kohli vs left arm spin')
print(f"    vs_conditions extracted: {parsed.get('vs_conditions')}")
if parsed.get('vs_conditions') == 'vs_left_arm_spin':
    print("    ✅ CORRECT (vs_left_arm_spin)")
else:
    print(f"    ❌ WRONG (expected vs_left_arm_spin, got {parsed.get('vs_conditions')})")

# Test 3: kohli vs off spinners
print("\n[3] 'kohli vs off spinners'")
parsed = handler.parse_query('kohli vs off spinners')
print(f"    vs_conditions extracted: {parsed.get('vs_conditions')}")
if parsed.get('vs_conditions') == 'vs_off_spin':
    print("    ✅ CORRECT (vs_off_spin)")
else:
    print(f"    ❌ WRONG (expected vs_off_spin, got {parsed.get('vs_conditions')})")

# Test 4: virat vs mi
print("\n[4] 'virat vs mi'")
parsed = handler.parse_query('virat vs mi')
print(f"    Player: {parsed.get('player1')}")
print(f"    Opposition: {parsed.get('opposition_team')}")
if parsed.get('opposition_team') == 'Mumbai Indians':
    print("    ✅ CORRECT team canonicalization")
else:
    print(f"    ❌ WRONG (got {parsed.get('opposition_team')})")

print("\n" + "="*70)
print("✅ CRITICAL FIXES TESTED")
print("="*70)

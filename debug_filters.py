#!/usr/bin/env python3
"""Debug opposition_team and vs filters"""

from data_loader import IPLDataLoader
from stats_engine import StatsEngine
from openai_handler import CricketChatbot

loader = IPLDataLoader()
matches_df, deliveries_df = loader.load_data()
stats_engine = StatsEngine(matches_df, deliveries_df)
handler = CricketChatbot(matches_df, deliveries_df)

print("=" * 70)
print("DEBUGGING FILTER ISSUES")
print("=" * 70)

# Test 1: Opposition team extraction
print("\n[TEST 1] Opposition team extraction")
parsed = handler.parse_query("kohli vs mi")
print(f"  opposition_team extracted: '{parsed.get('opposition_team')}'")
print(f"  player1: '{parsed.get('player1')}'")

# Test 2: Team canonicalization
print("\n[TEST 2] Team canonicalization")
mi_canonical = handler._get_canonical_team_name("mi")
print(f"  'mi' → '{mi_canonical}'")
print(f"  Type of result: {type(mi_canonical)}")

# Check what's in team_aliases
print(f"  team_aliases keys (sample): {list(handler.team_aliases.keys())[:5]}")
if 'mi' in handler.team_aliases:
    print(f"  team_aliases['mi'] = '{handler.team_aliases['mi']}'")
else:
    print(f"  'mi' NOT in team_aliases")

teams_in_data = matches_df['team1'].unique()
print(f"  Teams in data: {sorted(teams_in_data)[:3]}...")
print(f"  'Mumbai Indians' in data: {'Mumbai Indians' in teams_in_data}")

# Test 3: Filter comparison
print("\n[TEST 3] Filter application - Opposition Team")
all_stats = stats_engine.get_player_stats('V Kohli', None)
print(f"  Kohli overall runs: {all_stats.get('batting', {}).get('runs', 0)}")

vs_mi_stats = stats_engine.get_player_stats('V Kohli', {'opposition_team': 'Mumbai Indians'})
print(f"  Kohli vs MI runs: {vs_mi_stats.get('batting', {}).get('runs', 0)}")

if all_stats.get('batting', {}).get('runs', 0) == vs_mi_stats.get('batting', {}).get('runs', 0):
    print("  ❌ SAME STATS - FILTER NOT WORKING!")
else:
    print("  ✅ Different stats - filter working")

# Test 4: Left arm spin filter
print("\n[TEST 4] Filter application - Left arm bowlers")
all_left_arm = stats_engine.get_player_stats('V Kohli', {'vs_conditions': 'vs_left_arm'})
print(f"  Kohli vs left-arm runs: {all_left_arm.get('batting', {}).get('runs', 0)}")

# Test 5: Multiple filters
print("\n[TEST 5] Multiple filters combined")
multi_stats = stats_engine.get_player_stats('V Kohli', {
    'opposition_team': 'Mumbai Indians',
    'vs_conditions': 'vs_left_arm'
})
print(f"  Kohli vs MI vs left-arm runs: {multi_stats.get('batting', {}).get('runs', 0)}")

# Debug: Check how many matches each has
print("\n[DEBUG] Match counts")
all_matches = all_stats.get('batting', {}).get('matches', 0)
mi_matches = vs_mi_stats.get('batting', {}).get('matches', 0)
print(f"  Total matches: {all_matches}")
print(f"  MI matches: {mi_matches}")
if mi_matches == 0:
    print("  ❌ ZERO matches vs MI - filter is filtering out ALL data!")

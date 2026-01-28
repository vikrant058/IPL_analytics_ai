#!/usr/bin/env python3
"""Test that filters actually change stats"""

import os

# Load API key
env_file = '/Users/vikrant/Desktop/IPL_analytics_ai/.env'
if os.path.exists(env_file):
    with open(env_file) as f:
        for line in f:
            if line.startswith('OPENAI_API_KEY'):
                os.environ['OPENAI_API_KEY'] = line.split('=')[1].strip()

from data_loader import IPLDataLoader
from stats_engine import StatsEngine

# Load data
print("📊 Loading IPL data...")
loader = IPLDataLoader()
matches_df, deliveries_df = loader.load_data()
print(f"✅ Loaded: {len(matches_df)} matches, {len(deliveries_df)} deliveries\n")

# Initialize stats engine
stats_engine = StatsEngine(matches_df, deliveries_df)

print("🧪 Testing filter application in H2H stats:\n")
print("=" * 80)

# Test 1: kohli vs bumrah (overall)
print("\n1️⃣  KOHLI vs BUMRAH (Overall):")
h2h_overall = stats_engine.get_player_head_to_head("V Kohli", "JJ Bumrah")
print(f"   Deliveries: {h2h_overall.get('deliveries')}")
print(f"   Runs: {h2h_overall.get('runs')}")
print(f"   Strike Rate: {h2h_overall.get('strike_rate')}")

# Test 2: kohli vs bumrah in powerplay
print("\n2️⃣  KOHLI vs BUMRAH (Powerplay only):")
h2h_powerplay = stats_engine.get_player_head_to_head("V Kohli", "JJ Bumrah", 
                                                     filters={'match_phase': 'powerplay'})
print(f"   Deliveries: {h2h_powerplay.get('deliveries')}")
print(f"   Runs: {h2h_powerplay.get('runs')}")
print(f"   Strike Rate: {h2h_powerplay.get('strike_rate')}")

# Test 3: Compare - should be DIFFERENT!
print("\n3️⃣  COMPARISON:")
if h2h_overall['deliveries'] != h2h_powerplay['deliveries']:
    print(f"   ✅ GOOD! Overall has {h2h_overall['deliveries']} vs Powerplay has {h2h_powerplay['deliveries']}")
    print(f"   ✅ Strike rates different: {h2h_overall['strike_rate']} vs {h2h_powerplay['strike_rate']}")
else:
    print(f"   ❌ BAD! Same number of deliveries - filter NOT applied!")

print("\n" + "=" * 80)
print("\n✅ Test complete!")

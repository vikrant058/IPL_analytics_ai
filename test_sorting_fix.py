#!/usr/bin/env python3
"""Verify get_last_n_matches is sorting correctly"""

import sys
sys.path.insert(0, '.')
from data_loader import IPLDataLoader
from stats_engine import StatsEngine

loader = IPLDataLoader()
matches_df, deliveries_df = loader.load_data()
stats = StatsEngine(matches_df, deliveries_df)

print("Testing get_last_n_matches sorting:")
print("="*70)

# Get Bumrah's last 5 matches
matches = stats.get_last_n_matches('JJ Bumrah', 5)

print("\nBumrah's last 5 matches (from stats_engine):")
for i, match in enumerate(matches, 1):
    bowl = match['bowling']
    print(f"{i}. Date: {match['date']}, Opposition: {match['opposition']}, Bowling: {bowl['wickets']} wickets, {bowl['runs']} runs in {bowl['balls']} balls")

# Also check that they're in descending order
print("\nVerifying date order (should be descending):")
dates = [m['date'] for m in matches]
is_descending = all(dates[i] >= dates[i+1] for i in range(len(dates)-1))
print(f"Dates: {dates}")
print(f"Is descending order? {is_descending}")

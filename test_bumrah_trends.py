#!/usr/bin/env python3
"""Debug bumrah bowling trends"""

import sys
sys.path.insert(0, '.')
from data_loader import IPLDataLoader

loader = IPLDataLoader()
matches_df, deliveries_df = loader.load_data()

# Check bumrah's matches
bumrah_bat = deliveries_df[deliveries_df['batter'] == 'JJ Bumrah'][['match_id']].drop_duplicates()
bumrah_bowl = deliveries_df[deliveries_df['bowler'] == 'JJ Bumrah'][['match_id']].drop_duplicates()
bumrah_matches = set(bumrah_bat['match_id'].unique()) | set(bumrah_bowl['match_id'].unique())

# Get match details
print("Bumrah's last 10 matches (by match_id descending):")
print("="*70)

match_ids_sorted_by_id = sorted(list(bumrah_matches), key=lambda x: -x)[:10]

for match_id in match_ids_sorted_by_id:
    match_row = matches_df[matches_df['id'] == match_id]
    if not match_row.empty:
        match_info = match_row.iloc[0]
        print(f"Match ID: {match_id}, Date: {match_info['date']}, Season: {match_info.get('season', 'N/A')}")

print("\n" + "="*70)
print("ISSUE: Sorted by match_id (1160, 1159, ...) NOT by date!")
print("="*70)

print("\nBumrah's last 5 matches (sorted by date DESC - CORRECT):")
match_dates = {}
for match_id in bumrah_matches:
    match_row = matches_df[matches_df['id'] == match_id]
    if not match_row.empty:
        match_info = match_row.iloc[0]
        match_dates[match_id] = match_info['date']

# Sort by date in descending order
match_ids_correct = sorted(list(bumrah_matches), key=lambda x: match_dates.get(x, ''), reverse=True)[:5]
for match_id in match_ids_correct:
    print(f"Match ID: {match_id}, Date: {match_dates[match_id]}")

# Check wickets
print("\n" + "="*70)
print("Checking wickets in last 5 matches (by date DESC):")
print("="*70)

for match_id in match_ids_correct:
    bowl_deliv = deliveries_df[(deliveries_df['match_id'] == match_id) & 
                               (deliveries_df['bowler'] == 'JJ Bumrah')]
    wickets = (bowl_deliv['is_wicket'] == 1).sum()
    runs = bowl_deliv['total_runs'].sum()
    balls = len(bowl_deliv)
    print(f"Match {match_id}: {balls} balls, {runs} runs, {wickets} wickets")

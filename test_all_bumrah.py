#!/usr/bin/env python3
"""Check ALL bumrah matches to see wickets"""

import sys
sys.path.insert(0, '.')
from data_loader import IPLDataLoader

loader = IPLDataLoader()
matches_df, deliveries_df = loader.load_data()

# Check bumrah's matches
bumrah_bat = deliveries_df[deliveries_df['batter'] == 'JJ Bumrah'][['match_id']].drop_duplicates()
bumrah_bowl = deliveries_df[deliveries_df['bowler'] == 'JJ Bumrah'][['match_id']].drop_duplicates()
bumrah_matches = set(bumrah_bat['match_id'].unique()) | set(bumrah_bowl['match_id'].unique())

# Get match details with dates
match_dates = {}
for match_id in bumrah_matches:
    match_row = matches_df[matches_df['id'] == match_id]
    if not match_row.empty:
        match_info = match_row.iloc[0]
        match_dates[match_id] = match_info['date']

# Sort by date in descending order (most recent first)
match_ids_sorted = sorted(list(bumrah_matches), key=lambda x: match_dates.get(x, ''), reverse=True)

print("All Bumrah matches (sorted by date DESC):")
print("="*70)
print(f"Total matches: {len(match_ids_sorted)}")
print("\nFirst 10 (most recent):")

for i, match_id in enumerate(match_ids_sorted[:10], 1):
    bowl_deliv = deliveries_df[(deliveries_df['match_id'] == match_id) & 
                               (deliveries_df['bowler'] == 'JJ Bumrah')]
    wickets = (bowl_deliv['is_wicket'] == 1).sum()
    runs = bowl_deliv['total_runs'].sum()
    balls = len(bowl_deliv)
    
    match_row = matches_df[matches_df['id'] == match_id].iloc[0]
    opposition = match_row['team2'] if match_row['team1'] == 'Mumbai Indians' else match_row['team1']
    
    print(f"{i:2d}. Date: {match_dates[match_id]}, Opposition: {opposition:20s} | Balls: {balls:2d}, Runs: {runs:2d}, Wickets: {wickets}")

print("\nMatches with wickets (ordered by date DESC):")
print("="*70)

wicket_matches = []
for match_id in match_ids_sorted:
    bowl_deliv = deliveries_df[(deliveries_df['match_id'] == match_id) & 
                               (deliveries_df['bowler'] == 'JJ Bumrah')]
    wickets = (bowl_deliv['is_wicket'] == 1).sum()
    if wickets > 0:
        wicket_matches.append((match_id, wickets, match_dates[match_id]))

print(f"Total matches with wickets: {len(wicket_matches)}")
for i, (match_id, wickets, date) in enumerate(wicket_matches[:5], 1):
    match_row = matches_df[matches_df['id'] == match_id].iloc[0]
    opposition = match_row['team2'] if match_row['team1'] == 'Mumbai Indians' else match_row['team1']
    print(f"{i}. Date: {date}, Wickets: {wickets}, Opposition: {opposition}")

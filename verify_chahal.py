import pandas as pd

deliveries = pd.read_csv('deliveries.csv')
matches = pd.read_csv('matches.csv')

# Basic info
print("=== Dataset Info ===")
print(f"Total matches: {len(matches)}")
print(f"Total deliveries: {len(deliveries)}")
print(f"Date range: {matches['date'].min()} to {matches['date'].max()}")

# Chahal check
chahal = deliveries[deliveries['bowler'] == 'YS Chahal']
print(f"\n=== Chahal Stats ===")
print(f"Total deliveries: {len(chahal)}")
print(f"Wickets (is_wicket=1): {chahal['is_wicket'].sum()}")
print(f"Matches played: {chahal['match_id'].nunique()}")

# Dismissal breakdown
print(f"\n=== Dismissal Types ===")
dismissals = chahal[chahal['is_wicket'] == 1]
print(dismissals['dismissal_kind'].value_counts())

# Check if he's in top performers
from stats_engine import get_top_performers
top_bowlers = get_top_performers('bowlers', season=None, opposition=None, match_phase=None, home_away=None, ground=None)
print(f"\n=== Top Performers Check ===")
print(f"Top 10 bowlers: {top_bowlers}")
chahal_in_top = any('Chahal' in str(p) for p in top_bowlers)
print(f"Chahal in top 10: {chahal_in_top}")

import pandas as pd
from stats_engine import StatsEngine

print("Loading...")
matches_df = pd.read_csv('matches.csv')
deliveries_df = pd.read_csv('deliveries.csv')
print("Creating engine...")
stats = StatsEngine(matches_df, deliveries_df)
print("Testing Kohli...")
kohli_innings = stats.get_last_n_innings('V Kohli', 5)
print(f"Kohli innings: {len(kohli_innings)}")
if kohli_innings:
    print(f"First inning: {kohli_innings[0]}")

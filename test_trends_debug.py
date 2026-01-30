import pandas as pd
from stats_engine import StatsEngine

# Load data
matches_df = pd.read_csv('matches.csv')
deliveries_df = pd.read_csv('deliveries.csv')
stats = StatsEngine(matches_df, deliveries_df)

# Test Bumrah's last 5 matches
bumrah_matches = stats.get_last_n_matches('JJ Bumrah', 5)
print(f"Bumrah last 5 matches: {len(bumrah_matches)} matches")
if bumrah_matches:
    for i, match in enumerate(bumrah_matches[:3], 1):
        print(f"\n  Match {i}: vs {match['opposition']}")
        bowl = match['bowling']
        print(f"    Bowling: wickets={bowl['wickets']}, runs={bowl['runs']}, balls={bowl['balls']}")

# Test Kohli's last 5 innings
kohli_innings = stats.get_last_n_innings('V Kohli', 5)
print(f"\n\nKohli last 5 innings: {len(kohli_innings)} innings")
meaningful = [i for i in kohli_innings if i['balls'] >= 3]
print(f"Kohli meaningful innings (3+ balls): {len(meaningful)}")
if meaningful:
    for i, inning in enumerate(meaningful[:2], 1):
        print(f"  Inning {i}: {inning['opposition']}, {inning['runs']}/{inning['balls']}")

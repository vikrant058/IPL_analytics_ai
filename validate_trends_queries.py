"""
Comprehensive test for trends queries - validates last N innings/matches for multiple players
"""
import pandas as pd
from stats_engine import StatsEngine

# Load data
print("Loading data...")
matches_df = pd.read_csv('matches.csv')
deliveries_df = pd.read_csv('deliveries.csv')
stats = StatsEngine(matches_df, deliveries_df)

print(f"✅ Data loaded: {len(matches_df)} matches, {len(deliveries_df)} deliveries\n")

# Test batters
batters = ['V Kohli', 'RG Sharma', 'SA Yadav', 'AB de Villiers', 'MS Dhoni']
print("=" * 80)
print("BATTER TESTS - Last 5 Innings")
print("=" * 80)

for batter in batters:
    innings = stats.get_last_n_innings(batter, 5)
    meaningful = [i for i in innings if i['balls'] >= 3]
    print(f"\n{batter}:")
    print(f"  Total innings returned: {len(innings)}")
    print(f"  Meaningful innings (3+ balls): {len(meaningful)}")
    if meaningful:
        for i, inning in enumerate(meaningful[:2], 1):
            print(f"    Inning {i}: vs {inning['opposition']}, {inning['runs']}/{inning['balls']}, dismissed={inning['dismissed']}")
    else:
        print(f"    ❌ NO MEANINGFUL INNINGS!")

# Test bowlers
bowlers = ['JJ Bumrah', 'YA Chahal', 'R Ashwin', 'B Kumar', 'DC Pacer']
print("\n" + "=" * 80)
print("BOWLER TESTS - Last 5 Matches")
print("=" * 80)

for bowler in bowlers:
    matches = stats.get_last_n_matches(bowler, 5)
    print(f"\n{bowler}:")
    print(f"  Total matches returned: {len(matches)}")
    if matches:
        for i, match in enumerate(matches[:2], 1):
            bowl = match['bowling']
            bat = match['batting']
            print(f"    Match {i}: vs {match['opposition']}")
            print(f"      Bowling: {bowl['wickets']}W, {bowl['runs']}R, {bowl['balls']}B")
            print(f"      Batting: {bat['runs']}/{bat['balls']}")
    else:
        print(f"    ❌ NO MATCHES!")

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print("✅ If meaningful innings > 0 for batters, they should display innings breakdown")
print("✅ If matches > 0 for bowlers, they should display bowling breakdown")
print("❌ Any player with 0 results needs investigation")

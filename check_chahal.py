import pandas as pd
from data_loader import IPLDataLoader
from stats_engine import StatsEngine

loader = IPLDataLoader()
matches, deliveries = loader.load_data()
matches, deliveries = loader.preprocess_data()

# Create stats engine
stats_engine = StatsEngine(matches, deliveries)

# Check all bowlers with 'Chahal' in name
all_bowlers = deliveries['bowler'].unique()
chahal_bowlers = [b for b in all_bowlers if 'Chahal' in b or 'chahal' in b]
print(f"Chahal variants in data: {chahal_bowlers}\n")

# Get stats for each variant
for bowler in chahal_bowlers:
    stats = stats_engine.get_player_stats(bowler)
    if 'bowling' in stats and stats['bowling']:
        print(f"{bowler}:")
        print(f"  Wickets: {stats['bowling'].get('wickets', 0)}")
        print(f"  Matches: {stats['bowling'].get('matches', 0)}")
        print(f"  Economy: {stats['bowling'].get('economy', 0):.2f}")
    else:
        print(f"{bowler}: No bowling stats\n")

# Check top bowlers
print("\n=== Top 20 Bowlers ===")
bowler_stats = []
for bowler in deliveries['bowler'].unique()[:100]:  # Check first 100
    stats = stats_engine.get_player_stats(bowler)
    if 'bowling' in stats and stats['bowling']:
        bowler_stats.append({
            'Player': bowler,
            'Wickets': stats['bowling'].get('wickets', 0),
            'Economy': stats['bowling'].get('economy', 0)
        })

df = pd.DataFrame(bowler_stats).sort_values('Wickets', ascending=False).head(20)
print(df.to_string())

# Check if Chahal is in top performers
chahal_found = df[df['Player'].str.contains('Chahal', case=False, na=False)]
if len(chahal_found) > 0:
    print(f"\nChahal found in top 20:")
    print(chahal_found.to_string())
else:
    print("\nChahal NOT in top 20 bowlers!")

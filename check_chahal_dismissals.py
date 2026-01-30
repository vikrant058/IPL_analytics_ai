import pandas as pd

# Load deliveries
deliveries = pd.read_csv('deliveries.csv')
deliveries.columns = deliveries.columns.str.strip()

# Get Chahal's deliveries (regular innings only)
chahal = deliveries[(deliveries['bowler'].str.contains('Chahal', case=False, na=False)) & 
                    (deliveries['inning'].isin([1, 2]))]

print(f"Total Chahal deliveries: {len(chahal)}")
print(f"Wickets (is_wicket=1): {chahal['is_wicket'].sum()}")

# Check dismissals
print("\nDismissal breakdown for Chahal:")
dismissals = chahal[chahal['is_wicket'] == 1].groupby('dismissal_kind').size()
print(dismissals)

# Check if there are dismissals with is_wicket=0 (run out, retired, etc.)
non_bowler_dismissals = chahal[(chahal['is_wicket'] == 0) & (chahal['player_dismissed'].notna())].groupby('dismissal_kind').size()
print(f"\nNon-bowler dismissals (is_wicket=0):")
print(non_bowler_dismissals)

# Total dismissals
total_dismissals = chahal[chahal['player_dismissed'].notna()].shape[0]
print(f"\nTotal dismissals (any kind): {total_dismissals}")

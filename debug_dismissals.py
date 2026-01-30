import pandas as pd

deliveries = pd.read_csv('deliveries.csv')

# Check structure of dismissal columns
print("=== Sample Dismissal Data ===")
sample = deliveries[deliveries['is_wicket'] == 1][['bowler', 'dismissal_kind', 'player_dismissed', 'is_wicket']].head(20)
print(sample)

# Check for run outs
print("\n=== Run Out Examples ===")
run_outs = deliveries[deliveries['dismissal_kind'] == 'run out'][['bowler', 'dismissal_kind', 'player_dismissed', 'is_wicket']].head(10)
print(run_outs)

# Check Chahal specifically for any run outs
print("\n=== Chahal Run Out Check ===")
chahal_all = deliveries[deliveries['bowler'] == 'YS Chahal']
print(f"Total Chahal deliveries: {len(chahal_all)}")
print(f"Chahal wickets (is_wicket=1): {(chahal_all['is_wicket'] == 1).sum()}")
print(f"Chahal run outs: {(chahal_all['dismissal_kind'] == 'run out').sum()}")

# Check if run outs have is_wicket=1 or 0
run_out_is_wicket_1 = deliveries[(deliveries['dismissal_kind'] == 'run out') & (deliveries['is_wicket'] == 1)]
print(f"Run outs with is_wicket=1: {len(run_out_is_wicket_1)}")

run_out_is_wicket_0 = deliveries[(deliveries['dismissal_kind'] == 'run out') & (deliveries['is_wicket'] == 0)]
print(f"Run outs with is_wicket=0: {len(run_out_is_wicket_0)}")

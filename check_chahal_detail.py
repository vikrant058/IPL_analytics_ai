import pandas as pd

# Load deliveries
deliveries = pd.read_csv('deliveries.csv', low_memory=False)
deliveries.columns = deliveries.columns.str.strip()

# Get Chahal's deliveries (regular innings only)
chahal = deliveries[(deliveries['bowler'] == 'YS Chahal') & 
                    (deliveries['inning'].isin([1, 2]))]

print(f"Total Chahal deliveries: {len(chahal)}")
print(f"Bowler-responsible wickets (is_wicket=1): {chahal['is_wicket'].sum()}")

# Check if there are run-out dismissals where Chahal bowled
chahal_run_outs = chahal[(chahal['dismissal_kind'] == 'run out') & (chahal['is_wicket'] == 0)]
print(f"\nRun-out dismissals while Chahal bowled: {len(chahal_run_outs)}")

# Maybe the issue is in how the CSV was generated
# Let's check all dismissal kinds
print("\nAll dismissal kinds in deliveries:")
print(deliveries['dismissal_kind'].value_counts())

# Check if Chahal appears in multiple forms
print("\nAll Chahal variants in bowler column:")
chahal_all = deliveries[deliveries['bowler'].str.contains('Chahal', case=False, na=False)]
print(chahal_all['bowler'].unique())

# Total all Chahal including super overs
print(f"\nTotal Chahal all innings: {chahal_all['is_wicket'].sum()} wickets")
chahal_inning_3 = chahal_all[~chahal_all['inning'].isin([1, 2])]
print(f"Chahal in innings 3+: {chahal_inning_3['is_wicket'].sum()} wickets")

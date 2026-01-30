import pandas as pd

deliveries = pd.read_csv('deliveries.csv')
chahal = deliveries[deliveries['bowler'] == 'YS Chahal']

# Old way (with run outs)
old_wickets = (chahal['is_wicket'] == 1).sum()

# New way (exclude run outs)
new_wickets = len(chahal[(chahal['is_wicket'] == 1) & (chahal['dismissal_kind'] != 'run out')])

# Breakdown
breakdown = chahal[chahal['is_wicket'] == 1]['dismissal_kind'].value_counts()

print(f"Chahal Wicket Calculation:")
print(f"Old (with run outs): {old_wickets}")
print(f"New (excluding run outs): {new_wickets}")
print(f"Run outs: {breakdown.get('run out', 0)}")
print(f"\nBreakdown (bowler-credited):")
for kind, count in breakdown.items():
    if kind != 'run out':
        print(f"  {kind}: {count}")
print(f"  run out: {breakdown.get('run out', 0)} [NOT CREDITED]")
print(f"\nTotal (new): {new_wickets}")

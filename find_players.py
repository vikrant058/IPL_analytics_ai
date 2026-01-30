import pandas as pd

deliveries = pd.read_csv('deliveries.csv')

# Get unique batters and search for Kohli
batters = sorted(deliveries['batter'].unique())
kohli_options = [b for b in batters if 'kohli' in b.lower()]
bumrah_options = [b for b in batters if 'bumrah' in b.lower()]

print("Kohli options:", kohli_options)
print("Bumrah options:", bumrah_options)

if kohli_options:
    for kohli in kohli_options:
        kohli_bat = deliveries[deliveries['batter'] == kohli]
        print(f"\n{kohli}: {len(kohli_bat)} deliveries")

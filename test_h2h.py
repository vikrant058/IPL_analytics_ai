#!/usr/bin/env python3
"""Test the new head-to-head player comparison features"""

from data_loader import IPLDataLoader
from ai_engine import AIEngine

# Load data
loader = IPLDataLoader()
matches, deliveries = loader.load_data()
matches, deliveries = loader.preprocess_data()

ai = AIEngine(matches, deliveries)

print("\n" + "="*70)
print("Testing New Head-to-Head Player Comparison Features")
print("="*70)

# Test 1: Batter vs Bowler
print("\n1️⃣  BATTER vs BOWLER: V Kohli vs B Kumar")
print("-"*70)
result = ai.get_player_head_to_head('V Kohli', 'B Kumar')
if 'batter' in result:
    print(f"Batter: {result['batter']['player']}")
    print(f"  - Runs vs bowler: {result['batter']['runs_vs_bowler']}")
    print(f"  - Balls faced: {result['batter']['balls_vs_bowler']}")
    print(f"  - Strike Rate vs bowler: {result['batter']['sr_vs_bowler']}")
    print(f"  - Overall Strike Rate: {result['batter']['overall_sr']}")
    
    print(f"\nBowler: {result['bowler']['player']}")
    print(f"  - Runs conceded: {result['bowler']['runs_conceded_to_batter']}")
    print(f"  - Balls bowled: {result['bowler']['balls_bowled_to_batter']}")
    print(f"  - Economy vs batter: {result['bowler']['economy_vs_batter']}")
    print(f"  - Overall Economy: {result['bowler']['overall_economy']}")
else:
    print(result.get('message', 'No data found'))

# Test 2: Batter vs Batter
print("\n\n2️⃣  BATTER vs BATTER: V Kohli vs RG Sharma")
print("-"*70)
result = ai.get_player_head_to_head('V Kohli', 'RG Sharma')
if 'comparison' in result:
    print(f"Comparison: {result['batter1']} vs {result['batter2']}")
    print(f"\nRuns:")
    print(f"  - {result['batter1']}: {result['comparison']['runs'][result['batter1']]}")
    print(f"  - {result['batter2']}: {result['comparison']['runs'][result['batter2']]}")
    print(f"  - Difference: {result['comparison']['runs']['difference']}")
    
    print(f"\nAverage:")
    print(f"  - {result['batter1']}: {result['comparison']['average'][result['batter1']]}")
    print(f"  - {result['batter2']}: {result['comparison']['average'][result['batter2']]}")
    print(f"  - Better: {result['comparison']['average']['better']}")
    
    print(f"\nStrike Rate:")
    print(f"  - {result['batter1']}: {result['comparison']['strike_rate'][result['batter1']]}")
    print(f"  - {result['batter2']}: {result['comparison']['strike_rate'][result['batter2']]}")
    print(f"  - Better: {result['comparison']['strike_rate']['better']}")
else:
    print(result.get('error', 'No data found'))

# Test 3: Bowler vs Bowler
print("\n\n3️⃣  BOWLER vs BOWLER: B Kumar vs JJ Bumrah")
print("-"*70)
result = ai.get_player_head_to_head('B Kumar', 'JJ Bumrah')
if 'comparison' in result:
    print(f"Comparison: {result['bowler1']} vs {result['bowler2']}")
    print(f"\nWickets:")
    print(f"  - {result['bowler1']}: {result['comparison']['wickets'][result['bowler1']]}")
    print(f"  - {result['bowler2']}: {result['comparison']['wickets'][result['bowler2']]}")
    print(f"  - Difference: {result['comparison']['wickets']['difference']}")
    
    print(f"\nEconomy Rate:")
    print(f"  - {result['bowler1']}: {result['comparison']['economy'][result['bowler1']]}")
    print(f"  - {result['bowler2']}: {result['comparison']['economy'][result['bowler2']]}")
    print(f"  - Better (Lower): {result['comparison']['economy']['better']}")
else:
    print(result.get('error', 'No data found'))

# Test 4: Team Head-to-Head (original functionality)
print("\n\n4️⃣  TEAM HEAD-TO-HEAD: Mumbai Indians vs Chennai Super Kings")
print("-"*70)
result = ai.get_head_to_head("Mumbai Indians", "Chennai Super Kings")
print(f"Total Matches: {result['total_matches']}")
print(f"  - {result['team1']} Wins: {result['team1_wins']} ({result['team1_win_rate']}%)")
print(f"  - {result['team2']} Wins: {result['team2_wins']}")

print("\n" + "="*70)
print("✅ All tests completed successfully!")
print("="*70 + "\n")

"""Test queries with all new aliases to verify fixes work"""
import sys
sys.path.insert(0, '/Users/vikrant/Desktop/IPL_analytics_ai')

from openai_handler import OpenAIHandler, parse_query, find_player
import json

# Initialize handler
handler = OpenAIHandler()

print("=" * 70)
print("TESTING PLAYER ALIAS RESOLUTION")
print("=" * 70)

# Test various player queries
test_queries = [
    "kohli stats",
    "sachin stats",
    "ashwin stats",
    "narine stats",
    "chahal stats",
    "gayle stats",
    "bumrah last 5 matches",
    "kohli last 5 matches",
    "ashwin last 3 matches",
    "narine bowling last 5 matches",
    "rahane stats",
    "uthappa stats",
    "du plessis stats",
]

for query in test_queries:
    print(f"\n📝 Query: '{query}'")
    
    try:
        # Test find_player
        parsed = parse_query(query)
        print(f"   Parsed: {parsed}")
        
        if parsed.get('player1'):
            player_found = find_player(parsed['player1'])
            print(f"   Player resolved: {player_found}")
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)[:100]}")

print("\n" + "=" * 70)
print("TESTING TRENDS QUERIES (SKILL DETECTION)")
print("=" * 70)

# Test skill detection
test_players = ['V Kohli', 'JJ Bumrah', 'R Ashwin', 'RA Jadeja', 'RV Uthappa']

for player in test_players:
    try:
        skill = handler._get_player_primary_skill(player)
        print(f"✅ {player}: {skill}")
    except Exception as e:
        print(f"❌ {player}: {str(e)[:50]}")

print("\n" + "=" * 70)
print("DONE!")
print("=" * 70)

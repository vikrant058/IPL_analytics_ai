#!/usr/bin/env python3
"""Test record query improvements"""

import sys
sys.path.insert(0, '/Users/vikrant/Desktop/IPL_analytics_ai')

from openai_handler import CricketChatbot
from data_loader import IPLDataLoader

print("Loading data...")
loader = IPLDataLoader()
matches_df, deliveries_df = loader.load_data()

print("Initializing chatbot...")
chatbot = CricketChatbot(matches_df, deliveries_df, api_key="sk-test")

test_cases = [
    ("highest team total", None, "highest_team_score"),
    ("highest player total", None, "highest_score"),
    ("highest player score", None, "highest_score"),
    ("highest score in IPL", None, "highest_score"),
]

print("\n" + "="*70)
print("TESTING RECORD QUERY PARSING")
print("="*70)

for query, expected_player, expected_record in test_cases:
    result = chatbot.parse_query(query)
    player = result.get('player1')
    record = result.get('record_type')
    qtype = result.get('query_type')
    
    player_ok = "✓" if player == expected_player else "✗"
    record_ok = "✓" if record == expected_record else "✗"
    
    print(f"\n{player_ok}{record_ok} Query: '{query}'")
    print(f"   Type: {qtype} | Record: {record} (expected: {expected_record}) | Player: {player}")

print("\nAll tests completed!")

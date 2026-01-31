#!/usr/bin/env python3
"""Test full record responses"""

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
    ("highest score in IPL", None),
    ("highest team total", None),
    ("most runs in IPL", None),
    ("kohli highest score", "V Kohli"),
]

print("\n" + "="*70)
print("TESTING RECORD QUERIES")
print("="*70)

for query, expected_player in test_cases:
    print(f"\n{'─'*70}")
    print(f"Query: '{query}'")
    print(f"Expected Player: {expected_player or 'None (Overall Record)'}")
    print(f"{'─'*70}")
    
    response = chatbot.get_response(query)
    print(response[:500] + ("...[TRUNCATED]" if len(response) > 500 else ""))

print("\n" + "="*70)
print("All tests completed!")

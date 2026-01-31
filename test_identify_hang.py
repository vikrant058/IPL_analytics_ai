#!/usr/bin/env python3
"""Quick test to identify hanging point"""

import sys
sys.path.insert(0, '/Users/vikrant/Desktop/IPL_analytics_ai')

print("Step 1: Import...")
from openai_handler import CricketChatbot
from data_loader import IPLDataLoader

print("Step 2: Load...")
loader = IPLDataLoader()
matches_df, deliveries_df = loader.load_data()

print("Step 3: Init chatbot...")
chatbot = CricketChatbot(matches_df, deliveries_df, api_key="sk-test")

print("Step 4: Parse query...")
result = chatbot.parse_query("highest score in IPL")
print(f"  Query type: {result['query_type']}")
print(f"  Record type: {result['record_type']}")
print(f"  Player: {result['player1']}")

print("Step 5: Calling get_response...")
print("  (This might hang if it's trying to call GPT)")

try:
    response = chatbot.get_response("highest score in IPL")
    print("SUCCESS!")
    print(response[:200])
except KeyboardInterrupt:
    print("INTERRUPTED!")
except Exception as e:
    print(f"ERROR: {e}")

#!/usr/bin/env python3
"""Test record query fix"""

import sys
sys.path.insert(0, '/Users/vikrant/Desktop/IPL_analytics_ai')

print("Step 1: Importing modules...")
from data_loader import IPLDataLoader
print("  ✓ DataLoader imported")

print("Step 2: Loading data...")
loader = IPLDataLoader()
matches_df, deliveries_df = loader.load_data()
print(f"  ✓ Data loaded: {len(matches_df)} matches, {len(deliveries_df)} deliveries")

print("Step 3: Importing CricketChatbot...")
from openai_handler import CricketChatbot
print("  ✓ CricketChatbot imported")

print("Step 4: Initializing chatbot...")
chatbot = CricketChatbot(matches_df, deliveries_df, api_key="sk-test")
print("  ✓ Chatbot initialized")

print("\nStep 5: Testing parse_query...")
print("  Parsing: 'highest score in IPL'")
result = chatbot.parse_query("highest score in IPL")
print(f"  ✓ Query Type: {result.get('query_type')}")
print(f"  ✓ Record Type: {result.get('record_type')}")
print(f"  ✓ Player: {result.get('player1')}")

print("\nAll steps completed successfully!")


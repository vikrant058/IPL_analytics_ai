#!/usr/bin/env python3
"""Test end-to-end filter application in responses"""

import os
import sys

# Load API key
env_file = '/Users/vikrant/Desktop/IPL_analytics_ai/.env'
if os.path.exists(env_file):
    with open(env_file) as f:
        for line in f:
            if line.startswith('OPENAI_API_KEY'):
                os.environ['OPENAI_API_KEY'] = line.split('=')[1].strip()

from data_loader import IPLDataLoader
from openai_handler import CricketChatbot

# Load data
print("📊 Loading IPL data...")
loader = IPLDataLoader()
matches_df, deliveries_df = loader.load_data()
print(f"✅ Loaded: {len(matches_df)} matches, {len(deliveries_df)} deliveries\n")

# Initialize chatbot
print("🤖 Initializing chatbot...")
chatbot = CricketChatbot(matches_df, deliveries_df)
print("✅ Chatbot ready\n")

# Test queries that should now work with filters
test_queries = [
    "kohli in powerplay",
    "bumrah in death overs",
    "kohli vs bumrah in powerplay",
]

print("🧪 Testing filter application in responses:\n")
print("=" * 80)

for query in test_queries:
    print(f"\n📝 Query: '{query}'")
    print("-" * 40)
    try:
        response = chatbot.get_response(query)
        print(response[:300] + "..." if len(response) > 300 else response)
    except Exception as e:
        print(f"❌ Error: {str(e)[:200]}")
    print()

print("=" * 80)
print("\n✅ Test complete!")

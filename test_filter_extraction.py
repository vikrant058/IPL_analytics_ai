#!/usr/bin/env python3
"""Test filter extraction directly (without API calls)"""

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

# Test queries - Focus on filter extraction keyword matching
test_queries = [
    "kohli in powerplay",
    "bumrah in death overs",
    "kohli vs bumrah in powerplay",
    "rohit in death overs",
    "virat chasing",
    "sky in middle overs",
    "bumrah vs pace",
    "kohli vs bumrah in chasing"
]

print("🧪 Testing filter extraction (fallback parser):\n")
print("=" * 80)

for query in test_queries:
    # Use fallback parser directly to avoid API calls
    filters = chatbot._extract_filter_keywords(query)
    player1 = chatbot._resolve_player_name(query)
    player2 = None
    
    # Check for player 2
    if ' vs ' in query.lower():
        parts = query.lower().split(' vs ')
        if len(parts) >= 2:
            player2 = chatbot._resolve_player_name(parts[1])
    
    print(f"\n📝 Query: '{query}'")
    print(f"   player1: {player1}")
    print(f"   player2: {player2}")
    print(f"   match_phase: {filters.get('match_phase')}")
    print(f"   match_situation: {filters.get('match_situation')}")
    print(f"   bowler_type: {filters.get('bowler_type')}")
    print(f"   vs_conditions: {filters.get('vs_conditions')}")
    print(f"   batter_role: {filters.get('batter_role')}")

print("\n" + "=" * 80)
print("\n✅ Fallback filter extraction test complete!")

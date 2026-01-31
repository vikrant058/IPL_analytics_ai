#!/usr/bin/env python3
"""Quick test to verify the fixes work"""
import sys
sys.path.insert(0, '/Users/vikrant/Desktop/IPL_analytics_ai')

# Avoid OpenAI API calls
import os
os.environ['OPENAI_API_KEY'] = 'sk-test-key'

from data_loader import IPLDataLoader
from openai_handler import CricketChatbot

# Load data
loader = IPLDataLoader()
matches_df, deliveries_df = loader.load_data()

# Initialize chatbot
chatbot = CricketChatbot(matches_df, deliveries_df, api_key='sk-test-key')

# Test queries
test_queries = [
    "kohli last 5 matches",
    "kohli last 5 innings",
    "bumrah last 10 matches",
    "sachin last 5 matches",
]

print("Testing parse_query with new player resolution:")
print("=" * 70)

for query in test_queries:
    try:
        result = chatbot.parse_query(query)
        player = result.get('player1', 'Unknown')
        time_period = result.get('time_period', 'Unknown')
        query_type = result.get('query_type', 'Unknown')
        print(f"✅ '{query:30}' -> Player: {player:20} Type: {query_type:10} Period: {time_period}")
    except Exception as e:
        print(f"❌ '{query:30}' -> ERROR: {str(e)[:50]}")

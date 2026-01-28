#!/usr/bin/env python3
"""Test query parsing"""

from data_loader import IPLDataLoader
from openai_handler import CricketChatbot
import os
import json

# Load data
loader = IPLDataLoader()
loader.load_data()

# Initialize chatbot
api_key = os.getenv('OPENAI_API_KEY')
chatbot = CricketChatbot(loader.matches_df, loader.deliveries_df, api_key)

# Test queries
test_queries = [
    "virat kohli 2025",
    "kohli statistics",
    "rohit sharma powerplay",
    "bumrah vs siraj",
    "sky chasing performance"
]

print("🎯 Testing Query Parsing:\n")
for query in test_queries:
    parsed = chatbot.parse_query(query)
    print(f"Query: {query}")
    print(f"  player1: {parsed.get('player1')}")
    print(f"  player2: {parsed.get('player2')}")
    print(f"  query_type: {parsed.get('query_type')}")
    print(f"  match_phase: {parsed.get('match_phase')}")
    print(f"  match_situation: {parsed.get('match_situation')}")
    print(f"  seasons: {parsed.get('seasons')}")
    print(f"  interpretation: {parsed.get('interpretation')}")
    print()

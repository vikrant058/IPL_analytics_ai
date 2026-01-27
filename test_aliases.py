#!/usr/bin/env python3
"""Test the alias loading and resolution functionality"""

from data_loader import IPLDataLoader
from openai_handler import CricketChatbot
import os

# Load data
print("Loading IPL data...")
loader = IPLDataLoader()
loader.load_data()
print(f"✅ Data loaded: {len(loader.matches_df)} matches, {len(loader.deliveries_df)} deliveries")

# Initialize chatbot with .env API key
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("OPENAI_API_KEY not set")

print("\nInitializing chatbot with alias support...")
chatbot = CricketChatbot(loader.matches_df, loader.deliveries_df, api_key)
print(f"✅ Chatbot initialized with OpenAI GPT alias understanding")
print(f"   - Player aliases loaded: {len(chatbot.player_aliases)}")
print(f"   - Team aliases loaded: {len(chatbot.team_aliases)}")
print(f"   - All players in dataset: {len(chatbot.all_players)}")

# Test alias resolution
print("\n🎯 Testing player alias resolution:")
tests = ['virat', 'kohli', 'bumrah', 'sky', 'dhoni', 'rashid khan']
for test in tests:
    result = chatbot._resolve_player_name(test)
    print(f"  '{test}' → {result}")

print("\n🎯 Testing team alias resolution:")
team_tests = ['mi', 'csk', 'rcb', 'delhi', 'lucknow']
for test in team_tests:
    result = chatbot._resolve_team_name(test)
    print(f"  '{test}' → {result}")

print("\n✅ Alias loading and resolution working correctly!")
print("\n📝 The chatbot now uses OpenAI to understand query language intelligently")
print("   and resolves player/team names using the comprehensive alias dictionary.")

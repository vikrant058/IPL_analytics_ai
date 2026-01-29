#!/usr/bin/env python3
"""Simple test to verify filter extraction works correctly"""

from data_loader import IPLDataLoader
from openai_handler import CricketChatbot
import os

# Read API key from .env file
api_key = None
if os.path.exists('.env'):
    with open('.env', 'r') as f:
        for line in f:
            if line.startswith('OPENAI_API_KEY='):
                api_key = line.split('=')[1].strip()
                break

if not api_key:
    print("❌ API key not found in .env")
    exit(1)

# Load data
print("Loading IPL data...")
loader = IPLDataLoader()
matches_df, deliveries_df = loader.load_data()

# Initialize chatbot
print("Initializing chatbot...")
chatbot = CricketChatbot(matches_df, deliveries_df, api_key)

# Test filter extraction
test_cases = [
    ("kohli in powerplay", "Batter + match_phase"),
    ("kohli vs csk in 2024", "Batter vs team + year"),
    ("bumrah at wankhede in death overs", "Bowler + ground + phase"),
    ("kohli chasing in powerplay 2024", "Batter + situation + phase + year"),
    ("sky vs left hander", "Batter + handedness"),
    ("bumrah at home", "Bowler + match_type"),
    ("kohli vs bumrah in chinnaswamy", "H2H + ground"),
    ("sharma inning 1", "Batter + inning"),
    ("virat against pace", "Batter + vs_conditions"),
]

print("\n" + "=" * 80)
print("FILTER EXTRACTION TEST")
print("=" * 80)

success_count = 0
for query, description in test_cases:
    filters = chatbot._extract_filter_keywords(query)
    has_filters = bool(filters)
    status = "✅" if has_filters else "⚠️ "
    
    print(f"\n{status} {description}")
    print(f"   Query: '{query}'")
    print(f"   Filters: {filters if has_filters else 'None'}")
    
    if has_filters:
        success_count += 1

print("\n" + "=" * 80)
print(f"✅ Filter extraction working: {success_count}/{len(test_cases)} tests detected filters")
print("=" * 80)

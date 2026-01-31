#!/usr/bin/env python3
"""Debug script to test 'kohli last 5 matches' query"""

import sys
from openai_handler import OpenAIQueryHandler

# Initialize handler
handler = OpenAIQueryHandler()

# Test query
query = "kohli last 5 matches"
print(f"\n{'='*60}")
print(f"Testing Query: {query}")
print(f"{'='*60}\n")

# Step 1: Test parsing
parsed = handler.parse_query(query)
print("STEP 1: Parse Query Result")
print(f"  player1: {parsed.get('player1')}")
print(f"  time_period: {parsed.get('time_period')}")
print(f"  query_type: {parsed.get('query_type')}")
print(f"  interpretation: {parsed.get('interpretation')}")

# Step 2: Test filter extraction
filters = handler._extract_filter_keywords(query)
print(f"\nSTEP 2: Extract Filters Result")
print(f"  time_period: {filters.get('time_period')}")

# Step 3: Test get_last_n_innings
player = parsed.get('player1')
if player:
    innings_data = handler.stats_engine.get_last_n_innings(player, 5)
    print(f"\nSTEP 3: Get Last 5 Innings for {player}")
    print(f"  Innings count: {len(innings_data)}")
    if innings_data:
        print(f"  First inning: {innings_data[0]}")
    else:
        print(f"  ❌ NO INNINGS DATA RETURNED")

# Step 4: Get actual response
print(f"\n{'='*60}")
print(f"STEP 4: Full Response")
print(f"{'='*60}\n")
response = handler.get_response(query)
print(response)

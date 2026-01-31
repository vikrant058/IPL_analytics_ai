#!/usr/bin/env python3
"""Quick test of optimized query parsing"""

import sys
sys.path.insert(0, '/Users/vikrant/Desktop/IPL_analytics_ai')

from openai_handler import CricketChatbot
from data_loader import IPLDataLoader

print("=" * 80)
print("TESTING OPTIMIZED QUERY PARSING (NO GPT CALLS)")
print("=" * 80)
print()

try:
    loader = IPLDataLoader()
    matches_df, deliveries_df = loader.load_data()
    handler = CricketChatbot(matches_df, deliveries_df)
    
    # Test 1: kohli last 5 matches
    print("TEST 1: 'kohli last 5 matches'")
    print("-" * 80)
    query1 = "kohli last 5 matches"
    parsed1 = handler.parse_query(query1)
    print(f"Player: {parsed1.get('player1')}")
    print(f"Time Period: {parsed1.get('time_period')}")
    print(f"Query Type: {parsed1.get('query_type')}")
    print()
    
    # Test 2: bumrah last 10 matches
    print("TEST 2: 'bumrah last 10 matches'")
    print("-" * 80)
    query2 = "bumrah last 10 matches"
    parsed2 = handler.parse_query(query2)
    print(f"Player: {parsed2.get('player1')}")
    print(f"Time Period: {parsed2.get('time_period')}")
    print(f"Query Type: {parsed2.get('query_type')}")
    print()
    
    # Test 3: sky last 5 innings
    print("TEST 3: 'sky last 5 innings'")
    print("-" * 80)
    query3 = "sky last 5 innings"
    parsed3 = handler.parse_query(query3)
    print(f"Player: {parsed3.get('player1')}")
    print(f"Time Period: {parsed3.get('time_period')}")
    print(f"Query Type: {parsed3.get('query_type')}")
    print()
    
    # Test 4: Get actual response for kohli
    print("TEST 4: Response for 'kohli last 5 matches'")
    print("-" * 80)
    response1 = handler.get_response(query1)
    print(response1[:300])
    print()
    
    print("✅ ALL TESTS COMPLETED - NO TIMEOUT!")
    
except Exception as e:
    print(f"❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()

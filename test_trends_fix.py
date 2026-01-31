#!/usr/bin/env python3
"""Test the fixed trends query functionality"""

import sys
sys.path.insert(0, '/Users/vikrant/Desktop/IPL_analytics_ai')

from openai_handler import CricketChatbot
from data_loader import IPLDataLoader

print("=" * 80)
print("TESTING FIXED TRENDS QUERY FUNCTIONALITY")
print("=" * 80)
print()

try:
    # Load data
    loader = IPLDataLoader()
    matches_df, deliveries_df = loader.load_data()
    
    # Initialize handler
    handler = CricketChatbot(matches_df, deliveries_df)
    
    # Test 1: Query parsing for "kohli in last 5 matches"
    print("TEST 1: Query Parsing for 'kohli in last 5 matches'")
    print("-" * 80)
    query1 = "kohli in last 5 matches"
    parsed1 = handler.parse_query(query1)
    print(f"Query: '{query1}'")
    print(f"  player1: {parsed1.get('player1')}")
    print(f"  time_period: {parsed1.get('time_period')}")
    print(f"  query_type: {parsed1.get('query_type')}")
    print()
    
    # Test 2: Query parsing for "bumrah in last 10 matches"
    print("TEST 2: Query Parsing for 'bumrah in last 10 matches'")
    print("-" * 80)
    query2 = "bumrah in last 10 matches"
    parsed2 = handler.parse_query(query2)
    print(f"Query: '{query2}'")
    print(f"  player1: {parsed2.get('player1')}")
    print(f"  time_period: {parsed2.get('time_period')}")
    print(f"  query_type: {parsed2.get('query_type')}")
    print()
    
    # Test 3: Verify primary skill detection
    print("TEST 3: Primary Skill Detection")
    print("-" * 80)
    bumrah = handler.stats_engine.find_player("Bumrah")
    kohli = handler.stats_engine.find_player("Kohli")
    
    if bumrah:
        bumrah_skill = handler._get_player_primary_skill(bumrah)
        print(f"Bumrah primary skill: {bumrah_skill} (should be 'bowler')")
    
    if kohli:
        kohli_skill = handler._get_player_primary_skill(kohli)
        print(f"Kohli primary skill: {kohli_skill} (should be 'batter')")
    print()
    
    # Test 4: Get actual response for kohli
    print("TEST 4: Getting Kohli Trends Response")
    print("-" * 80)
    response_kohli = handler.get_response(query1)
    print("Response preview (first 500 chars):")
    print(response_kohli[:500])
    print()
    
    # Test 5: Get actual response for bumrah
    print("TEST 5: Getting Bumrah Bowling Trends Response")
    print("-" * 80)
    response_bumrah = handler.get_response(query2)
    print("Response preview (first 500 chars):")
    print(response_bumrah[:500])
    print()
    
    print("=" * 80)
    print("✅ ALL TESTS COMPLETED")
    print("=" * 80)
    
except Exception as e:
    print(f"❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

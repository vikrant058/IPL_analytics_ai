#!/usr/bin/env python3
"""Debug app alias loading and query flow"""

import sys
sys.path.insert(0, '/Users/vikrant/Desktop/IPL_analytics_ai')

from openai_handler import CricketChatbot
from data_loader import IPLDataLoader

print("=" * 80)
print("DEBUGGING ALIAS LOADING AND QUERY FLOW")
print("=" * 80)
print()

try:
    loader = IPLDataLoader()
    matches_df, deliveries_df = loader.load_data()
    handler = CricketChatbot(matches_df, deliveries_df)
    
    # Test 1: Check if sachin is in aliases NOW
    print("TEST 1: Sachin in Aliases After Reload")
    print("-" * 80)
    aliases = handler.player_aliases
    print(f"Total aliases loaded: {len(aliases)}")
    
    sachin_check = 'sachin' in aliases
    tendulkar_check = 'tendulkar' in aliases
    print(f"'sachin' in aliases: {sachin_check}")
    print(f"'tendulkar' in aliases: {tendulkar_check}")
    
    if sachin_check:
        print(f"'sachin' maps to: {aliases['sachin']}")
    if tendulkar_check:
        print(f"'tendulkar' maps to: {aliases['tendulkar']}")
    
    print()
    
    # Test 2: Parse sachin tendulkar query
    print("TEST 2: Query Parsing for 'sachin tendulkar'")
    print("-" * 80)
    query = "sachin tendulkar"
    parsed = handler.parse_query(query)
    print(f"Query: '{query}'")
    print(f"  player1: {parsed.get('player1')}")
    print(f"  query_type: {parsed.get('query_type')}")
    print(f"  interpretation: {parsed.get('interpretation')}")
    print()
    
    # Test 3: Parse kohli last 5 matches query
    print("TEST 3: Query Parsing for 'kohli last 5 matches'")
    print("-" * 80)
    query2 = "kohli last 5 matches"
    parsed2 = handler.parse_query(query2)
    print(f"Query: '{query2}'")
    print(f"  player1: {parsed2.get('player1')}")
    print(f"  time_period: {parsed2.get('time_period')}")
    print(f"  query_type: {parsed2.get('query_type')}")
    print()
    
    # Test 4: Get response for sachin tendulkar
    print("TEST 4: Response for 'sachin tendulkar'")
    print("-" * 80)
    response = handler.get_response(query)
    print(response[:400] if len(response) > 400 else response)
    print()
    
    # Test 5: Get response for kohli last 5 matches
    print("TEST 5: Response for 'kohli last 5 matches'")
    print("-" * 80)
    response2 = handler.get_response(query2)
    print(response2[:400] if len(response2) > 400 else response2)
    
except Exception as e:
    print(f"❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()

#!/usr/bin/env python3
"""Debug the kohli and sachin query issues - simplified"""

import sys
sys.path.insert(0, '/Users/vikrant/Desktop/IPL_analytics_ai')

from openai_handler import CricketChatbot
from data_loader import IPLDataLoader

print("=" * 80)
print("DEBUGGING ISSUES - SIMPLIFIED")
print("=" * 80)
print()

try:
    loader = IPLDataLoader()
    matches_df, deliveries_df = loader.load_data()
    handler = CricketChatbot(matches_df, deliveries_df)
    
    # Test 1: kohli last 5 matches - Full response
    print("TEST 1: 'kohli last 5 matches' - Full Response")
    print("-" * 80)
    query1 = "kohli last 5 matches"
    response1 = handler.get_response(query1)
    print(response1)
    print()
    print()
    
    # Test 2: sachin - Full response
    print("TEST 2: 'sachin stats' - Full Response")
    print("-" * 80)
    query2 = "sachin stats"
    response2 = handler.get_response(query2)
    print(response2)
    print()
    print()
    
    # Test 3: Check sachin in dataset
    print("TEST 3: Sachin in Dataset")
    print("-" * 80)
    sachin_found = handler.stats_engine.find_player("Sachin")
    print(f"find_player('Sachin'): {sachin_found}")
    
    sachin_found2 = handler.stats_engine.find_player("SR Tendulkar")
    print(f"find_player('SR Tendulkar'): {sachin_found2}")
    print()
    
    # Test 4: Check if sachin in aliases
    print("TEST 4: Sachin in Player Aliases")
    print("-" * 80)
    aliases = handler.player_aliases
    print(f"Total aliases loaded: {len(aliases)}")
    
    # Check what players ARE in aliases
    players_in_aliases = set(aliases.values())
    print(f"Total unique players in aliases: {len(players_in_aliases)}")
    print(f"Sample players in aliases: {list(players_in_aliases)[:5]}")
    
    # Is sachin in there?
    sachin_variations = ['sachin', 'tendulkar', 'sr tendulkar']
    for var in sachin_variations:
        if var in aliases:
            print(f"✅ '{var}' is in aliases -> {aliases[var]}")
        else:
            print(f"❌ '{var}' is NOT in aliases")
    
except Exception as e:
    print(f"❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()

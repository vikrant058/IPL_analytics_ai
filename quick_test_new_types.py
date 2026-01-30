#!/usr/bin/env python3
"""Quick test of new query type implementations"""

import sys
sys.path.insert(0, '/Users/vikrant/Desktop/IPL_analytics_ai')

from openai_handler import OpenAIHandler

def test_new_query_types():
    """Test new query type implementations"""
    handler = OpenAIHandler()
    
    tests = [
        ("kohli records", "RECORDS"),
        ("top 10 run scorers", "RANKINGS"),
        ("kohli at wankhede", "GROUND_INSIGHTS"),
        ("kohli vs sharma", "COMPARATIVE"),
        ("predictions powerplay", "PREDICTIONS"),
        ("kohli current form", "FORM_GUIDE"),
    ]
    
    for query, query_type in tests:
        print(f"\n{'='*60}")
        print(f"TESTING: {query_type}")
        print(f"Query: {query}")
        print('='*60)
        try:
            response = handler.get_response(query)
            print(f"Response length: {len(response)} chars")
            print(f"Preview:\n{response[:300]}")
            print("✅ SUCCESS")
        except Exception as e:
            print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    test_new_query_types()

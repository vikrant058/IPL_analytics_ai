#!/usr/bin/env python3
"""
Comprehensive test suite for all 10 IPL chatbot query types
Tests: player_stats, head_to_head, team_comparison, trends, records, rankings, ground_insights, form_guide, comparative_analysis, predictions
"""

import sys
import time
from openai_handler import OpenAIHandler

def test_chatbot_queries():
    """Test comprehensive set of queries for all query types"""
    
    print("=" * 80)
    print("IPL ANALYTICS CHATBOT - COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    
    try:
        handler = OpenAIHandler()
        print("✅ Chatbot initialized successfully\n")
    except Exception as e:
        print(f"❌ Failed to initialize chatbot: {e}")
        return False
    
    # Test queries organized by type
    test_cases = {
        "PLAYER STATS (working)": [
            "kohli",
            "bumrah bowling stats",
            "virat in powerplay",
            "rohit vs MI",
        ],
        
        "HEAD-TO-HEAD (working)": [
            "kohli vs bumrah",
            "virat vs boult",
        ],
        
        "TEAM COMPARISON (working)": [
            "RCB vs MI",
            "CSK performance",
        ],
        
        "TRENDS - Last N Innings/Matches (ENHANCED)": [
            "kohli last 5 innings",
            "bumrah last 5 matches",
            "virat last 10 innings",
            "sky last 3 matches",
        ],
        
        "RECORDS (ENHANCED)": [
            "kohli records",
            "bumrah highest wickets",
            "virat highest score",
            "dhoni all records",
        ],
        
        "RANKINGS (ENHANCED)": [
            "top 10 run scorers",
            "best bowlers by economy",
            "highest strike rates",
            "top wicket takers 2024",
            "best batting averages",
        ],
        
        "GROUND INSIGHTS (ENHANCED)": [
            "kohli at wankhede",
            "bumrah at eden gardens",
            "virat performance at chinnaswamy",
        ],
        
        "FORM GUIDE (ENHANCED)": [
            "kohli current form",
            "is bumrah in form",
            "virat recent performance",
            "sky form analysis",
        ],
        
        "COMPARATIVE ANALYSIS (ENHANCED)": [
            "kohli vs sharma comparison",
            "bumrah vs chahal",
            "virat vs dhoni head to head",
        ],
        
        "PREDICTIONS (ENHANCED)": [
            "predicted top scorer",
            "bowling recommendations",
            "powerplay strategy",
            "death overs analysis",
        ],
    }
    
    total_tests = 0
    passed_tests = 0
    
    for category, queries in test_cases.items():
        print(f"\n{'=' * 80}")
        print(f"TESTING: {category}")
        print('=' * 80)
        
        for query in queries:
            total_tests += 1
            try:
                print(f"\n📍 Query {total_tests}: {query}")
                response = handler.get_response(query)
                
                if response and len(response) > 10:  # Valid response
                    passed_tests += 1
                    print(f"✅ PASS - Response length: {len(response)} chars")
                    # Print first 200 chars of response for verification
                    preview = response[:200].replace('\n', ' ')
                    print(f"   Preview: {preview}...")
                else:
                    print(f"⚠️  PARTIAL - Response too short or empty")
            
            except Exception as e:
                print(f"❌ FAIL - Error: {str(e)[:100]}")
            
            time.sleep(0.5)  # Rate limiting
    
    # Summary
    print(f"\n{'=' * 80}")
    print("TEST SUMMARY")
    print('=' * 80)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed/Partial: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests / total_tests * 100):.1f}%")
    
    if passed_tests >= total_tests * 0.85:  # 85% pass rate
        print(f"\n✅ TEST SUITE PASSED - {passed_tests}/{total_tests} tests successful")
        return True
    else:
        print(f"\n⚠️  TEST SUITE PARTIAL - {passed_tests}/{total_tests} tests successful")
        return False

if __name__ == "__main__":
    success = test_chatbot_queries()
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""Test concise record answers feature"""

import sys
sys.path.insert(0, '.')

from data_loader import IPLDataLoader
from openai_handler import CricketChatbot

def run_tests():
    loader = IPLDataLoader()
    matches_df, deliveries_df = loader.load_data()
    chatbot = CricketChatbot(matches_df, deliveries_df, api_key='sk-test')
    
    # Comprehensive test suite
    test_cases = [
        # Concise single-fact queries
        ('kohli highest score', 'records', 'concise'),
        ('bumrah most wickets', 'records', 'concise'),
        ('sachin total runs', 'records', 'concise'),
        
        # Comprehensive record queries
        ('kohli records', 'records', 'comprehensive'),
        ('bumrah bowling records', 'records', 'comprehensive'),
        
        # Overall records (league-wide)
        ('highest score in ipl', 'records', 'overall'),
        ('most runs in ipl', 'records', 'overall'),
        ('highest team score', 'records', 'overall'),
        
        # Other query types (should still work)
        ('kohli last 5 matches', 'trends', 'other'),
        ('sachin stats', 'player_stats', 'other'),
    ]
    
    print('COMPREHENSIVE TEST SUITE - RECORD QUERIES')
    print('='*70)
    
    passed = 0
    failed = 0
    
    for query, expected_type, response_type in test_cases:
        try:
            parsed = chatbot.parse_query(query)
            response = chatbot.get_response(query)
            query_type = parsed.get('query_type')
            record_type = parsed.get('record_type')
            player = parsed.get('player1')
            
            # Verify query type matches expected
            if query_type == expected_type:
                status = '✓'
                passed += 1
            else:
                status = '✗'
                failed += 1
            
            print(f'\n{status} Query: {query}')
            print(f'  Type: {query_type} | Record: {record_type} | Player: {player}')
            print(f'  Response Type: {response_type}')
            print(f'  Response: {response[:100]}...')
        except Exception as e:
            failed += 1
            print(f'\n✗ Query: {query}')
            print(f'  ERROR: {str(e)[:150]}')
    
    print('\n' + '='*70)
    print(f'RESULTS: {passed}/{len(test_cases)} tests passed')
    
    # Detailed test for concise vs comprehensive
    print('\n' + '='*70)
    print('DETAILED TEST: CONCISE vs COMPREHENSIVE')
    print('='*70)
    
    print('\n1. CONCISE SINGLE-FACT QUERIES (should return one-liner):')
    concise_queries = [
        'kohli highest score',
        'bumrah most wickets',
        'sachin total runs',
        'bumrah best figures',
    ]
    
    for query in concise_queries:
        response = chatbot.get_response(query)
        is_concise = response.count('\n') <= 2 and '|' not in response
        status = '✓' if is_concise else '✗'
        print(f'  {status} {query}')
        print(f'     {response[:100]}')
    
    print('\n2. COMPREHENSIVE RECORD QUERIES (should return full table):')
    comprehensive_queries = [
        'kohli records',
        'bumrah bowling records',
    ]
    
    for query in comprehensive_queries:
        response = chatbot.get_response(query)
        is_comprehensive = '|' in response or '\n' > 5
        status = '✓' if is_comprehensive else '✗'
        print(f'  {status} {query}')
        print(f'     {response[:100]}...')

if __name__ == '__main__':
    run_tests()

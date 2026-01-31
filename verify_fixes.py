#!/usr/bin/env python3
"""
Quick test of player resolution fixes
Run this to verify the fixes work before testing in the browser
"""
import sys
import os
sys.path.insert(0, '/Users/vikrant/Desktop/IPL_analytics_ai')
os.environ['OPENAI_API_KEY'] = 'sk-test-key'

import json

# Test 1: Player alias resolution
print("=" * 70)
print("TEST 1: Player Alias Resolution")
print("=" * 70)

with open('/Users/vikrant/Desktop/IPL_analytics_ai/player_aliases.json', 'r') as f:
    data = json.load(f)

canonical_aliases = data.get("aliases", {})

# Build alias map
alias_map = {}
for canonical_name, alias_list in canonical_aliases.items():
    for alias in alias_list:
        alias_lower = alias.lower()
        if alias_lower not in alias_map:
            alias_map[alias_lower] = []
        alias_map[alias_lower].append(canonical_name)

def resolve_player(query):
    """Simulate the actual resolution logic"""
    query_lower = query.lower()
    matches = []
    for alias, players_list in alias_map.items():
        if alias in query_lower:
            for full_name in players_list:
                player_alias_count = len(canonical_aliases.get(full_name, []))
                matches.append((alias, full_name, len(alias), player_alias_count))
    
    if matches:
        matches.sort(key=lambda x: (-x[2], -x[3]))
        return matches[0][1]
    return None

test_cases = [
    ("kohli", "V Kohli"),
    ("sachin", "SR Tendulkar"),
    ("bumrah", "JJ Bumrah"),
    ("ashwin", "R Ashwin"),
    ("narine", "SP Narine"),
    ("chahal", "YS Chahal"),
]

print("\nTesting player resolution:")
for query, expected in test_cases:
    result = resolve_player(query)
    status = "✅" if result == expected else "❌"
    print(f"{status} '{query:15}' -> {result:20} (expected: {expected})")

# Test 2: Parse query with time period
print("\n" + "=" * 70)
print("TEST 2: Parse Query with Time Period")
print("=" * 70)

import re

pattern = r'last\s+(\d+)\s+(match(?:es)?|innings?|games?)'

test_queries = [
    ("kohli last 5 matches", True, "5", "matches"),
    ("kohli last 5 innings", True, "5", "innings"),
    ("bumrah last 10 matches", True, "10", "matches"),
    ("sachin stats", False, None, None),
    ("ashwin bowling", False, None, None),
]

print("\nTesting time period regex:")
for query, should_match, expected_num, expected_period in test_queries:
    match = re.search(pattern, query.lower())
    if should_match:
        if match:
            num = match.group(1)
            period = match.group(2)
            status = "✅" if (num == expected_num and period == expected_period) else "❌"
            print(f"{status} '{query:30}' -> {num} {period}")
        else:
            print(f"❌ '{query:30}' -> NO MATCH (expected: {expected_num} {expected_period})")
    else:
        if not match:
            print(f"✅ '{query:30}' -> No match (correct)")
        else:
            print(f"❌ '{query:30}' -> Unexpected match: {match.group(0)}")

# Test 3: Combined: Player + Time Period
print("\n" + "=" * 70)
print("TEST 3: Combined - Player Resolution + Time Period")
print("=" * 70)

combined_tests = [
    ("kohli last 5 matches", "V Kohli", "last 5 matches"),
    ("sachin last 5 matches", "SR Tendulkar", "last 5 matches"),
    ("bumrah last 10 matches", "JJ Bumrah", "last 10 matches"),
    ("ashwin last 3 matches", "R Ashwin", "last 3 matches"),
]

print("\nTesting player + time period together:")
for query, expected_player, expected_time in combined_tests:
    player = resolve_player(query)
    time_match = re.search(pattern, query.lower())
    time_str = f"{time_match.group(1)} {time_match.group(2)}" if time_match else "NO MATCH"
    
    player_ok = player == expected_player
    time_ok = time_str == expected_time
    status = "✅" if (player_ok and time_ok) else "❌"
    
    print(f"{status} '{query:30}' -> Player: {player:20} Time: {time_str}")

print("\n" + "=" * 70)
print("All tests complete!")
print("=" * 70)

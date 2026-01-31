#!/usr/bin/env python3
"""Test the regex pattern fix for 'last N matches/innings' extraction"""

import re

print("=" * 70)
print("Testing Time Period Regex Pattern Fix")
print("=" * 70)
print()

# Test cases
test_cases = [
    ("kohli in last 5 matches", "last 5 matches"),
    ("bumrah in last 10 matches", "last 10 matches"),
    ("kohli last 5 innings", "last 5 innings"),
    ("sky in last 3 games", "last 3 games"),
    ("pant in last 7 match", "last 7 match"),  # singular
    ("virat in last 2 inning", "last 2 inning"),  # singular
]

pattern = r'last\s+(\d+)\s+(matches?|innings?|games?)'

print(f"Pattern: {pattern}\n")

all_pass = True
for query, expected in test_cases:
    match = re.search(pattern, query.lower())
    if match:
        extracted = match.group(0)
        status = "✅" if extracted == expected else "⚠️"
        print(f"{status} '{query}'")
        print(f"   Expected: '{expected}'")
        print(f"   Extracted: '{extracted}'")
        if extracted != expected:
            all_pass = False
    else:
        print(f"❌ '{query}' - NO MATCH")
        print(f"   Expected: '{expected}'")
        all_pass = False
    print()

print("=" * 70)
if all_pass:
    print("✅ ALL TESTS PASSED")
else:
    print("⚠️ Some tests failed or didn't match exactly")
print("=" * 70)

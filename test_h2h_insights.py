#!/usr/bin/env python3
"""Test H2H insights generation with intelligent rules"""

import os
from dotenv import load_dotenv
from data_loader import IPLDataLoader

load_dotenv('.env')
api_key = os.getenv('OPENAI_API_KEY')

loader = IPLDataLoader()
matches_df, deliveries_df = loader.load_data()

from openai_handler import CricketChatbot
chatbot = CricketChatbot(matches_df, deliveries_df, api_key)

print("="*70)
print("H2H INSIGHTS - Multiple Matchup Examples")
print("="*70)

# Test 1: High strike rate (aggressive)
print("\n1️⃣ AGGRESSIVE APPROACH (SR > 150):")
print("-" * 70)
response1 = chatbot._get_head_to_head_response("V Kohli", "JJ Bumrah")
print(response1)

# Test 2: Cautious approach (SR < 100)
print("\n\n2️⃣ CAUTIOUS/DEFENSIVE APPROACH (SR < 100):")
print("-" * 70)
response2 = chatbot._get_head_to_head_response("RG Sharma", "BA Stokes")
print(response2)

# Test 3: Different matchup
print("\n\n3️⃣ ANOTHER MATCHUP:")
print("-" * 70)
response3 = chatbot._get_head_to_head_response("SK Yadav", "R Ashwin")
print(response3)

print("\n" + "="*70)
print("✅ All Insights Generated with Intelligent Rules!")
print("="*70)

"""
Comprehensive test for chatbot filter extraction and query parsing.
Tests all primary and secondary variables with filter combinations.
"""

from data_loader import IPLDataLoader
from openai_handler import CricketChatbot

# Load data
loader = IPLDataLoader()
matches_df = loader.load_matches()
deliveries_df = loader.load_deliveries()

# Initialize chatbot
import os
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')

chatbot = CricketChatbot(matches_df, deliveries_df, api_key)

# Test cases following the user's requirements
test_queries = [
    # Primary variables - Batter
    ("kohli stats", "Single batter"),
    ("virat", "Single batter (alias)"),
    
    # Primary variables - Batter vs Team
    ("kohli vs csk", "Batter vs team"),
    ("sharma against mumbai", "Batter vs team (against)"),
    
    # Batter vs Team + Secondary Filters
    ("kohli vs csk in 2024", "Batter vs team + year"),
    ("kohli vs csk at wankhede", "Batter vs team + ground"),
    ("kohli vs mumbai in powerplay 2025", "Batter vs team + phase + year"),
    
    # Batter vs Bowler + Secondary Filters
    ("kohli vs bumrah", "Batter vs bowler (H2H)"),
    ("kohli vs bumrah in death overs", "Batter vs bowler + match phase"),
    ("kohli vs bumrah in 2024", "Batter vs bowler + year"),
    ("kohli vs bumrah at eden gardens 2024", "Batter vs bowler + ground + year"),
    ("virat vs bumrah in powerplay 2024 chasing", "Batter vs bowler + phase + year + situation"),
    
    # Batter with Situational Filters
    ("kohli chasing", "Batter + match situation"),
    ("sharma in powerplay defending", "Batter + phase + situation"),
    ("kohli batting first", "Batter + inning (batting first)"),
    ("sky in death overs chasing 2024", "Batter + phase + situation + year"),
    
    # Batter with Handedness Filter
    ("kohli vs left hander", "Batter + opponent handedness"),
    ("sharma against right handed bowler", "Batter + bowler handedness"),
    
    # Batter with Home/Away Filter
    ("kohli at home", "Batter + home filter"),
    ("rohit away", "Batter + away filter"),
    ("bumrah at home in death 2024", "Bowler + home + phase + year"),
    
    # Team Comparisons
    ("mumbai vs delhi", "Team vs team stats"),
    
    # Bowler Stats
    ("bumrah", "Single bowler"),
    ("jj bumrah stats", "Single bowler (full name)"),
    
    # Bowler with Filters
    ("bumrah in powerplay", "Bowler + phase"),
    ("bumrah vs batters in death overs", "Bowler + phase"),
    ("bumrah against right handed", "Bowler + batter handedness"),
    ("bumrah in 2024 powerplay", "Bowler + year + phase"),
    ("chahal at wankhede 2024", "Bowler + ground + year"),
    ("bumrah chasing 2024", "Bowler + situation + year"),
    
    # Complex multi-filter queries
    ("kohli vs bumrah at chinnaswamy in powerplay 2024", "H2H + ground + phase + year"),
    ("sky chasing in death overs vs pace 2025", "Batter + situation + phase + vs_condition + year"),
    ("bumrah vs left handed in powerplay at home 2024", "Bowler + handedness + phase + home + year"),
]

print("=" * 80)
print("COMPREHENSIVE CHATBOT FILTER TEST")
print("=" * 80)
print()

for i, (query, description) in enumerate(test_queries, 1):
    print(f"\n[Test {i}] {description}")
    print(f"Query: '{query}'")
    print("-" * 80)
    
    try:
        # First test filter extraction
        filters = chatbot._extract_filter_keywords(query)
        print(f"Extracted Filters: {filters if filters else 'None'}")
        
        # Then test query parsing
        parsed = chatbot.parse_query(query)
        print(f"\nQuery Parsing Result:")
        print(f"  Player1: {parsed.get('player1')}")
        print(f"  Player2: {parsed.get('player2')}")
        print(f"  Opposition Team: {parsed.get('opposition_team')}")
        print(f"  Query Type: {parsed.get('query_type')}")
        print(f"  Match Phase: {parsed.get('match_phase')}")
        print(f"  Match Situation: {parsed.get('match_situation')}")
        print(f"  Vs Conditions: {parsed.get('vs_conditions')}")
        print(f"  Ground: {parsed.get('ground')}")
        print(f"  Handedness: {parsed.get('handedness')}")
        print(f"  Inning: {parsed.get('inning')}")
        print(f"  Match Type: {parsed.get('match_type')}")
        print(f"  Seasons: {parsed.get('seasons')}")
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)

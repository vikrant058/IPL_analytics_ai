from data_loader import IPLDataLoader
from openai_handler import CricketChatbot
import os

loader = IPLDataLoader()
try:
    chatbot = CricketChatbot(loader.matches_df, loader.deliveries_df)
    
    test_queries = [
        "How many matches has CSK played?",
        "Total wins by Mumbai Indians",
        "Win percentage of RCB",
        "Which team has the highest win percentage?",
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")
        parsed = chatbot.parse_query(query)
        print(f"Query Type: {parsed.get('query_type')}")
        print(f"Opposition Team: {parsed.get('opposition_team')}")
        print(f"Ranking Metric: {parsed.get('ranking_metric')}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

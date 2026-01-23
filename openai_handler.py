"""
OpenAI LLM integration for natural language cricket analytics queries
"""

import json
import os
import pandas as pd
from typing import Dict, List, Tuple, Optional
from openai import OpenAI
from data_loader import IPLDataLoader
from stats_engine import StatsEngine

class CricketChatbot:
    """
    Chatbot for parsing natural language cricket queries and returning analytics
    Supports queries like: "kohli vs bumrah in chinnaswamy stadium"
    """
    
    def __init__(self, matches_df, deliveries_df, api_key: Optional[str] = None):
        """Initialize chatbot with IPL data and OpenAI API"""
        self.matches_df = matches_df
        self.deliveries_df = deliveries_df
        self.stats_engine = StatsEngine(matches_df, deliveries_df)
        
        # Set OpenAI API key
        if api_key:
            self.client = OpenAI(api_key=api_key)
        elif os.getenv('OPENAI_API_KEY'):
            self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        else:
            raise ValueError("OpenAI API key not provided. Set OPENAI_API_KEY environment variable.")
        
        # Get all unique players and venues for context
        self.all_players = self._get_all_players()
        self.all_venues = self._get_all_venues()
        self.all_teams = self._get_all_teams()
    
    def _get_all_players(self) -> List[str]:
        """Extract all unique player names from dataset"""
        batters = self.deliveries_df['batter'].unique().tolist()
        bowlers = self.deliveries_df['bowler'].unique().tolist()
        return list(set(batters + bowlers))
    
    def _get_all_venues(self) -> List[str]:
        """Extract all unique venues from dataset"""
        return self.matches_df['venue'].unique().tolist()
    
    def _get_all_teams(self) -> List[str]:
        """Extract all unique teams from dataset"""
        teams = pd.concat([self.matches_df['team1'], self.matches_df['team2']]).unique()
        return teams.tolist()
    
    def parse_query(self, query: str) -> Dict:
        """
        Parse natural language query using GPT to extract:
        - Player 1 name
        - Player 2 name
        - Venue (if mentioned)
        - Season/Year (if mentioned)
        - Query type (h2h, stats, comparison)
        """
        
        prompt = f"""
        Parse this cricket analytics query and extract the following information in JSON format:
        - player1: first player name (if mentioned)
        - player2: second player name (if mentioned)
        - venue: stadium/venue name (if mentioned)
        - seasons: list of years/seasons (e.g., [2025] or [2023, 2024] or null if not mentioned)
        - query_type: one of ['head_to_head', 'player_stats', 'team_comparison', 'general']
        
        Available players: {', '.join(self.all_players[:20])}... (and {len(self.all_players)-20} more)
        Available venues: {', '.join(self.all_venues)}
        Available teams: {', '.join(self.all_teams)}
        
        Query: "{query}"
        
        Response format:
        {{
            "player1": "string or null",
            "player2": "string or null", 
            "venue": "string or null",
            "seasons": [list of integers or null],
            "query_type": "string",
            "interpretation": "brief explanation of what user is asking"
        }}
        
        For years, extract any 4-digit numbers that represent IPL seasons (2007-2025).
        Return ONLY valid JSON, no other text.
        """
        
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Parse JSON response
        try:
            parsed = json.loads(response_text)
            return parsed
        except json.JSONDecodeError:
            return {
                "player1": None,
                "player2": None,
                "venue": None,
                "seasons": None,
                "query_type": "general",
                "interpretation": "Could not parse query clearly"
            }
    
    def get_response(self, query: str) -> str:
        """
        Main method: Takes user query and returns analytics response
        """
        
        # Parse the query
        parsed = self.parse_query(query)
        player1 = parsed.get('player1')
        player2 = parsed.get('player2')
        venue = parsed.get('venue')
        seasons = parsed.get('seasons')
        query_type = parsed.get('query_type')
        
        try:
            if query_type == 'head_to_head' and player1 and player2:
                return self._get_head_to_head_response(player1, player2, venue, seasons)
            elif query_type == 'player_stats' and player1:
                return self._get_player_stats_response(player1, seasons)
            elif query_type == 'team_comparison' and player1:
                return self._get_team_stats_response(player1)
            else:
                return f"I understood you're asking about: {parsed['interpretation']}\n\nPlease ask something like:\n- 'kohli vs bumrah in chinnaswamy'\n- 'virat kohli statistics in 2025'\n- 'mumbai indians performance'"
        
        except Exception as e:
            return f"Error processing query: {str(e)}\n\nPlease try again with a clearer query."
    
    def _get_head_to_head_response(self, player1: str, player2: str, venue: Optional[str] = None, seasons: List[int] = None) -> str:
        """Get head-to-head comparison between two players"""
        
        try:
            # Find actual player names using fuzzy matching
            found_player1 = self.stats_engine.find_player(player1)
            found_player2 = self.stats_engine.find_player(player2)
            
            if not found_player1 or not found_player2:
                return f"Could not find players. Searching for: {player1}, {player2}"
            
            # Build filters dict
            filters = {}
            if seasons:
                filters['seasons'] = seasons
            
            # Get H2H stats from stats engine
            h2h_data = self.stats_engine.get_player_head_to_head(found_player1, found_player2, filters if filters else None)
            
            if h2h_data.get('error'):
                return f"Could not find head-to-head data between {found_player1} and {found_player2}. They may not have faced each other."
            
            # Format response
            response = f"**Head-to-Head: {found_player1} vs {found_player2}**"
            if seasons:
                response += f" **({', '.join(str(s) for s in seasons)})**"
            response += "\n\n"
            
            response += f"📊 **Deliveries**: {h2h_data['deliveries']}\n"
            response += f"🏃 **Runs**: {h2h_data['runs']}\n"
            response += f"⚡ **Strike Rate**: {h2h_data['strike_rate']:.2f}\n"
            response += f"🎯 **Dot Balls**: {h2h_data.get('dot_balls', 'N/A')}\n"
            
            if venue:
                response += f"\n📍 **Venue**: {venue}\n"
            
            response += f"\n{h2h_data.get('summary', '')}"
            
            return response
        
        except Exception as e:
            return f"Error getting head-to-head data: {str(e)}"
    
    def _get_player_stats_response(self, player: str, seasons: List[int] = None) -> str:
        """Get player statistics for specific season(s) if provided"""
        
        try:
            # Find player with fuzzy matching
            found_player = self.stats_engine.find_player(player)
            if not found_player:
                return f"Player '{player}' not found in IPL dataset. Try searching for similar names."
            
            # Build filters
            filters = {}
            if seasons:
                filters['seasons'] = seasons
            
            # Get stats with optional season filter
            stats = self.stats_engine.get_player_stats(found_player, filters if filters else None)
            
            if not stats or 'error' in stats:
                season_text = f" in {seasons}" if seasons else ""
                return f"Player '{found_player}' has no data{season_text} in IPL dataset."
            
            response = f"**Player Profile: {found_player}**"
            if seasons:
                response += f" **({', '.join(str(s) for s in seasons)})**"
            response += "\n\n"
            
            if 'batting' in stats and stats['batting']:
                bat = stats['batting']
                response += f"🏏 **Batting Stats**\n"
                response += f"- Matches: {bat.get('matches', 0)}\n"
                response += f"- Innings: {bat.get('innings', 0)}\n"
                response += f"- Runs: {bat.get('runs', 0)}\n"
                response += f"- Average: {bat.get('average', 0):.2f}\n"
                response += f"- Strike Rate: {bat.get('strike_rate', 0):.2f}\n"
                response += f"- Highest Score: {bat.get('highest_score', 0)}\n"
                response += f"- Centuries: {bat.get('centuries', 0)}\n"
                response += f"- Fifties: {bat.get('fifties', 0)}\n"
                response += f"- Fours: {bat.get('fours', 0)}\n"
                response += f"- Sixes: {bat.get('sixes', 0)}\n\n"
            
            if 'bowling' in stats and stats['bowling']:
                bowl = stats['bowling']
                response += f"🎳 **Bowling Stats**\n"
                response += f"- Matches: {bowl.get('matches', 0)}\n"
                response += f"- Innings: {bowl.get('innings', 0)}\n"
                response += f"- Wickets: {bowl.get('wickets', 0)}\n"
                response += f"- Average: {bowl.get('average', 0):.2f}\n"
                response += f"- Economy: {bowl.get('economy', 0):.2f}\n"
                response += f"- Best Figures: {bowl.get('best_figures', 'N/A')}\n"
                response += f"- Maiden Overs: {bowl.get('maiden_overs', 0)}\n"
            
            return response
        
        except Exception as e:
            return f"Error getting player stats: {str(e)}"
    
    def _get_team_stats_response(self, team: str) -> str:
        """Get team statistics"""
        
        try:
            # Find team with fuzzy matching
            found_team = self.stats_engine.find_team(team)
            if not found_team:
                return f"Team '{team}' not found in IPL dataset."
            
            stats = self.stats_engine.get_team_stats(found_team)
            
            if not stats or 'error' in stats:
                return f"Team '{found_team}' not found in IPL dataset."
            
            response = f"**Team Profile: {found_team}**\n\n"
            response += f"🏆 **Performance**\n"
            response += f"- Total Matches: {stats.get('matches', 0)}\n"
            response += f"- Wins: {stats.get('wins', 0)}\n"
            response += f"- Win Rate: {stats.get('win_percentage', 0):.1f}%\n"
            
            return response
        
        except Exception as e:
            return f"Error getting team stats: {str(e)}"

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
        - Bowler type (Pace, Spin, Left-arm, Right-arm, etc.)
        - Match phase (Powerplay 0-6, Middle 6-16, Death 16-20)
        - Opposition team
        - Query type (h2h, stats, comparison)
        """
        
        prompt = f"""
        Parse this cricket analytics query and extract cricket-specific information in JSON format:
        
        REQUIRED FIELDS:
        - player1: first player name (if mentioned)
        - player2: second player name (if mentioned)
        - venue: stadium/venue name (if mentioned)
        - seasons: list of years/seasons (e.g., [2025] or [2023, 2024] or null)
        - query_type: one of ['head_to_head', 'player_stats', 'team_comparison', 'general']
        
        ADDITIONAL FILTERS:
        - bowler_type: null or one of ['pace', 'spin', 'left_arm', 'right_arm', 'off_spinner', 'leg_spinner', 'medium', 'fast']
        - match_phase: null or one of ['powerplay', 'middle_overs', 'death_overs'] (powerplay: 0-6 overs, middle: 6-15.6, death: 16+)
        - match_situation: null or one of ['batting_first', 'chasing', 'pressure_chase', 'comfortable_chase'] (batting first vs chasing; pressure: RRR>10, comfortable: RRR<8)
        - opposition_team: opposing team name (if mentioned)
        - batter_role: null or one of ['opener', 'middle_order', 'lower_order']
        - vs_conditions: null or one of ['vs_pace', 'vs_spin', 'home', 'away']
        - form_filter: null or one of ['recent', 'consistent', 'peak_performance']
        
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
            "bowler_type": "string or null",
            "match_phase": "string or null",
            "match_situation": "string or null",
            "opposition_team": "string or null",
            "batter_role": "string or null",
            "vs_conditions": "string or null",
            "form_filter": "string or null",
            "query_type": "string",
            "interpretation": "brief explanation of what user is asking"
        }}
        
        EXAMPLES:
        - "rohit's powerplay performance vs pace bowlers in 2024" 
          → player1: "Rohit Sharma", match_phase: "powerplay", vs_conditions: "vs_pace", seasons: [2024]
        - "compare bumrah and siraj in death overs" 
          → player1: "Bumrah", player2: "Siraj", match_phase: "death_overs", query_type: "head_to_head"
        - "virat kohli opening the innings" 
          → player1: "Virat Kohli", batter_role: "opener"
        - "rohit's chasing performance"
          → player1: "Rohit", match_situation: "chasing"
        - "kohli in pressure chases"
          → player1: "Kohli", match_situation: "pressure_chase"
        
        Return ONLY valid JSON, no other text.
        """
        
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=300
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
                "bowler_type": None,
                "match_phase": None,
                "match_situation": None,
                "opposition_team": None,
                "batter_role": None,
                "vs_conditions": None,
                "form_filter": None,
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
        bowler_type = parsed.get('bowler_type')
        match_phase = parsed.get('match_phase')
        match_situation = parsed.get('match_situation')
        opposition_team = parsed.get('opposition_team')
        batter_role = parsed.get('batter_role')
        vs_conditions = parsed.get('vs_conditions')
        form_filter = parsed.get('form_filter')
        query_type = parsed.get('query_type')
        
        try:
            if query_type == 'head_to_head' and player1 and player2:
                return self._get_head_to_head_response(player1, player2, venue, seasons, 
                                                        match_phase=match_phase, match_situation=match_situation,
                                                        bowler_type=bowler_type)
            elif query_type == 'player_stats' and player1:
                return self._get_player_stats_response(player1, seasons, 
                                                       match_phase=match_phase, match_situation=match_situation,
                                                       bowler_type=bowler_type,
                                                       batter_role=batter_role, vs_conditions=vs_conditions)
            elif query_type == 'team_comparison' and player1:
                return self._get_team_stats_response(player1)
            else:
                return f"I understood you're asking about: {parsed['interpretation']}\n\nPlease ask something like:\n- 'kohli vs bumrah in powerplay'\n- 'virat kohli statistics vs pace in 2025'\n- 'rohit's chasing performance in death overs'"
        
        except Exception as e:
            return f"Error processing query: {str(e)}\n\nPlease try again with a clearer query."
    
    def _get_head_to_head_response(self, player1: str, player2: str, venue: Optional[str] = None, 
                                    seasons: List[int] = None, match_phase: Optional[str] = None,
                                    match_situation: Optional[str] = None, bowler_type: Optional[str] = None) -> str:
        """Get head-to-head comparison between two players with additional filters"""
        
        try:
            # Find actual player names using fuzzy matching
            found_player1 = self.stats_engine.find_player(player1)
            found_player2 = self.stats_engine.find_player(player2)
            
            if not found_player1 or not found_player2:
                return f"Could not find players. Searching for: {player1}, {player2}"
            
            # Build filters dict with all available filters
            filters = {}
            if seasons:
                filters['seasons'] = seasons
            if match_phase:
                filters['match_phase'] = match_phase
            if match_situation:
                filters['match_situation'] = match_situation
            if bowler_type:
                filters['bowler_type'] = bowler_type
            
            # Get H2H stats from stats engine
            h2h_data = self.stats_engine.get_player_head_to_head(found_player1, found_player2, 
                                                                  filters if filters else None)
            
            if h2h_data.get('error'):
                return f"Could not find head-to-head data between {found_player1} and {found_player2}. They may not have faced each other."
            
            # Format response
            response = f"**Head-to-Head: {found_player1} vs {found_player2}**"
            if seasons:
                response += f" **({', '.join(str(s) for s in seasons)})**"
            if match_phase:
                response += f" - **{match_phase.replace('_', ' ').title()}**"
            if match_situation:
                response += f" - **{match_situation.replace('_', ' ').title()}**"
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
    
    def _get_player_stats_response(self, player: str, seasons: List[int] = None, 
                                    match_phase: Optional[str] = None, match_situation: Optional[str] = None,
                                    bowler_type: Optional[str] = None,
                                    batter_role: Optional[str] = None, vs_conditions: Optional[str] = None) -> str:
        """Get player statistics with advanced filters like match phase, match situation, bowler type, etc."""
        
        try:
            # Find player with fuzzy matching
            found_player = self.stats_engine.find_player(player)
            if not found_player:
                return f"Player '{player}' not found in IPL dataset. Try searching for similar names."
            
            # Build filters
            filters = {}
            if seasons:
                filters['seasons'] = seasons
            if match_phase:
                filters['match_phase'] = match_phase
            if match_situation:
                filters['match_situation'] = match_situation
            if bowler_type:
                filters['bowler_type'] = bowler_type
            if batter_role:
                filters['batter_role'] = batter_role
            if vs_conditions:
                filters['vs_conditions'] = vs_conditions
            
            # Get stats with optional filters
            stats = self.stats_engine.get_player_stats(found_player, filters if filters else None)
            
            if not stats or 'error' in stats:
                season_text = f" in {seasons}" if seasons else ""
                filter_text = f" {match_phase}" if match_phase else ""
                return f"Player '{found_player}' has no data{season_text}{filter_text} in IPL dataset."
            
            response = f"**Player Profile: {found_player}**"
            if seasons:
                response += f" **({', '.join(str(s) for s in seasons)})**"
            if match_phase:
                response += f" - **{match_phase.replace('_', ' ').title()}**"
            if match_situation:
                response += f" - **{match_situation.replace('_', ' ').title()}**"
            if vs_conditions:
                response += f" - **{vs_conditions.replace('_', ' ').title()}**"
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

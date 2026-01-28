"""
OpenAI LLM integration for natural language cricket analytics queries
"""

import json
import os
import pandas as pd
from typing import Dict, List, Tuple, Optional
from openai import OpenAI
from pathlib import Path
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

        # Model selection (with environment variable override)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        # Set OpenAI API key - strip whitespace and ensure it's valid
        if api_key:
            api_key_to_use = api_key.strip()
        elif os.getenv('OPENAI_API_KEY'):
            api_key_to_use = os.getenv('OPENAI_API_KEY').strip()
        else:
            raise ValueError("OpenAI API key not provided. Set OPENAI_API_KEY environment variable.")
        
        if not api_key_to_use or not api_key_to_use.startswith('sk-'):
            raise ValueError(f"Invalid API key format. Expected sk-... format, got: {api_key_to_use[:20] if api_key_to_use else 'empty'}")
        
        self.client = OpenAI(api_key=api_key_to_use)
        
        # Get all unique players and venues for context
        self.all_players = self._get_all_players()
        self.all_venues = self._get_all_venues()
        self.all_teams = self._get_all_teams()
        
        # Load player aliases for smart matching
        self.player_aliases = self._build_player_aliases()
        self.team_aliases = self._build_team_aliases()
        
        # Valid filter values
        self.VALID_MATCH_PHASES = ['powerplay', 'middle_overs', 'death_overs', 'opening', 'closing']
        self.VALID_MATCH_SITUATIONS = ['chasing', 'defending', 'pressure_chase', 'winning_position', 'batting_first']
        self.VALID_BOWLER_TYPES = ['fast_bowler', 'spin_bowler', 'left_arm', 'right_arm', 'pacer', 'spinner', 'pace']
        self.VALID_BATTER_ROLES = ['opener', 'middle_order', 'lower_order', 'finisher']
        self.VALID_VS_CONDITIONS = ['vs_pace', 'vs_spin', 'vs_left_arm', 'vs_right_arm']
    
    def _validate_filter(self, filter_name: str, filter_value: Optional[str]) -> bool:
        """Validate that filter values are recognized"""
        if not filter_value:
            return True
        
        filter_value_lower = filter_value.lower().replace(' ', '_')
        
        if filter_name == 'match_phase':
            return filter_value_lower in self.VALID_MATCH_PHASES
        elif filter_name == 'match_situation':
            return filter_value_lower in self.VALID_MATCH_SITUATIONS
        elif filter_name == 'bowler_type':
            return filter_value_lower in self.VALID_BOWLER_TYPES
        elif filter_name == 'batter_role':
            return filter_value_lower in self.VALID_BATTER_ROLES
        elif filter_name == 'vs_conditions':
            return filter_value_lower in self.VALID_VS_CONDITIONS
        
        return True  # Other filters are always valid
    
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
    
    def _build_player_aliases(self) -> Dict[str, str]:
        """Load player name aliases from player_aliases.json"""
        try:
            aliases_file = Path(__file__).resolve().parent / "player_aliases.json"
            if aliases_file.exists():
                with open(aliases_file, 'r') as f:
                    data = json.load(f)
                    
                # Build reverse mapping: alias -> canonical name
                alias_map = {}
                for canonical_name, alias_list in data.get("aliases", {}).items():
                    for alias in alias_list:
                        alias_map[alias.lower()] = canonical_name
                
                return alias_map
        except Exception as e:
            print(f"Warning: Could not load player aliases: {e}")
        
        return {}
    
    def _build_team_aliases(self) -> Dict[str, str]:
        """Load team aliases from player_aliases.json"""
        try:
            aliases_file = Path(__file__).resolve().parent / "player_aliases.json"
            if aliases_file.exists():
                with open(aliases_file, 'r') as f:
                    data = json.load(f)
                    
                # Build reverse mapping: alias -> canonical name
                alias_map = {}
                for canonical_name, alias_list in data.get("teams", {}).items():
                    for alias in alias_list:
                        alias_map[alias.lower()] = canonical_name
                
                return alias_map
        except Exception as e:
            print(f"Warning: Could not load team aliases: {e}")
        
        return {}
    
    def _resolve_player_name(self, query_text: str) -> Optional[str]:
        """Intelligently resolve player name from query using aliases and fuzzy matching"""
        query_lower = query_text.lower()
        
        # Check for exact aliases first
        for alias, full_name in self.player_aliases.items():
            if alias in query_lower:
                return full_name
        
        # Check for partial matches in all players
        for player in self.all_players:
            if player and not pd.isna(player):
                player_lower = player.lower()
                if player_lower in query_lower or query_lower in player_lower:
                    return player
        
        return None
    
    def _resolve_team_name(self, query_text: str) -> Optional[str]:
        """Intelligently resolve team name from query using aliases"""
        query_lower = query_text.lower()
        
        # Check for exact aliases first
        for alias, full_name in self.team_aliases.items():
            if alias in query_lower:
                return full_name
        
        # Check for partial matches
        for team in self.all_teams:
            if team and not pd.isna(team):
                team_lower = team.lower()
                if team_lower in query_lower:
                    return team
        
        return None
    
    def _extract_filter_keywords(self, query: str) -> Dict:
        """Extract filter keywords from query text using pattern matching"""
        query_lower = query.lower()
        filters = {}
        
        # Match phase keywords
        if any(word in query_lower for word in ['powerplay', 'power play', '0-6']):
            filters['match_phase'] = 'powerplay'
        elif any(word in query_lower for word in ['middle overs', 'middle']):
            filters['match_phase'] = 'middle_overs'
        elif any(word in query_lower for word in ['death', 'death overs', 'final overs']):
            filters['match_phase'] = 'death_overs'
        elif any(word in query_lower for word in ['opening', 'start']):
            filters['match_phase'] = 'opening'
        elif any(word in query_lower for word in ['closing', 'end']):
            filters['match_phase'] = 'closing'
        
        # Match situation keywords
        if any(word in query_lower for word in ['chasing', 'chase']):
            filters['match_situation'] = 'chasing'
        elif any(word in query_lower for word in ['defending', 'defend']):
            filters['match_situation'] = 'defending'
        elif any(word in query_lower for word in ['pressure chase', 'tight chase']):
            filters['match_situation'] = 'pressure_chase'
        elif any(word in query_lower for word in ['winning', 'winning position']):
            filters['match_situation'] = 'winning_position'
        elif any(word in query_lower for word in ['batting first', 'batting 1st']):
            filters['match_situation'] = 'batting_first'
        
        # Bowler type keywords
        if any(word in query_lower for word in ['pacer', 'pace', 'fast bowler', 'fast']):
            filters['bowler_type'] = 'pace'
        elif any(word in query_lower for word in ['spinner', 'spin', 'spin bowler']):
            filters['bowler_type'] = 'spin'
        elif any(word in query_lower for word in ['left arm', 'left-arm']):
            filters['bowler_type'] = 'left_arm'
        elif any(word in query_lower for word in ['right arm', 'right-arm']):
            filters['bowler_type'] = 'right_arm'
        
        # Batter role keywords
        if any(word in query_lower for word in ['opener', 'opening']):
            filters['batter_role'] = 'opener'
        elif any(word in query_lower for word in ['middle order', 'middle']):
            filters['batter_role'] = 'middle_order'
        elif any(word in query_lower for word in ['lower order', 'lower']):
            filters['batter_role'] = 'lower_order'
        elif any(word in query_lower for word in ['finisher', 'finishing']):
            filters['batter_role'] = 'finisher'
        
        # VS conditions keywords
        if any(word in query_lower for word in ['vs off spin', 'against off spin', 'vs off-spin', 'vs offspinner']):
            filters['vs_conditions'] = 'vs_off_spin'
        elif any(word in query_lower for word in ['vs leg spin', 'against leg spin', 'vs leg-spin', 'vs legspinner']):
            filters['vs_conditions'] = 'vs_leg_spin'
        elif any(word in query_lower for word in ['vs pace', 'against pace', 'vs fast']):
            filters['vs_conditions'] = 'vs_pace'
        elif any(word in query_lower for word in ['vs spin', 'against spin']):
            filters['vs_conditions'] = 'vs_spin'
        elif any(word in query_lower for word in ['vs left arm', 'against left arm', 'vs left-arm']):
            filters['vs_conditions'] = 'vs_left_arm'
        elif any(word in query_lower for word in ['vs right arm', 'against right arm', 'vs right-arm']):
            filters['vs_conditions'] = 'vs_right_arm'
        
        return filters
    
    def parse_query(self, query: str) -> Dict:
        """
        Parse natural language query using GPT to intelligently extract cricket-specific information.
        Leverages loaded player/team aliases for smart entity resolution.
        """
        
        # Build context about available aliases for the prompt
        player_alias_samples = {k: v for k, v in list(self.player_aliases.items())[:8]}
        team_alias_samples = {k: v for k, v in list(self.team_aliases.items())[:6]}
        
        prompt = f"""You are an expert cricket analytics assistant. Parse this cricket query intelligently.

USE THESE PLAYER ALIASES TO RESOLVE NAMES:
{json.dumps(player_alias_samples, indent=2)}
... and {len(self.player_aliases)-8} more aliases loaded from player_aliases.json

USE THESE TEAM ALIASES:
{json.dumps(team_alias_samples, indent=2)}
... and {len(self.team_aliases)-6} more team aliases

CRICKET FILTER OPTIONS:
- match_phase: 'powerplay' (0-6 overs), 'middle_overs' (6-16 overs), 'death_overs' (16+ overs), 'opening', 'closing'
- match_situation: 'batting_first', 'chasing', 'defending', 'pressure_chase', 'winning_position'
- bowler_type: 'pace', 'spin', 'left_arm', 'right_arm'
- batter_role: 'opener', 'middle_order', 'lower_order', 'finisher'
- vs_conditions: 'vs_pace', 'vs_spin', 'vs_left_arm', 'vs_right_arm'

USER QUERY: "{query}"

Return ONLY valid JSON (NO other text):
{{
    "player1": "Full player name (use aliases if needed) or null",
    "player2": "Second player (for comparisons) or null",
    "venue": "Venue name or null",
    "seasons": [List of years mentioned or null],
    "bowler_type": "Bowler type or null",
    "match_phase": "Match phase or null",
    "match_situation": "Match situation or null",
    "opposition_team": "Full team name or null",
    "batter_role": "Batter role or null",
    "vs_conditions": "Condition or null",
    "form_filter": "Form or null",
    "query_type": "head_to_head|player_stats|team_comparison|general",
    "interpretation": "What the user is asking"
}}

EXAMPLES:
- "virat vs bumrah" → player1: "V Kohli", player2: "JJ Bumrah", query_type: "head_to_head"
- "rohit in powerplay" → player1: "RG Sharma", match_phase: "powerplay", query_type: "player_stats"
- "kohli in death overs" → player1: "V Kohli", match_phase: "death_overs", query_type: "player_stats"
- "kohli vs bumrah in powerplay" → player1: "V Kohli", player2: "JJ Bumrah", match_phase: "powerplay", query_type: "head_to_head"
- "kohli chasing" → player1: "V Kohli", match_situation: "chasing", query_type: "player_stats"
- "bumrah vs pace against csk" → player1: "JJ Bumrah", vs_conditions: "vs_pace", opposition_team: "Chennai Super Kings"
- "sky vs spin 2024" → player1: "SA Yadav", vs_conditions: "vs_spin", seasons: [2024]"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=500
            )
            
            response_text = response.choices[0].message.content.strip()
            parsed = json.loads(response_text)
            
            # Normalize and validate player/team names
            if parsed.get('player1'):
                canonical = self._get_canonical_player_name(str(parsed['player1']))
                if canonical:
                    parsed['player1'] = canonical
            
            if parsed.get('player2'):
                canonical = self._get_canonical_player_name(str(parsed['player2']))
                if canonical:
                    parsed['player2'] = canonical
            
            if parsed.get('opposition_team'):
                canonical = self._get_canonical_team_name(str(parsed['opposition_team']))
                if canonical:
                    parsed['opposition_team'] = canonical
            
            # Normalize filter values to snake_case lowercase
            if parsed.get('match_phase'):
                parsed['match_phase'] = str(parsed['match_phase']).lower().replace(' ', '_').replace('-', '_')
            if parsed.get('match_situation'):
                parsed['match_situation'] = str(parsed['match_situation']).lower().replace(' ', '_').replace('-', '_')
            if parsed.get('bowler_type'):
                parsed['bowler_type'] = str(parsed['bowler_type']).lower().replace(' ', '_').replace('-', '_')
            if parsed.get('batter_role'):
                parsed['batter_role'] = str(parsed['batter_role']).lower().replace(' ', '_').replace('-', '_')
            if parsed.get('vs_conditions'):
                parsed['vs_conditions'] = str(parsed['vs_conditions']).lower().replace(' ', '_').replace('-', '_')
            
            return parsed
            
        except (json.JSONDecodeError, Exception) as e:
            # Fallback: Extract keywords AND entities
            player1 = self._resolve_player_name(query)
            player2 = None
            team = self._resolve_team_name(query)
            
            # Try to extract second player from "vs" comparison
            if ' vs ' in query.lower() or ' against ' in query.lower():
                separator = ' vs ' if ' vs ' in query.lower() else ' against '
                parts = query.lower().split(separator)
                if len(parts) >= 2:
                    player2 = self._resolve_player_name(parts[1])
            
            # Extract filter keywords using pattern matching
            extracted_filters = self._extract_filter_keywords(query)
            
            # Determine query type
            determined_type = 'general'
            if player1 and player2:
                determined_type = 'head_to_head'
            elif player1:
                determined_type = 'player_stats'
            elif team:
                determined_type = 'team_comparison'
            
            return {
                "player1": player1,
                "player2": player2,
                "venue": None,
                "seasons": None,
                "bowler_type": extracted_filters.get('bowler_type'),
                "match_phase": extracted_filters.get('match_phase'),
                "match_situation": extracted_filters.get('match_situation'),
                "opposition_team": team,
                "batter_role": extracted_filters.get('batter_role'),
                "vs_conditions": extracted_filters.get('vs_conditions'),
                "form_filter": None,
                "query_type": determined_type,
                "interpretation": f"Comparing {player1} vs {player2}" if (player1 and player2) else (f"Stats for {player1}" if player1 else "Cricket query")
            }
    
    def _get_canonical_player_name(self, player_input: str) -> Optional[str]:
        """Get canonical player name using loaded aliases"""
        if not player_input:
            return None
        
        player_lower = player_input.lower().strip()
        
        # Direct match in aliases
        if player_lower in self.player_aliases:
            return self.player_aliases[player_lower]
        
        # Check if it's already a canonical name in dataset
        for player in self.all_players:
            if player and player.lower() == player_lower:
                return player
        
        # Fuzzy match: partial word match
        for player in self.all_players:
            if player and (player.lower() in player_lower or player_lower in player.lower()):
                return player
        
        return None
    
    def _get_canonical_team_name(self, team_input: str) -> Optional[str]:
        """Get canonical team name using loaded aliases"""
        if not team_input:
            return None
        
        team_lower = team_input.lower().strip()
        
        # Direct alias match
        if team_lower in self.team_aliases:
            return self.team_aliases[team_lower]
        
        # Already canonical
        for team in self.all_teams:
            if team and team.lower() == team_lower:
                return team
        
        # Fuzzy match
        for team in self.all_teams:
            if team and (team.lower() in team_lower or team_lower in team.lower()):
                return team
        
        return None
    
    def get_response(self, query: str) -> str:
        """
        Main method: Takes user query and returns analytics response
        Validates that query contains cricket-relevant parameters before processing.
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
        
        # Canonicalize opposition_team using team aliases
        if opposition_team:
            opposition_team = self._get_canonical_team_name(opposition_team)
        query_type = parsed.get('query_type')
        
        # Validation: Ensure query has cricket-relevant entity (player, team, or venue)
        # Allow queries that mention at least one cricket entity, even without specific filters
        has_cricket_entity = player1 or player2 or venue or opposition_team
        
        if not has_cricket_entity:
            return f"🏏 I understood you're asking about: {parsed['interpretation']}\n\n**Please ask something specific about IPL cricket:**\n- 'kohli vs bumrah in powerplay'\n- 'virat kohli statistics vs pace in 2025'\n- 'rohit's chasing performance in death overs'\n- 'bumrah in pressure situations'\n- 'kohli against left-arm fast bowlers'"
        
        try:
            # Determine query type if not set correctly
            if not query_type or query_type == 'general':
                if player1 and player2:
                    query_type = 'head_to_head'
                elif player1:
                    query_type = 'player_stats'
                elif opposition_team:
                    query_type = 'team_comparison'
            
            # Route to appropriate handler
            if query_type == 'head_to_head' and player1 and player2:
                return self._get_head_to_head_response(player1, player2, venue, seasons, 
                                                        match_phase=match_phase, match_situation=match_situation,
                                                        bowler_type=bowler_type, opposition_team=opposition_team,
                                                        vs_conditions=vs_conditions)
            elif query_type == 'player_stats' and player1:
                return self._get_player_stats_response(player1, seasons, 
                                                       match_phase=match_phase, match_situation=match_situation,
                                                       bowler_type=bowler_type, opposition_team=opposition_team,
                                                       batter_role=batter_role, vs_conditions=vs_conditions)
            elif query_type == 'team_comparison' and opposition_team:
                return self._get_team_stats_response(opposition_team)
            elif player1:
                # Default to player stats if we have a player
                return self._get_player_stats_response(player1, seasons, 
                                                       match_phase=match_phase, match_situation=match_situation,
                                                       bowler_type=bowler_type, opposition_team=opposition_team,
                                                       batter_role=batter_role, vs_conditions=vs_conditions)
            else:
                return f"I understood you're asking about: {parsed['interpretation']}\n\nPlease ask something like:\n- 'kohli vs bumrah in powerplay'\n- 'virat kohli statistics vs pace in 2025'\n- 'rohit's chasing performance in death overs'"
        
        except Exception as e:
            return f"Error processing query: {str(e)}\n\nPlease try again with a clearer query."
    
    def _get_head_to_head_response(self, player1: str, player2: str, venue: Optional[str] = None, 
                                    seasons: List[int] = None, match_phase: Optional[str] = None,
                                    match_situation: Optional[str] = None, bowler_type: Optional[str] = None,
                                    opposition_team: Optional[str] = None, vs_conditions: Optional[str] = None) -> str:
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
            if opposition_team:
                filters['opposition_team'] = opposition_team
            if vs_conditions:
                filters['vs_conditions'] = vs_conditions
            
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
                                    bowler_type: Optional[str] = None, opposition_team: Optional[str] = None,
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
            if opposition_team:
                filters['opposition_team'] = opposition_team
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
            if opposition_team:
                response += f" - **vs {opposition_team}**"
            if vs_conditions:
                response += f" - **{vs_conditions.replace('_', ' ').title()}**"
            response += "\n\n"
            
            if 'batting' in stats and stats['batting']:
                bat = stats['batting']
                
                # Use table format for vs_conditions filters
                if vs_conditions:
                    response += f"🏏 **Batting Stats - {vs_conditions.replace('_', ' ').title()}**\n\n"
                    response += "| Metric | Value |\n|--------|-------|\n"
                    response += f"| Matches | {bat.get('matches', 0)} |\n"
                    response += f"| Runs | {bat.get('runs', 0)} |\n"
                    response += f"| Average | {bat.get('average', 0):.2f} |\n"
                    response += f"| Strike Rate | {bat.get('strike_rate', 0):.2f} |\n"
                    response += f"| Hundreds | {bat.get('centuries', 0)} |\n"
                    response += f"| Fifties | {bat.get('fifties', 0)} |\n"
                    response += f"| Fours | {bat.get('fours', 0)} |\n"
                    response += f"| Sixes | {bat.get('sixes', 0)} |\n\n"
                else:
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

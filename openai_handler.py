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
                # The first element in the alias_list is the full team name
                alias_map = {}
                for key, alias_list in data.get("teams", {}).items():
                    # First item in alias_list should be the full team name
                    if alias_list and len(alias_list) > 0:
                        full_name = alias_list[0]  # e.g., "Mumbai Indians"
                        # Map all aliases to the full team name
                        for alias in alias_list:
                            alias_map[alias.lower()] = full_name
                    else:
                        # Fallback: use the key as the full name
                        alias_map[key.lower()] = key
                
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
        """
        Extract ALL filter keywords from query text using comprehensive pattern matching.
        Supports: match_phase, match_situation, bowler_type, batter_role, vs_conditions,
                  ground, handedness, year/season, inning, and home/away filters.
        """
        query_lower = query.lower()
        filters = {}
        
        # ===== MATCH PHASE FILTERS =====
        if any(word in query_lower for word in ['powerplay', 'power play', '0-6', 'first 6']):
            filters['match_phase'] = 'powerplay'
        elif any(word in query_lower for word in ['middle overs', 'middle overs', 'middle phase']):
            filters['match_phase'] = 'middle_overs'
        elif any(word in query_lower for word in ['death', 'death overs', 'final overs', 'last overs']):
            filters['match_phase'] = 'death_overs'
        elif any(word in query_lower for word in ['opening', 'first 3 overs', 'start']):
            filters['match_phase'] = 'opening'
        elif any(word in query_lower for word in ['closing', 'last 3 overs', 'final phase']):
            filters['match_phase'] = 'closing'
        
        # ===== MATCH SITUATION FILTERS =====
        if any(word in query_lower for word in ['chasing', 'chase', 'while chasing']):
            filters['match_situation'] = 'chasing'
        elif any(word in query_lower for word in ['defending', 'defend', 'defended']):
            filters['match_situation'] = 'defending'
        elif any(word in query_lower for word in ['pressure chase', 'tight chase']):
            filters['match_situation'] = 'pressure_chase'
        elif any(word in query_lower for word in ['winning', 'winning position']):
            filters['match_situation'] = 'winning_position'
        elif any(word in query_lower for word in ['batting first', 'batting 1st', 'bat first']):
            filters['match_situation'] = 'batting_first'
        
        # ===== BOWLING TYPE FILTERS =====
        if any(word in query_lower for word in ['pacer', 'pace', 'fast bowler', 'fast', 'pace bowler', 'pacers']):
            filters['bowler_type'] = 'pace'
        elif any(word in query_lower for word in ['spinner', 'spin', 'spin bowler', 'spinners']):
            filters['bowler_type'] = 'spin'
        elif any(word in query_lower for word in ['left arm', 'left-arm', 'left arm fast', 'left arm bowler']):
            filters['bowler_type'] = 'left_arm'
        elif any(word in query_lower for word in ['right arm', 'right-arm', 'right arm fast', 'right arm bowler']):
            filters['bowler_type'] = 'right_arm'
        
        # ===== BATTER ROLE FILTERS =====
        if any(word in query_lower for word in ['opener', 'opening batter', 'open the batting']):
            filters['batter_role'] = 'opener'
        elif any(word in query_lower for word in ['middle order', 'middle-order', 'middle batsman']):
            filters['batter_role'] = 'middle_order'
        elif any(word in query_lower for word in ['lower order', 'lower-order', 'tail-ender']):
            filters['batter_role'] = 'lower_order'
        elif any(word in query_lower for word in ['finisher', 'finishing', 'death batter']):
            filters['batter_role'] = 'finisher'
        
        # ===== HANDEDNESS FILTERS =====
        if any(word in query_lower for word in ['left-hand', 'left handed', 'left hander', 'lhb', 'vs left hand']):
            filters['handedness'] = 'left_handed'
        elif any(word in query_lower for word in ['right-hand', 'right handed', 'right hander', 'rhb', 'vs right hand']):
            filters['handedness'] = 'right_handed'
        
        # ===== INNING FILTERS =====
        if any(word in query_lower for word in ['inning 1', 'first inning', 'first innings', 'inning one']):
            filters['inning'] = 1
        elif any(word in query_lower for word in ['inning 2', 'second inning', 'second innings', 'inning two']):
            filters['inning'] = 2
        
        # ===== YEAR/SEASON FILTERS =====
        # Extract 4-digit years (2008-2025 for IPL)
        import re
        years = re.findall(r'\b(20\d{2})\b', query)
        if years:
            filters['seasons'] = [int(y) for y in years if 2008 <= int(y) <= 2025]
        
        # ===== GROUND/VENUE FILTERS =====
        # Check for ground names - first try exact matches with known venues
        venues_to_check = [
            ('wankhede', 'Wankhede Stadium'),
            ('chinnaswamy', 'M Chinnaswamy Stadium'),
            ('arun jaitley', 'Arun Jaitley Stadium'),
            ('feroz shah kotla', 'Arun Jaitley Stadium'),
            ('eden gardens', 'Eden Gardens'),
            ('chidambaram', 'MA Chidambaram Stadium'),
            ('rajiv gandhi', 'Rajiv Gandhi International Stadium'),
            ('narendra modi', 'Narendra Modi Stadium'),
            ('sardar patel', 'Narendra Modi Stadium'),
            ('motera', 'Narendra Modi Stadium'),
            ('sawai mansingh', 'Sawai Mansingh Stadium'),
            ('dy patil', 'Dr DY Patil Sports Academy'),
            ('bindra', 'Punjab Cricket Association IS Bindra Stadium'),
            ('mohali', 'Punjab Cricket Association IS Bindra Stadium'),
            ('reddy', 'Dr. Y.S. Rajasekhara Reddy ACA-VDCA Cricket Stadium'),
            ('visakhapatnam', 'Dr. Y.S. Rajasekhara Reddy ACA-VDCA Cricket Stadium'),
            ('arun nagar', 'Arun Nagar Stadium'),
            ('maharashtra cricket', 'Maharashtra Cricket Association Stadium'),
            ('pune', 'Maharashtra Cricket Association Stadium'),
            ('bharat ratna', 'Bharat Ratna Rajiv Gandhi Intl'),
            ('chepauk', 'MA Chidambaram Stadium'),
            ('uppal', 'Rajiv Gandhi International Stadium'),
            ('hyderabad', 'Rajiv Gandhi International Stadium'),
            ('ahmedabad', 'Narendra Modi Stadium'),
            ('jaipur', 'Sawai Mansingh Stadium'),
            ('mumbai', 'Wankhede Stadium'),
            ('bangalore', 'M Chinnaswamy Stadium'),
            ('bengaluru', 'M Chinnaswamy Stadium'),
            ('delhi', 'Arun Jaitley Stadium'),
            ('kolkata', 'Eden Gardens'),
            ('chennai', 'MA Chidambaram Stadium'),
        ]
        
        for venue_keyword, canonical_venue in venues_to_check:
            if venue_keyword in query_lower:
                filters['ground'] = canonical_venue
                break
        
        # ===== HOME/AWAY FILTERS =====
        if any(word in query_lower for word in ['home', 'at home', 'home ground']):
            filters['match_type'] = 'home'
        elif any(word in query_lower for word in ['away', 'away game', 'away match']):
            filters['match_type'] = 'away'
        
        # ===== TIME PERIOD FILTERS =====
        # Extract "last N matches", "last N innings", "last season", "recent"
        import re
        if 'recent' in query_lower or 'current' in query_lower or 'now' in query_lower:
            filters['time_period'] = 'recent'
        elif 'last season' in query_lower:
            filters['time_period'] = 'last season'
        elif 'all time' in query_lower or 'career' in query_lower:
            filters['time_period'] = 'all time'
        else:
            # Look for "last N matches/innings" pattern - supports: matches, match, innings, inning, games
            match_pattern = re.search(r'last\s+(\d+)\s+(match(?:es)?|innings?|games?)', query_lower)
            if match_pattern:
                number = match_pattern.group(1)
                period_type = match_pattern.group(2)
                filters['time_period'] = f"last {number} {period_type}"
        
        # ===== VS CONDITIONS KEYWORDS - More specific patterns first =====
        # Spin + arm combinations (most specific)
        if any(word in query_lower for word in ['left arm spin', 'left-arm spin', 'vs left arm spinner']):
            filters['vs_conditions'] = 'vs_left_arm_spin'
        elif any(word in query_lower for word in ['right arm spin', 'right-arm spin', 'vs right arm spinner']):
            filters['vs_conditions'] = 'vs_right_arm_spin'
        elif any(word in query_lower for word in ['vs off spin', 'against off spin', 'vs offspinner']):
            filters['vs_conditions'] = 'vs_off_spin'
        elif any(word in query_lower for word in ['vs leg spin', 'against leg spin', 'vs legspinner']):
            filters['vs_conditions'] = 'vs_leg_spin'
        # General vs conditions
        elif any(word in query_lower for word in ['vs pace', 'against pace', 'vs fast']):
            filters['vs_conditions'] = 'vs_pace'
        elif any(word in query_lower for word in ['vs spin', 'against spin']):
            filters['vs_conditions'] = 'vs_spin'
        elif any(word in query_lower for word in ['vs left arm', 'against left arm']):
            filters['vs_conditions'] = 'vs_left_arm'
        elif any(word in query_lower for word in ['vs right arm', 'against right arm']):
            filters['vs_conditions'] = 'vs_right_arm'
        
        return filters
    
    def parse_query(self, query: str) -> Dict:
        """
        Parse natural language query using GPT to intelligently extract cricket-specific information.
        Leverages loaded player/team aliases for smart entity resolution.
        
        Optimization: Try simple pattern matching FIRST before calling GPT.
        """
        
        # OPTIMIZATION: Try simple pattern matching first for common queries
        # This avoids expensive GPT calls for queries like "player last N matches"
        query_lower = query.lower()
        
        # Check if this is a "player last N matches/innings" query
        import re
        time_period_match = re.search(r'last\s+(\d+)\s+(match(?:es)?|innings?|games?)', query_lower)
        if time_period_match:
            # This is likely a trends query
            player1 = self._resolve_player_name(query)
            if player1:
                # We found a player and time period - extract it without GPT
                number = time_period_match.group(1)
                period_type = time_period_match.group(2)
                return {
                    "player1": player1,
                    "player2": None,
                    "venue": None,
                    "seasons": None,
                    "bowler_type": None,
                    "match_phase": None,
                    "match_situation": None,
                    "opposition_team": None,
                    "batter_role": None,
                    "vs_conditions": None,
                    "ground": None,
                    "handedness": None,
                    "inning": None,
                    "match_type": None,
                    "time_period": f"last {number} {period_type}",
                    "record_type": None,
                    "comparison_type": None,
                    "ranking_metric": None,
                    "player_list": None,
                    "form_filter": None,
                    "query_type": "trends",
                    "interpretation": f"Trends for {player1} in last {number} {period_type}"
                }
        
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
- match_phase: 'powerplay' (0-6 overs), 'middle_overs' (6-16 overs), 'death_overs' (16+ overs), 'opening' (0-3 overs), 'closing' (17-20 overs)
- match_situation: 'batting_first', 'chasing', 'defending', 'pressure_chase', 'winning_position'
- bowler_type: 'pace', 'spin', 'left_arm', 'right_arm'
- batter_role: 'opener', 'middle_order', 'lower_order', 'finisher'
- vs_conditions: 'vs_pace', 'vs_spin', 'vs_left_arm', 'vs_right_arm', 'vs_off_spin', 'vs_leg_spin'
- ground: IPL stadium names (e.g., 'Wankhede Stadium', 'Eden Gardens', 'M Chinnaswamy Stadium')
- handedness: 'left_handed', 'right_handed'
- seasons: List of years [2008-2025]
- inning: 1 or 2 (1 = batting first, 2 = batting second/chasing)
- match_type: 'home', 'away'
- time_period: 'recent', 'last 5 matches', 'last 10 matches', 'last season', 'all time'
- record_type: 'highest_score', 'most_runs', 'fastest_century', 'best_figures', 'most_wickets', 'most_sixes'
- comparison_type: 'vs_league_avg', 'vs_cohort', 'peer_group', 'vs_all_rounders'
- trend_direction: 'improving', 'declining', 'stable'
- form_status: 'in_form', 'good_form', 'average', 'poor_form', 'out_of_form'
- ranking_metric: 'runs', 'strike_rate', 'economy', 'wickets', 'consistency'

USER QUERY: "{query}"

Return ONLY valid JSON (NO other text):
{{
    "player1": "Full player name (use aliases if needed) or null",
    "player2": "Second player (for comparisons) or null",
    "venue": "Venue/Ground name or null",
    "seasons": [List of years mentioned (2008-2025) or null],
    "bowler_type": "Bowler type or null",
    "match_phase": "Match phase or null",
    "match_situation": "Match situation or null",
    "opposition_team": "Full team name or null",
    "batter_role": "Batter role or null",
    "vs_conditions": "Condition or null",
    "ground": "Ground/Venue name or null",
    "handedness": "left_handed or right_handed or null",
    "inning": 1 or 2 or null,
    "match_type": "home or away or null",
    "form_filter": "Form or null",
    "time_period": "Time period filter or null",
    "record_type": "Type of record requested or null",
    "comparison_type": "Type of comparison or null",
    "ranking_metric": "Ranking metric or null",
    "player_list": [List of player names for group queries or null],
    "query_type": "player_stats|head_to_head|team_comparison|trends|records|rankings|ground_insights|form_guide|comparative_analysis|predictions|general",
    "interpretation": "What the user is asking"
}}

EXAMPLES:
- "virat in powerplay" → player1: "V Kohli", match_phase: "powerplay", query_type: "player_stats"
- "virat vs bumrah" → player1: "V Kohli", player2: "JJ Bumrah", query_type: "head_to_head"
- "kohli vs bumrah in chinnaswamy" → player1: "V Kohli", player2: "JJ Bumrah", ground: "M Chinnaswamy Stadium", query_type: "head_to_head"
- "kohli chasing in death overs 2024" → player1: "V Kohli", match_situation: "chasing", match_phase: "death_overs", seasons: [2024], query_type: "player_stats"
- "bumrah vs left hander" → player1: "JJ Bumrah", handedness: "left_handed", query_type: "player_stats"
- "sky in powerplay chasing" → player1: "SA Yadav", match_phase: "powerplay", match_situation: "chasing", query_type: "player_stats"
- "bumrah at home in 2024" → player1: "JJ Bumrah", match_type: "home", seasons: [2024], query_type: "player_stats"
- "sharma vs pace bowlers" → player1: "RG Sharma", vs_conditions: "vs_pace", query_type: "player_stats"
- "bumrah vs right hander" → player1: "JJ Bumrah", handedness: "right_handed", query_type: "player_stats"
- "kohli's recent form" → player1: "V Kohli", time_period: "recent", query_type: "form_guide"
- "kohli's highest score" → player1: "V Kohli", record_type: "highest_score", query_type: "records"
- "top 10 run scorers in 2024" → seasons: [2024], ranking_metric: "runs", query_type: "rankings"
- "kohli at wankhede" → player1: "V Kohli", ground: "Wankhede Stadium", query_type: "ground_insights"
- "bumrah's trend in last 5 matches" → player1: "JJ Bumrah", time_period: "last 5 matches", query_type: "trends"
- "kohli last 5 innings" → player1: "V Kohli", time_period: "last 5 innings", query_type: "trends"
- "bumrah last 10 matches" → player1: "JJ Bumrah", time_period: "last 10 matches", query_type: "trends"
- "kohli vs sharma in powerplay" → player1: "V Kohli", player2: "RG Sharma", match_phase: "powerplay", query_type: "comparative_analysis"
- "who should bat for CSK in powerplay" → opposition_team: "CSK", match_phase: "powerplay", query_type: "predictions"
"""
        
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
            
            # Determine query_type based on extracted filters
            if extracted_filters.get('time_period') and player1:
                determined_type = 'trends'
            
            return {
                "player1": player1,
                "player2": player2,
                "venue": None,
                "seasons": extracted_filters.get('seasons'),
                "bowler_type": extracted_filters.get('bowler_type'),
                "match_phase": extracted_filters.get('match_phase'),
                "match_situation": extracted_filters.get('match_situation'),
                "opposition_team": team,
                "batter_role": extracted_filters.get('batter_role'),
                "vs_conditions": extracted_filters.get('vs_conditions'),
                "ground": extracted_filters.get('ground'),
                "handedness": extracted_filters.get('handedness'),
                "inning": extracted_filters.get('inning'),
                "match_type": extracted_filters.get('match_type'),
                "time_period": extracted_filters.get('time_period'),
                "record_type": None,
                "comparison_type": None,
                "ranking_metric": None,
                "player_list": None,
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
        Supports 10 query types: player_stats, head_to_head, team_comparison, trends, 
        records, rankings, ground_insights, form_guide, comparative_analysis, predictions
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
        ground = parsed.get('ground')
        handedness = parsed.get('handedness')
        inning = parsed.get('inning')
        match_type = parsed.get('match_type')
        form_filter = parsed.get('form_filter')
        
        # New filters for enhanced query types
        time_period = parsed.get('time_period')
        record_type = parsed.get('record_type')
        comparison_type = parsed.get('comparison_type')
        ranking_metric = parsed.get('ranking_metric')
        player_list = parsed.get('player_list')
        
        # Canonicalize opposition_team using team aliases
        if opposition_team:
            opposition_team = self._get_canonical_team_name(opposition_team)
        query_type = parsed.get('query_type')
        
        # Validation: Ensure query has cricket-relevant entity
        has_cricket_entity = player1 or player2 or venue or opposition_team or ranking_metric
        
        if not has_cricket_entity:
            return f"🏏 I understood you're asking about: {parsed['interpretation']}\n\n**Please ask something specific about IPL cricket:**\n- 'kohli vs bumrah in powerplay'\n- 'kohli's recent form'\n- 'top 10 run scorers'\n- 'bumrah at wankhede'\n- 'who should bat for CSK'"
        
        try:
            # Determine query type if not set correctly or set to 'general'
            # IMPORTANT: Check time_period FIRST - it's highly specific
            if not query_type or query_type == 'general':
                if time_period and player1:
                    query_type = 'trends'
                elif player1 and player2:
                    query_type = 'head_to_head'
                elif ranking_metric or (seasons and not player1):
                    query_type = 'rankings'
                elif record_type:
                    query_type = 'records'
                elif ground and player1:
                    query_type = 'ground_insights'
                elif player1:
                    query_type = 'player_stats'
                elif opposition_team:
                    query_type = 'team_comparison'
            
            # Route to appropriate handler based on query type
            if query_type == 'head_to_head' and player1 and player2:
                return self._get_head_to_head_response(player1, player2, venue, seasons, 
                                                        match_phase=match_phase, match_situation=match_situation,
                                                        bowler_type=bowler_type, opposition_team=opposition_team,
                                                        vs_conditions=vs_conditions, ground=ground,
                                                        handedness=handedness, inning=inning, match_type=match_type)
            
            elif query_type == 'player_stats' and player1:
                return self._get_player_stats_response(player1, seasons, 
                                                       match_phase=match_phase, match_situation=match_situation,
                                                       bowler_type=bowler_type, opposition_team=opposition_team,
                                                       batter_role=batter_role, vs_conditions=vs_conditions,
                                                       ground=ground, handedness=handedness, inning=inning, 
                                                       match_type=match_type)
            
            elif query_type == 'trends' and player1:
                return self._get_trends_response(player1, time_period=time_period, 
                                                 match_phase=match_phase, match_situation=match_situation,
                                                 seasons=seasons)
            
            elif query_type == 'records':
                return self._get_records_response(player=player1, record_type=record_type, 
                                                  seasons=seasons, match_phase=match_phase)
            
            elif query_type == 'rankings':
                return self._get_rankings_response(metric=ranking_metric, seasons=seasons,
                                                   match_phase=match_phase, ground=ground, limit=10)
            
            elif query_type == 'ground_insights' and player1 and ground:
                return self._get_ground_insights_response(player1, ground)
            
            elif query_type == 'form_guide':
                return self._get_form_guide_response(player=player1, time_period=time_period)
            
            elif query_type == 'comparative_analysis' and (player1 or player_list):
                return self._get_comparative_analysis_response(player1=player1, player2=player2,
                                                               player_list=player_list, 
                                                               comparison_type=comparison_type,
                                                               match_phase=match_phase)
            
            elif query_type == 'predictions':
                return self._get_predictions_response(opposition_team=opposition_team, 
                                                      match_phase=match_phase)
            
            elif query_type == 'team_comparison' and opposition_team:
                return self._get_team_stats_response(opposition_team)
            
            elif player1:
                # Default to player stats if we have a player
                return self._get_player_stats_response(player1, seasons, 
                                                       match_phase=match_phase, match_situation=match_situation,
                                                       bowler_type=bowler_type, opposition_team=opposition_team,
                                                       batter_role=batter_role, vs_conditions=vs_conditions)
            else:
                return f"I understood you're asking about: {parsed['interpretation']}\n\nPlease ask something like:\n- 'kohli statistics'\n- 'kohli vs bumrah in powerplay'\n- 'kohli's recent form'\n- 'top 10 run scorers in 2024'\n- 'kohli at wankhede'"
        
        except Exception as e:
            return f"Error processing query: {str(e)}\n\nPlease try again with a clearer query."
    
    def _get_head_to_head_response(self, player1: str, player2: str, venue: Optional[str] = None, 
                                    seasons: List[int] = None, match_phase: Optional[str] = None,
                                    match_situation: Optional[str] = None, bowler_type: Optional[str] = None,
                                    opposition_team: Optional[str] = None, vs_conditions: Optional[str] = None,
                                    ground: Optional[str] = None, handedness: Optional[str] = None,
                                    inning: Optional[int] = None, match_type: Optional[str] = None) -> str:
        """Get head-to-head comparison between two players with comprehensive filters"""
        
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
            if ground:
                filters['ground'] = ground
            if handedness:
                filters['handedness'] = handedness
            if inning:
                filters['innings_order'] = inning  # stats_engine uses 'innings_order'
            if match_type:
                filters['match_type'] = match_type
            
            # Get H2H stats from stats engine
            h2h_data = self.stats_engine.get_player_head_to_head(found_player1, found_player2, 
                                                                  filters if filters else None)
            
            if h2h_data.get('error'):
                return f"Could not find head-to-head data between {found_player1} and {found_player2}. They may not have faced each other."
            
            # Generate intelligent insights
            insights = []
            
            # Deliveries and runs analysis
            deliveries = h2h_data['deliveries']
            runs = h2h_data['runs']
            strike_rate = h2h_data['strike_rate']
            dot_balls = h2h_data.get('dot_balls', 0)
            
            if deliveries > 0:
                # Strike rate insights
                if strike_rate > 150:
                    insights.append(f"🔥 **Aggressive Approach**: {found_player1} has been very aggressive vs {found_player2} with SR of {strike_rate:.1f}")
                elif strike_rate < 100:
                    insights.append(f"🛡️ **Cautious**: {found_player1} plays cautiously vs {found_player2} (SR: {strike_rate:.1f})")
                
                # Dot ball analysis
                dot_percentage = (dot_balls / deliveries) * 100 if deliveries > 0 else 0
                if dot_percentage > 40:
                    insights.append(f"📊 **High Dot Ball Rate**: {dot_percentage:.1f}% dot balls faced - facing difficulty")
                elif dot_percentage < 20:
                    insights.append(f"⚡ **Scoring Intent**: Only {dot_percentage:.1f}% dot balls - {found_player1} is finding the gaps")
                
                # Wicket/Dismissal insights (from runs data - proxy for control)
                if runs == 0 and deliveries > 3:
                    insights.append(f"😱 **Dominant Bowler**: {found_player2} has been exceptional - 0 runs in {deliveries} deliveries!")
                elif runs < deliveries:
                    insights.append(f"💪 **Bowler's Strength**: {found_player2} restricts {found_player1} effectively")
            
            # Format main response
            response = f"**Head-to-Head: {found_player1} vs {found_player2}**\n\n"
            
            # Filter context
            filters_context = []
            if seasons:
                filters_context.append(f"📅 {', '.join(str(s) for s in seasons)}")
            if match_phase:
                filters_context.append(f"🎯 {match_phase.replace('_', ' ').title()}")
            if match_situation:
                filters_context.append(f"⚙️ {match_situation.replace('_', ' ').title()}")
            if ground:
                filters_context.append(f"📍 {ground}")
            if handedness:
                filters_context.append(f"👤 {handedness.replace('_', ' ').title()}")
            
            if filters_context:
                response += f"**Filters**: {' • '.join(filters_context)}\n\n"
            
            # H2H Stats Table
            response += "| Metric | Value |\n|--------|-------|\n"
            response += f"| Deliveries | {deliveries} |\n"
            response += f"| Runs | {runs} |\n"
            response += f"| Strike Rate | {strike_rate:.2f} |\n"
            response += f"| Dot Balls | {dot_balls} ({dot_percentage:.1f}%) |\n"
            
            if venue:
                response += f"| Venue | {venue} |\n"
            
            response += "\n"
            
            # Add insights section
            if insights:
                response += f"**Key Insights:**\n"
                for insight in insights:
                    response += f"• {insight}\n"
            
            response += f"\n{h2h_data.get('summary', '')}"
            
            return response
        
        except Exception as e:
            return f"Error getting head-to-head data: {str(e)}"
    
    def _get_player_stats_response(self, player: str, seasons: List[int] = None, 
                                    match_phase: Optional[str] = None, match_situation: Optional[str] = None,
                                    bowler_type: Optional[str] = None, opposition_team: Optional[str] = None,
                                    batter_role: Optional[str] = None, vs_conditions: Optional[str] = None,
                                    ground: Optional[str] = None, handedness: Optional[str] = None,
                                    inning: Optional[int] = None, match_type: Optional[str] = None) -> str:
        """Get player statistics with comprehensive filters: phases, situations, grounds, years, handedness, etc."""
        
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
            if ground:
                filters['ground'] = ground
            if handedness:
                filters['handedness'] = handedness
            if inning:
                filters['innings_order'] = inning  # stats_engine uses 'innings_order'
            if match_type:
                filters['match_type'] = match_type
            
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
                if vs_conditions and vs_conditions in ['vs_spin', 'vs_pace']:
                    response += f"🏏 **Batting Stats - {vs_conditions.replace('_', ' ').title()}**\n\n"
                    # Overall stats
                    response += "**TOTAL**\n"
                    response += "| Metric | Value |\n|--------|-------|\n"
                    response += f"| Matches | {bat.get('matches', 0)} |\n"
                    response += f"| Balls | {bat.get('balls', 0)} |\n"
                    response += f"| Runs | {bat.get('runs', 0)} |\n"
                    response += f"| Average | {bat.get('average', 0):.2f} |\n"
                    response += f"| Strike Rate | {bat.get('strike_rate', 0):.2f} |\n\n"
                    
                    # Get breakdown by sub-types
                    breakdown = self.stats_engine.get_bowling_subtype_breakdown(found_player, vs_conditions, filters)
                    if breakdown:
                        response += "**BREAKDOWN BY BOWLING TYPE**\n\n"
                        response += "| Bowling Type | Balls | Runs | Avg | SR |\n|---|---|---|---|---|\n"
                        for sub_type, sub_stats in breakdown.items():
                            type_label = sub_type.replace('vs_', '').replace('_', ' ').title()
                            balls = sub_stats.get('balls', 0)
                            runs = sub_stats.get('runs', 0)
                            avg = sub_stats.get('average', 0)
                            sr = sub_stats.get('strike_rate', 0)
                            response += f"| {type_label} | {balls} | {runs} | {avg:.2f} | {sr:.1f} |\n"
                    response += "\n"
                elif vs_conditions:
                    response += f"🏏 **Batting Stats - {vs_conditions.replace('_', ' ').title()}**\n\n"
                    response += "| Metric | Value |\n|--------|-------|\n"
                    response += f"| Matches | {bat.get('matches', 0)} |\n"
                    response += f"| Balls | {bat.get('balls', 0)} |\n"
                    response += f"| Runs | {bat.get('runs', 0)} |\n"
                    response += f"| Average | {bat.get('average', 0):.2f} |\n"
                    response += f"| Strike Rate | {bat.get('strike_rate', 0):.2f} |\n"
                    response += f"| Hundreds | {bat.get('centuries', 0)} |\n"
                    response += f"| Fifties | {bat.get('fifties', 0)} |\n"
                    response += f"| Fours | {bat.get('fours', 0)} |\n"
                    response += f"| Sixes | {bat.get('sixes', 0)} |\n\n"
                else:
                    response += f"🏏 **Batting Stats**\n\n"
                    response += "| Metric | Value |\n|--------|-------|\n"
                    response += f"| Matches | {bat.get('matches', 0)} |\n"
                    response += f"| Innings | {bat.get('innings', 0)} |\n"
                    response += f"| Balls | {bat.get('balls', 0)} |\n"
                    response += f"| Runs | {bat.get('runs', 0)} |\n"
                    response += f"| Average | {bat.get('average', 0):.2f} |\n"
                    response += f"| Strike Rate | {bat.get('strike_rate', 0):.2f} |\n"
                    response += f"| Highest Score | {bat.get('highest_score', 0)} |\n"
                    response += f"| Centuries | {bat.get('centuries', 0)} |\n"
                    response += f"| Fifties | {bat.get('fifties', 0)} |\n"
                    response += f"| Fours | {bat.get('fours', 0)} |\n"
                    response += f"| Sixes | {bat.get('sixes', 0)} |\n\n"
            
            if 'bowling' in stats and stats['bowling']:
                bowl = stats['bowling']
                response += f"🎳 **Bowling Stats**\n\n"
                response += "| Metric | Value |\n|--------|-------|\n"
                response += f"| Matches | {bowl.get('matches', 0)} |\n"
                response += f"| Innings | {bowl.get('innings', 0)} |\n"
                response += f"| Balls | {bowl.get('balls', 0)} |\n"
                response += f"| Wickets | {bowl.get('wickets', 0)} |\n"
                response += f"| Runs Conceded | {bowl.get('runs_conceded', 0)} |\n"
                response += f"| Average | {bowl.get('average', 0):.2f} |\n"
                response += f"| Economy | {bowl.get('economy', 0):.2f} |\n"
                response += f"| Best Figures | {bowl.get('best_figures', 'N/A')} |\n"
                response += f"| Maiden Overs | {bowl.get('maiden_overs', 0)} |\n\n"
                
                # Get bowling breakdown by batter handedness
                breakdown = self.stats_engine.get_bowling_handedness_breakdown(found_player, filters)
                if breakdown and len(breakdown) > 0:
                    response += "**BREAKDOWN BY BATTER HANDEDNESS**\n\n"
                    response += "| Batter Type | Balls | Wickets | Runs | Economy |\n|---|---|---|---|---|\n"
                    for hand_type, hand_stats in breakdown.items():
                        hand_label = hand_type.replace('vs_', '').replace('_', ' ').title()
                        balls = hand_stats.get('balls', 0)
                        wickets = hand_stats.get('wickets', 0)
                        runs = hand_stats.get('runs_conceded', 0)
                        economy = hand_stats.get('economy', 0)
                        response += f"| {hand_label} | {balls} | {wickets} | {runs} | {economy:.2f} |\n"
            
            return response
        
        except Exception as e:
            return f"Error getting player stats: {str(e)}"
    
    def _get_player_primary_skill(self, player: str) -> str:
        """Determine if player is primarily a batter, bowler, or all-rounder"""
        try:
            overall_stats = self.stats_engine.get_player_stats(player)
            if not overall_stats:
                return 'unknown'
            
            batting_matches = overall_stats.get('batting', {}).get('matches', 0)
            bowling_matches = overall_stats.get('bowling', {}).get('matches', 0)
            
            # If only bats
            if batting_matches > 0 and bowling_matches == 0:
                return 'batter'
            # If only bowls
            elif bowling_matches > 0 and batting_matches == 0:
                return 'bowler'
            # If both with significant usage
            elif batting_matches > 0 and bowling_matches > 0:
                # Check which one is more frequently used
                batting_balls = overall_stats.get('batting', {}).get('balls', 0)
                bowling_balls = overall_stats.get('bowling', {}).get('balls', 0)
                
                if bowling_balls > batting_balls:
                    return 'bowler'  # Primary skill is bowling
                elif batting_balls > bowling_balls:
                    return 'batter'  # Primary skill is batting
                else:
                    return 'all-rounder'  # Equal usage
            else:
                return 'unknown'
        except:
            return 'unknown'
    
    def _get_trends_response(self, player: str, time_period: Optional[str] = None, 
                            match_phase: Optional[str] = None, 
                            match_situation: Optional[str] = None,
                            seasons: Optional[List[int]] = None) -> str:
        """Get performance trend analysis for a player - shows appropriate stats based on primary skill"""
        try:
            found_player = self.stats_engine.find_player(player)
            if not found_player:
                return f"Player '{player}' not found."
            
            # Parse time period to get N matches/innings
            n_period = 5  # Default
            
            if time_period:
                time_lower = time_period.lower()
                import re
                
                # Extract the number from "last N"
                match = re.search(r'(\d+)', time_lower)
                if match:
                    n_period = int(match.group(1))
            
            # Determine player's primary skill
            primary_skill = self._get_player_primary_skill(found_player)
            
            # For bowlers or all-rounders: get last N matches (show bowling first)
            # For batters: get last N innings (show batting)
            if primary_skill == 'bowler':
                return self._get_bowler_trends(found_player, n_period, match_phase, match_situation)
            elif primary_skill == 'all-rounder':
                return self._get_all_rounder_trends(found_player, n_period, match_phase, match_situation)
            else:  # batter or unknown - default to batting
                return self._get_batter_trends(found_player, n_period, match_phase, match_situation)
        
        except Exception as e:
            return f"Error analyzing trends: {str(e)}"
    
    def _get_batter_trends(self, player: str, n_period: int, match_phase: Optional[str] = None, 
                           match_situation: Optional[str] = None) -> str:
        """Show batting performance trends for batters"""
        try:
            # Get last N innings data
            innings_data = self.stats_engine.get_last_n_innings(player, n_period)
            
            if not innings_data:
                overall_stats = self.stats_engine.get_player_stats(player)
                if overall_stats and 'batting' in overall_stats and overall_stats['batting']:
                    response = f"📈 **{player} - Career Batting Stats (No Recent Innings Data)**\n\n"
                    response += "🏏 **Batting Statistics**\n\n"
                    bat = overall_stats['batting']
                    response += "| Metric | Value |\n|--------|-------|\n"
                    response += f"| Matches | {bat.get('matches', 0)} |\n"
                    response += f"| Runs | {bat.get('runs', 0)} |\n"
                    response += f"| Average | {bat.get('average', 0):.2f} |\n"
                    response += f"| Strike Rate | {bat.get('strike_rate', 0):.2f} |\n\n"
                    return response
                return f"No data available for {player}."
            
            # Filter meaningful innings (3+ balls)
            meaningful_innings = [i for i in innings_data if i['balls'] >= 3]
            
            if not meaningful_innings:
                return f"No recent batting data for {player}."
            
            # Show batting breakdown
            response = f"📈 **{player} - Last {len(meaningful_innings)} Batting Innings**\n\n"
            response += "🏏 **Batting Performance**\n\n"
            response += "| Inning | Opposition | Runs | Balls | SR |\n"
            response += "|--------|------------|------|-------|----|\n"
            
            for i, inning in enumerate(meaningful_innings, 1):
                sr = (inning['runs'] / inning['balls'] * 100) if inning['balls'] > 0 else 0
                # Show asterisk on score ONLY if not out (dismissed = False)
                runs_display = f"{inning['runs']}*" if inning['balls'] > 0 and not inning['dismissed'] else str(inning['runs'])
                response += f"| {i} | {inning['opposition'][:12]} | {runs_display} | {inning['balls']} | {sr:.1f} |\n"
            
            response += "\n"
            
            # Calculate averages
            total_runs = sum(m['runs'] for m in meaningful_innings)
            total_balls = sum(m['balls'] for m in meaningful_innings)
            avg_sr = (total_runs / total_balls * 100) if total_balls > 0 else 0
            innings_count = len([m for m in meaningful_innings if m['balls'] > 0])
            
            if innings_count > 0:
                response += f"**Recent Stats**: Average {total_runs / innings_count:.1f} | Strike Rate {avg_sr:.1f}\n\n"
            
            return response
        except Exception as e:
            return f"Error analyzing batter trends: {str(e)}"
    
    def _get_bowler_trends(self, player: str, n_period: int, match_phase: Optional[str] = None, 
                          match_situation: Optional[str] = None) -> str:
        """Show bowling performance trends for bowlers"""
        try:
            # Get last N matches data
            matches_data = self.stats_engine.get_last_n_matches(player, n_period)
            
            if not matches_data:
                return f"No recent data available for {player}."
            
            # Show bowling breakdown first
            response = f"📈 **{player} - Last {len(matches_data)} Matches Bowling Performance**\n\n"
            response += "🎳 **Bowling Stats**\n\n"
            response += "| Match # | Opposition | Wickets | Runs | Balls | Economy |\n"
            response += "|---------|------------|---------|------|-------|----------|\n"
            
            bowled_count = 0
            for i, match in enumerate(matches_data, 1):
                bowl = match['bowling']
                if bowl['balls'] > 0:
                    overs = bowl['balls'] / 6
                    economy = (bowl['runs'] / overs) if overs > 0 else 0
                    response += f"| {i} | {match['opposition'][:12]} | {bowl['wickets']} | {bowl['runs']} | {bowl['balls']} | {economy:.2f} |\n"
                    bowled_count += 1
                else:
                    response += f"| {i} | {match['opposition'][:12]} | - | - | - | Did not bowl |\n"
            
            response += "\n"
            
            # Calculate bowling averages
            total_wickets = sum(m['bowling']['wickets'] for m in matches_data if m['bowling']['balls'] > 0)
            total_runs_conceded = sum(m['bowling']['runs'] for m in matches_data if m['bowling']['balls'] > 0)
            total_balls_bowled = sum(m['bowling']['balls'] for m in matches_data if m['bowling']['balls'] > 0)
            
            if total_balls_bowled > 0:
                avg_economy = (total_runs_conceded / (total_balls_bowled / 6))
                response += f"**Recent Bowling Stats**: {total_wickets} wickets | Economy {avg_economy:.2f}\n\n"
            
            # Also show batting stats if the bowler has meaningful batting
            batting_data = [m for m in matches_data if m.get('batting', {}).get('balls', 0) >= 3]
            if batting_data:
                response += "---\n\n"
                response += f"🏏 **Also Contributed with Bat**\n\n"
                response += "| Match # | Opposition | Runs | Balls | SR |\n"
                response += "|---------|------------|------|-------|----|\n"
                
                for i, match in enumerate(batting_data, 1):
                    bat = match['batting']
                    if bat['balls'] > 0:
                        sr = (bat['runs'] / bat['balls'] * 100) if bat['balls'] > 0 else 0
                        response += f"| {i} | {match['opposition'][:12]} | {bat['runs']} | {bat['balls']} | {sr:.1f} |\n"
            
            return response
        except Exception as e:
            return f"Error analyzing bowler trends: {str(e)}"
    
    def _get_all_rounder_trends(self, player: str, n_period: int, match_phase: Optional[str] = None, 
                               match_situation: Optional[str] = None) -> str:
        """Show both batting and bowling trends for all-rounders"""
        try:
            matches_data = self.stats_engine.get_last_n_matches(player, n_period)
            
            if not matches_data:
                return f"No recent data available for {player}."
            
            response = f"📈 **{player} - Last {len(matches_data)} Matches Performance (All-Rounder)**\n\n"
            
            # Batting section
            batting_data = [m for m in matches_data if m.get('batting', {}).get('balls', 0) >= 3]
            if batting_data:
                response += "🏏 **Batting Performance**\n\n"
                response += "| Match # | Opposition | Runs | Balls | SR |\n"
                response += "|---------|------------|------|-------|----|\n"
                
                for i, match in enumerate(batting_data, 1):
                    bat = match['batting']
                    sr = (bat['runs'] / bat['balls'] * 100) if bat['balls'] > 0 else 0
                    response += f"| {i} | {match['opposition'][:12]} | {bat['runs']} | {bat['balls']} | {sr:.1f} |\n"
                
                response += "\n"
            
            # Bowling section
            bowling_data = [m for m in matches_data if m.get('bowling', {}).get('balls', 0) > 0]
            if bowling_data:
                response += "🎳 **Bowling Performance**\n\n"
                response += "| Match # | Opposition | Wickets | Runs | Economy |\n"
                response += "|---------|------------|---------|------|----------|\n"
                
                for i, match in enumerate(bowling_data, 1):
                    bowl = match['bowling']
                    overs = bowl['balls'] / 6
                    economy = (bowl['runs'] / overs) if overs > 0 else 0
                    response += f"| {i} | {match['opposition'][:12]} | {bowl['wickets']} | {bowl['runs']} | {economy:.2f} |\n"
                
                response += "\n"
            
            # Overall summary
            if batting_data or bowling_data:
                bat_runs = sum(m['batting']['runs'] for m in matches_data if m['batting']['balls'] >= 3)
                ball_wickets = sum(m['bowling']['wickets'] for m in matches_data if m['bowling']['balls'] > 0)
                response += f"**Recent Impact**: {bat_runs} runs | {ball_wickets} wickets\n\n"
            
            return response
        except Exception as e:
            return f"Error analyzing all-rounder trends: {str(e)}"
    
    
    def _get_records_response(self, player: Optional[str] = None, record_type: Optional[str] = None,
                             seasons: Optional[List[int]] = None,
                             match_phase: Optional[str] = None) -> str:
        """Get record information for a player"""
        try:
            if not player:
                return "Please specify a player for record analysis."
            
            found_player = self.stats_engine.find_player(player)
            if not found_player:
                return f"Player '{player}' not found."
            
            # Get player records
            records = self.stats_engine.get_player_records(found_player)
            
            if 'error' in records:
                return f"No record data available for {found_player}."
            
            response = f"🏆 **{found_player} - IPL Records**\n\n"
            
            # Batting records
            bat_records = records.get('batting_records', {})
            response += "🏏 **Batting Records**\n\n"
            response += "| Record | Value |\n|--------|-------|\n"
            response += f"| Highest Score | {bat_records.get('highest_score', 0)} |\n"
            response += f"| Total Runs | {bat_records.get('total_runs', 0)} |\n"
            response += f"| Total Matches | {bat_records.get('total_matches', 0)} |\n"
            response += f"| Centuries | {bat_records.get('centuries', 0)} |\n"
            response += f"| Half-Centuries | {bat_records.get('half_centuries', 0)} |\n"
            response += f"| Sixes | {bat_records.get('total_sixes', 0)} |\n"
            response += f"| Fours | {bat_records.get('total_fours', 0)} |\n"
            response += f"| Average | {bat_records.get('batting_average', 0):.2f} |\n"
            response += f"| Strike Rate | {bat_records.get('strike_rate', 0):.2f} |\n\n"
            
            # Bowling records
            bowl_records = records.get('bowling_records', {})
            if bowl_records.get('total_wickets', 0) > 0:
                response += "🎳 **Bowling Records**\n\n"
                response += "| Record | Value |\n|--------|-------|\n"
                response += f"| Total Wickets | {bowl_records.get('total_wickets', 0)} |\n"
                response += f"| Best Figures | {bowl_records.get('best_figures', 'N/A')} |\n"
                response += f"| Total Matches | {bowl_records.get('total_matches', 0)} |\n"
                response += f"| Runs Conceded | {bowl_records.get('runs_conceded', 0)} |\n"
                response += f"| Economy | {bowl_records.get('economy', 0):.2f} |\n"
                response += f"| Average | {bowl_records.get('bowling_average', 0):.2f} |\n"
                response += f"| Maiden Overs | {bowl_records.get('maiden_overs', 0)} |\n\n"
            
            return response
        
        except Exception as e:
            return f"Error retrieving records: {str(e)}"
    
    def _get_rankings_response(self, metric: Optional[str] = None, seasons: Optional[List[int]] = None,
                               match_phase: Optional[str] = None, ground: Optional[str] = None,
                               limit: int = 10) -> str:
        """Get rankings of players by various metrics"""
        try:
            if not metric:
                metric = 'runs'  # Default to runs
            
            # Normalize metric name
            metric = metric.lower().replace('-', '_')
            
            # Get league rankings
            rankings = self.stats_engine.get_league_rankings(
                metric=metric, 
                seasons=seasons, 
                match_phase=match_phase, 
                limit=limit
            )
            
            if not rankings:
                return f"No ranking data available for metric: {metric}"
            
            metric_display = rankings[0]['metric'] if rankings else metric.replace('_', ' ').title()
            response = f"🏅 **IPL Rankings - Top {limit} by {metric_display}**\n\n"
            response += "| Rank | Player | Value |\n|------|--------|-------|\n"
            
            for i, ranking in enumerate(rankings, 1):
                value = ranking['value']
                if isinstance(value, float):
                    response += f"| {i} | {ranking['player']} | {value:.2f} |\n"
                else:
                    response += f"| {i} | {ranking['player']} | {value} |\n"
            
            response += f"\n📊 *Ranking metric: {metric_display}"
            if seasons:
                response += f" | Seasons: {', '.join(map(str, seasons))}"
            if match_phase:
                response += f" | Phase: {match_phase.replace('_', ' ').title()}"
            response += "*"
            
            return response
        
        except Exception as e:
            return f"Error retrieving rankings: {str(e)}"
    
    def _get_ground_insights_response(self, player: str, ground: str) -> str:
        """Get performance insights for a player at a specific ground"""
        try:
            found_player = self.stats_engine.find_player(player)
            if not found_player:
                return f"Player '{player}' not found."
            
            # Get ground performance
            perf = self.stats_engine.get_ground_performance(found_player, ground)
            
            if 'error' in perf:
                return f"No data available for {found_player} at {ground}."
            
            response = f"📍 **{found_player} at {ground}**\n\n"
            
            # Batting stats at venue
            bat = perf.get('batting', {})
            if bat.get('matches', 0) > 0:
                response += "🏏 **Batting at this Venue**\n\n"
                response += "| Metric | Value |\n|--------|-------|\n"
                response += f"| Matches | {bat.get('matches', 0)} |\n"
                response += f"| Runs | {bat.get('runs', 0)} |\n"
                response += f"| Average | {bat.get('average', 0):.2f} |\n"
                response += f"| Strike Rate | {bat.get('strike_rate', 0):.2f} |\n"
                response += f"| Highest Score | {bat.get('highest_score', 0)} |\n"
                response += f"| Centuries | {bat.get('centuries', 0)} |\n"
                response += f"| Half-Centuries | {bat.get('fifties', 0)} |\n\n"
            
            # Bowling stats at venue
            bowl = perf.get('bowling', {})
            if bowl.get('matches', 0) > 0:
                response += "🎳 **Bowling at this Venue**\n\n"
                response += "| Metric | Value |\n|--------|-------|\n"
                response += f"| Matches | {bowl.get('matches', 0)} |\n"
                response += f"| Wickets | {bowl.get('wickets', 0)} |\n"
                response += f"| Runs Conceded | {bowl.get('runs_conceded', 0)} |\n"
                response += f"| Economy | {bowl.get('economy', 0):.2f} |\n"
                response += f"| Average | {bowl.get('average', 0):.2f} |\n"
                response += f"| Best Figures | {bowl.get('best_figures', 'N/A')} |\n\n"
            
            if bat.get('matches', 0) == 0 and bowl.get('matches', 0) == 0:
                return f"{found_player} has not played at {ground}."
            
            return response
        
        except Exception as e:
            return f"Error analyzing ground insights: {str(e)}"
    
    def _get_form_guide_response(self, player: Optional[str] = None, time_period: Optional[str] = None) -> str:
        """Get current form analysis for a player - last 5 matches breakdown"""
        try:
            if not player:
                return "Please specify a player for form analysis."
            
            found_player = self.stats_engine.find_player(player)
            if not found_player:
                return f"Player '{player}' not found."
            
            # Get last 5 matches data
            matches_data = self.stats_engine.get_last_n_matches(found_player, 5)
            
            if not matches_data:
                return f"No recent match data available for {found_player}."
            
            # Check if player is batter or bowler
            has_batting = any(m['batting']['balls'] > 0 for m in matches_data)
            has_bowling = any(m['bowling']['balls'] > 0 for m in matches_data)
            
            # Calculate form status
            form_status = "⚪ NO RECENT DATA"
            if has_batting:
                bat_runs = sum(m['batting']['runs'] for m in matches_data if m['batting']['balls'] > 0)
                bat_matches = len([m for m in matches_data if m['batting']['balls'] > 0])
                bat_avg = bat_runs / bat_matches if bat_matches > 0 else 0
                
                if bat_avg > 35:
                    form_status = "✅ **EXCELLENT FORM** 🔥"
                elif bat_avg > 28:
                    form_status = "✅ **GOOD FORM** ✅"
                elif bat_avg > 20:
                    form_status = "⚪ **AVERAGE FORM** ⚪"
                elif bat_avg > 10:
                    form_status = "⚠️ **POOR FORM** ⚠️"
                else:
                    form_status = "📉 **OUT OF FORM** ❌"
            elif has_bowling:
                bowl_wickets = sum(m['bowling']['wickets'] for m in matches_data if m['bowling']['balls'] > 0)
                bowl_matches = len([m for m in matches_data if m['bowling']['balls'] > 0])
                
                if bowl_wickets >= 5:
                    form_status = "✅ **EXCELLENT FORM** 🔥"
                elif bowl_wickets >= 3:
                    form_status = "✅ **GOOD FORM** ✅"
                elif bowl_wickets > 0:
                    form_status = "⚪ **AVERAGE FORM** ⚪"
                else:
                    form_status = "⚠️ **POOR FORM** ⚠️"
            
            response = f"📊 **{found_player} - Form Guide (Last 5 Matches)**\n\n"
            response += f"{form_status}\n\n"
            
            # Batting breakdown
            if has_batting:
                response += "🏏 **Batting in Last 5 Innings**\n\n"
                response += "| Inning | Opposition | Runs | Balls | SR | Result |\n"
                response += "|--------|------------|------|-------|----|---------|\n"
                
                for i, match in enumerate(matches_data, 1):
                    bat = match['batting']
                    if bat['balls'] > 0:
                        sr = (bat['runs'] / bat['balls'] * 100) if bat['balls'] > 0 else 0
                        result = f"{'💯' if bat['runs'] > 50 else '🔥' if bat['runs'] > 30 else '⚪' if bat['runs'] > 10 else '❌'} {'Out' if bat['dismissed'] else 'Not Out'}"
                        response += f"| {i} | {match['opposition'][:12]} | {bat['runs']} | {bat['balls']} | {sr:.1f} | {result} |\n"
                
                response += "\n"
            
            # Bowling breakdown
            if has_bowling:
                response += "🎳 **Bowling in Last 5 Matches**\n\n"
                response += "| Match | Opposition | Wickets | Runs | Economy | Status |\n"
                response += "|-------|------------|---------|------|---------|--------|\n"
                
                for i, match in enumerate(matches_data, 1):
                    bowl = match['bowling']
                    if bowl['balls'] > 0:
                        overs = bowl['balls'] / 6
                        economy = (bowl['runs'] / overs) if overs > 0 else 0
                        status = f"{'🔥' if bowl['wickets'] > 1 else '✅' if bowl['wickets'] == 1 else '⚪'}"
                        response += f"| {i} | {match['opposition'][:12]} | {bowl['wickets']} | {bowl['runs']} | {economy:.2f} | {status} |\n"
                
                response += "\n"
            
            return response
        
        except Exception as e:
            return f"Error analyzing form: {str(e)}"
    
    def _get_comparative_analysis_response(self, player1: Optional[str] = None, player2: Optional[str] = None,
                                          player_list: Optional[List[str]] = None,
                                          comparison_type: Optional[str] = None,
                                          match_phase: Optional[str] = None) -> str:
        """Compare multiple players or player vs league average"""
        try:
            if not player1 and not player_list:
                return "Please specify players to compare (e.g., 'kohli vs sharma' or 'top batters')."
            
            response = f"⚖️ **Comparative Analysis**\n\n"
            
            if player1 and player2:
                p1 = self.stats_engine.find_player(player1)
                p2 = self.stats_engine.find_player(player2)
                
                if not p1 or not p2:
                    return "One or both players not found."
                
                # Get full stats for both players
                stats1 = self.stats_engine.get_player_stats(p1)
                stats2 = self.stats_engine.get_player_stats(p2)
                
                response += f"**{p1} vs {p2}**\n\n"
                response += "| Metric | " + p1 + " | " + p2 + " | Advantage |\n"
                response += "|--------|--------|--------|----------|\n"
                
                # Batting comparison
                bat1 = stats1.get('batting', {})
                bat2 = stats2.get('batting', {})
                
                if bat1.get('runs', 0) > 0 or bat2.get('runs', 0) > 0:
                    response += f"| Runs | {bat1.get('runs', 0)} | {bat2.get('runs', 0)} | "
                    response += (p1 if bat1.get('runs', 0) > bat2.get('runs', 0) else (p2 if bat2.get('runs', 0) > bat1.get('runs', 0) else "Equal")) + " |\n"
                    
                    avg1 = bat1.get('average', 0)
                    avg2 = bat2.get('average', 0)
                    response += f"| Batting Average | {avg1:.2f} | {avg2:.2f} | "
                    response += (p1 if avg1 > avg2 else (p2 if avg2 > avg1 else "Equal")) + " |\n"
                    
                    sr1 = bat1.get('strike_rate', 0)
                    sr2 = bat2.get('strike_rate', 0)
                    response += f"| Strike Rate | {sr1:.2f} | {sr2:.2f} | "
                    response += (p1 if sr1 > sr2 else (p2 if sr2 > sr1 else "Equal")) + " |\n"
                
                # Bowling comparison
                bowl1 = stats1.get('bowling', {})
                bowl2 = stats2.get('bowling', {})
                
                if bowl1.get('wickets', 0) > 0 or bowl2.get('wickets', 0) > 0:
                    response += f"| Wickets | {bowl1.get('wickets', 0)} | {bowl2.get('wickets', 0)} | "
                    response += (p1 if bowl1.get('wickets', 0) > bowl2.get('wickets', 0) else (p2 if bowl2.get('wickets', 0) > bowl1.get('wickets', 0) else "Equal")) + " |\n"
                    
                    econ1 = bowl1.get('economy', 0)
                    econ2 = bowl2.get('economy', 0)
                    response += f"| Economy | {econ1:.2f} | {econ2:.2f} | "
                    response += (p2 if econ1 > econ2 else (p1 if econ2 > econ1 else "Equal")) + " |\n"  # Lower economy is better
                
                response += "\n**Summary**: Direct comparison of career statistics between players.\n"
            
            elif player_list and len(player_list) > 0:
                # Compare multiple players
                players = [self.stats_engine.find_player(p) for p in player_list if self.stats_engine.find_player(p)]
                
                if not players:
                    return "No players found for comparison."
                
                response += f"**Comparing {len(players)} Players**\n\n"
                response += "| Player | Runs | Wickets | Strike Rate | Economy |\n"
                response += "|--------|------|---------|-------------|----------|\n"
                
                for player in players:
                    stats = self.stats_engine.get_player_stats(player)
                    bat = stats.get('batting', {})
                    bowl = stats.get('bowling', {})
                    
                    runs = bat.get('runs', 0)
                    wickets = bowl.get('wickets', 0)
                    sr = bat.get('strike_rate', 0)
                    econ = bowl.get('economy', 0)
                    
                    response += f"| {player} | {runs} | {wickets} | {sr:.2f} | {econ:.2f} |\n"
            
            return response
        
        except Exception as e:
            return f"Error in comparative analysis: {str(e)}"
    
    def _get_predictions_response(self, opposition_team: Optional[str] = None,
                                 match_phase: Optional[str] = None) -> str:
        """Provide data-driven recommendations and predictions"""
        try:
            response = f"🎯 **Data-Driven Predictions & Recommendations**\n\n"
            
            # Get top performers who play in this phase
            if match_phase:
                phase_display = match_phase.replace('_', ' ').title()
            else:
                phase_display = "All Phases"
            
            # Get top run scorers
            top_batters = self.stats_engine.get_league_rankings(metric='runs', limit=5)
            if top_batters:
                response += f"📈 **Top Scorers (for {phase_display})**\n\n"
                for i, batter in enumerate(top_batters, 1):
                    response += f"{i}. **{batter['player']}** - {batter['value']} runs\n"
                response += "\n"
            
            # Get top bowlers
            top_bowlers = self.stats_engine.get_league_rankings(metric='wickets', limit=5)
            if top_bowlers:
                response += f"🎳 **Top Bowlers (for {phase_display})**\n\n"
                for i, bowler in enumerate(top_bowlers, 1):
                    response += f"{i}. **{bowler['player']}** - {bowler['value']} wickets\n"
                response += "\n"
            
            # Strategic recommendations
            response += "**Strategic Recommendations**\n\n"
            response += "| Aspect | Recommendation | Rationale |\n|--------|-----------------|----------|\n"
            
            if match_phase == 'powerplay' or match_phase == 'opening':
                response += "| Batting | Consolidate & Build | Field restrictions - settle in for good start |\n"
                response += "| Bowling | New ball attack | Early wickets critical with short boundaries |\n"
                response += "| Strategy | Aggressive Defense | Take calculated risks to build momentum |\n"
            elif match_phase == 'death_overs' or match_phase == 'closing':
                response += "| Batting | Maximum Risk-Taking | Push for big shots - maximize final overs |\n"
                response += "| Bowling | Vary pace & line | Yorkers and slower balls crucial |\n"
                response += "| Strategy | Defensive Placement | Block boundaries - slower approach |\n"
            else:
                response += "| Batting | Build Platform | Balance between scoring and stability |\n"
                response += "| Bowling | Control & Variation | Vary pace and spin - contain opposition |\n"
                response += "| Strategy | Flexible Approach | Adapt to match situation |\n"
            
            response += "\n📊 **Data-Driven Insight**: Recommendations based on IPL historical analysis and statistical trends."
            
            return response
        
        except Exception as e:
            return f"Error generating predictions: {str(e)}"
    
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

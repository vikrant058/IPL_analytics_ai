import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from difflib import SequenceMatcher
import json
import os
from data_loader import IPLDataLoader

class StatsEngine:
    """Calculate cricket statistics from IPL data"""
    
    def __init__(self, matches_df: pd.DataFrame, deliveries_df: pd.DataFrame):
        self.matches_df = matches_df
        self.deliveries_df = deliveries_df
        self._player_cache = None
        self._team_cache = None
        self._aliases = self._load_aliases()
        self._bowler_types = self._load_bowler_types()
        self._batter_handedness = self._load_batter_handedness()
    
    def _load_aliases(self) -> Dict:
        """Load player and team aliases from JSON file"""
        try:
            alias_file = os.path.join(os.path.dirname(__file__), 'player_aliases.json')
            with open(alias_file, 'r') as f:
                data = json.load(f)
                return data.get('aliases', {})
        except FileNotFoundError:
            return {}
    
    def _load_bowler_types(self) -> Dict:
        """Load bowler type classifications from JSON file"""
        try:
            bowler_file = os.path.join(os.path.dirname(__file__), 'bowler_types.json')
            with open(bowler_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def _load_batter_handedness(self) -> Dict:
        """Load batter handedness (left/right) from JSON file"""
        try:
            hand_file = os.path.join(os.path.dirname(__file__), 'batter_handedness.json')
            with open(hand_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {'right_hand_batters': [], 'left_hand_batters': []}
    
    def _get_all_players(self) -> List[str]:
        """Get cached list of all unique players"""
        if self._player_cache is None:
            batters = self.deliveries_df['batter'].unique().tolist()
            bowlers = self.deliveries_df['bowler'].unique().tolist()
            self._player_cache = list(set(batters + bowlers))
        return self._player_cache
    
    def _get_all_teams(self) -> List[str]:
        """Get cached list of all unique teams"""
        if self._team_cache is None:
            teams = pd.concat([self.matches_df['team1'], self.matches_df['team2']]).unique()
            self._team_cache = teams.tolist()
        return self._team_cache
    
    def find_player(self, query: str) -> str:
        """Find player by fuzzy matching. Returns best match or None"""
        all_players = self._get_all_players()
        query_lower = query.lower().strip()
        
        # 1. Check aliases first - most reliable
        for player_name, aliases in self._aliases.items():
            if player_name in all_players:  # Make sure player exists in dataset
                for alias in aliases:
                    if alias.lower() == query_lower:
                        return player_name
        
        # 2. Exact match (case-insensitive)
        for player in all_players:
            if player.lower() == query_lower:
                return player
        
        # 3. Check if query matches as alias substring
        query_words = query_lower.split()
        for player_name, aliases in self._aliases.items():
            if player_name in all_players:
                for alias in aliases:
                    if query_lower in alias.lower():
                        return player_name
        
        # 4. Multi-word matching with player name parts
        if len(query_words) > 1:
            candidates = []
            for player in all_players:
                player_lower = player.lower()
                player_parts = player_lower.split()
                
                matches = 0
                for qword in query_words:
                    for ppart in player_parts:
                        if qword in ppart and len(qword) > 1:
                            matches += 1
                            break
                
                if matches == len(query_words):
                    match_count = self._count_player_matches(player)
                    candidates.append((player, match_count))
            
            if candidates:
                return max(candidates, key=lambda x: x[1])[0]
        
        # 5. Single word - substring match with priority on last name
        candidates = []
        for player in all_players:
            player_lower = player.lower()
            if query_lower in player_lower:
                player_parts = player_lower.split()
                is_last_name_match = query_lower in player_parts[-1]
                match_count = self._count_player_matches(player)
                candidates.append((player, is_last_name_match, match_count))
        
        if candidates:
            candidates.sort(key=lambda x: (-x[1], -x[2]))
            return candidates[0][0]
        
        # 6. Fuzzy match with threshold
        best_matches = []
        for player in all_players:
            ratio = SequenceMatcher(None, query_lower, player.lower()).ratio()
            if ratio > 0.7:
                match_count = self._count_player_matches(player)
                best_matches.append((player, ratio, match_count))
        
        if best_matches:
            best_matches.sort(key=lambda x: (-x[1], -x[2]))
            return best_matches[0][0]
        
        return None
    
    def _count_player_matches(self, player_name: str) -> int:
        """Count total deliveries for a player"""
        batter_count = len(self.deliveries_df[self.deliveries_df['batter'] == player_name])
        bowler_count = len(self.deliveries_df[self.deliveries_df['bowler'] == player_name])
        return batter_count + bowler_count
    
    def find_team(self, query: str) -> str:
        """Find team by fuzzy matching"""
        all_teams = self._get_all_teams()
        query_lower = query.lower()
        
        for team in all_teams:
            if team.lower() == query_lower or query_lower in team.lower():
                return team
        
        best_match = None
        best_ratio = 0
        for team in all_teams:
            ratio = SequenceMatcher(None, query_lower, team.lower()).ratio()
            if ratio > best_ratio and ratio > 0.6:
                best_ratio = ratio
                best_match = team
        
        return best_match
    
    def get_player_stats(self, player: str, filters: Dict = None) -> Dict:
        """Get comprehensive stats for a player with optional filters
        
        Filters: {
            'seasons': [list of seasons like '2008', '2020'],
            'venue': [list of venue names],
            'team': [list of team names],
            'home_away': 'home' or 'away' or None for all,
            'innings_order': 1 or 2 or None for all
        }
        """
        # Try to find the player first
        found_player = self.find_player(player)
        if not found_player:
            return {'error': f'Player {player} not found'}
        
        # Calculate overall matches from batting OR bowling appearances
        total_matches = self._get_total_matches(found_player, filters)
        
        batting_stats = self._get_batting_stats(found_player, filters, total_matches)
        bowling_stats = self._get_bowling_stats(found_player, filters, total_matches)
        
        return {
            'player': found_player,
            'batting': batting_stats,
            'bowling': bowling_stats
        }
    
    def get_last_n_matches(self, player: str, n: int = 5) -> List[Dict]:
        """Get match-by-match data for player's last N appearances"""
        found_player = self.find_player(player)
        if not found_player:
            return []
        
        # Get all matches where player appeared (batting or bowling)
        batter_matches = self.deliveries_df[self.deliveries_df['batter'] == found_player][['match_id']].drop_duplicates()
        bowler_matches = self.deliveries_df[self.deliveries_df['bowler'] == found_player][['match_id']].drop_duplicates()
        
        # Union of all matches
        all_matches = set(batter_matches['match_id'].unique()) | set(bowler_matches['match_id'].unique())
        
        # Get match details sorted by date (descending - most recent first)
        match_ids = sorted(list(all_matches), key=lambda x: -x)[:n]
        
        results = []
        for match_id in match_ids:
            match_info = self.matches_df[self.matches_df['id'] == match_id].iloc[0] if not self.matches_df[self.matches_df['id'] == match_id].empty else None
            if match_info is None:
                continue
            
            # Get batting data for this match
            bat_deliv = self.deliveries_df[(self.deliveries_df['match_id'] == match_id) & 
                                          (self.deliveries_df['batter'] == found_player)]
            
            # Get bowling data for this match
            bowl_deliv = self.deliveries_df[(self.deliveries_df['match_id'] == match_id) & 
                                           (self.deliveries_df['bowler'] == found_player)]
            
            # Calculate batting score if batted
            bat_runs = 0
            bat_balls = 0
            dismissed = False
            if len(bat_deliv) > 0:
                for _, deliv in bat_deliv.iterrows():
                    bat_runs += deliv['batter_runs']
                    bat_balls += 1
                    if deliv['wicket'] == 1:
                        dismissed = True
            
            # Calculate bowling figures if bowled
            bowl_balls = 0
            bowl_runs = 0
            bowl_wickets = 0
            if len(bowl_deliv) > 0:
                for _, deliv in bowl_deliv.iterrows():
                    bowl_balls += 1
                    bowl_runs += deliv['total_runs']
                    if deliv['wicket'] == 1:
                        bowl_wickets += 1
            
            results.append({
                'match_id': match_id,
                'date': match_info['date'] if 'date' in match_info else 'N/A',
                'season': match_info['season'] if 'season' in match_info else 'N/A',
                'batting_team': match_info['batting_team'] if 'batting_team' in match_info else 'N/A',
                'opposition': match_info['bowling_team'] if 'bowling_team' in match_info else 'N/A',
                'batting': {
                    'runs': bat_runs,
                    'balls': bat_balls,
                    'dismissed': dismissed
                },
                'bowling': {
                    'wickets': bowl_wickets,
                    'runs': bowl_runs,
                    'balls': bowl_balls
                }
            })
        
        return results
    
    def _apply_filters(self, deliveries_df: pd.DataFrame, filters: Dict) -> pd.DataFrame:
        """Apply filters to deliveries dataframe"""
        if not filters:
            return deliveries_df
        
        df = deliveries_df.copy()
        
        # Merge with matches to get match metadata
        df = df.merge(self.matches_df[['id', 'year', 'season', 'venue', 'team1', 'team2']], 
                      left_on='match_id', right_on='id', how='left')
        
        # Season/Year filter
        if filters.get('seasons'):
            df = df[df['year'].isin(filters['seasons'])]
        
        # Venue filter
        if filters.get('venue'):
            venues = filters['venue'] if isinstance(filters['venue'], list) else [filters['venue']]
            df = df[df['venue'].isin(venues)]
        
        # Team filter (must be batting team for batting stats, bowling team for bowling)
        # This is handled in individual stat functions
        
        # Home/Away filter
        if filters.get('home_away'):
            if filters['home_away'].lower() == 'home':
                df = df[df['batting_team'] == df['team1']]
            elif filters['home_away'].lower() == 'away':
                df = df[df['batting_team'] == df['team2']]
        
        # Innings order filter (1 = batting first, 2 = batting second)
        if filters.get('innings_order'):
            df = df[df['inning'] == filters['innings_order']]
        
        return df.drop(columns=['id', 'year', 'season', 'venue', 'team1', 'team2'], errors='ignore')
    
    def _get_total_matches(self, player: str, filters: Dict = None) -> int:
        """Get total matches where player appeared (batted OR bowled in inning 1 or 2)"""
        # Get deliveries where player batted (only inning 1 and 2)
        batter_deliveries = self.deliveries_df[(self.deliveries_df['batter'] == player) & 
                                               (self.deliveries_df['inning'].isin([1, 2]))]
        
        # Get deliveries where player bowled (only inning 1 and 2)
        bowler_deliveries = self.deliveries_df[(self.deliveries_df['bowler'] == player) & 
                                               (self.deliveries_df['inning'].isin([1, 2]))]
        
        # Combine both (union of matches where player appeared)
        all_match_ids = set(batter_deliveries['match_id'].unique()) | set(bowler_deliveries['match_id'].unique())
        
        if len(all_match_ids) == 0:
            return 0
        
        # If no filters, return all matches
        if not filters or all(v is None for v in filters.values()):
            return len(all_match_ids)
        
        # Apply filters manually to get filtered matches
        filtered_matches = set()
        for match_id in all_match_ids:
            # Get match metadata
            match_info = self.matches_df[self.matches_df['id'] == match_id]
            if match_info.empty:
                filtered_matches.add(match_id)
                continue
            
            # Check if match passes filters
            if filters.get('seasons') and match_info['year'].iloc[0] not in filters['seasons']:
                continue
            if filters.get('venue') and match_info['venue'].iloc[0] not in filters['venue']:
                continue
            
            filtered_matches.add(match_id)
        
        return len(filtered_matches)
    
    def _apply_cricket_filters(self, deliveries_df: pd.DataFrame, filters: Dict) -> pd.DataFrame:
        """Apply cricket-specific filters like match_phase, bowler_type, match_situation, etc"""
        if not filters:
            return deliveries_df
        
        df = deliveries_df.copy()
        
        # Calculate ball_number if not already present (over*6 + ball)
        if 'ball_number' not in df.columns:
            df['ball_number'] = df['over'] * 6 + df['ball']
        
        # Opposition team filter: filter for matches where player played AGAINST opposition_team
        if filters.get('opposition_team'):
            opp_team = filters['opposition_team']
            df = df.merge(self.matches_df[['id', 'team1', 'team2']], left_on='match_id', right_on='id', how='left')
            
            # For batting stats: opposition is the bowling_team
            # For bowling stats: opposition is the batting_team
            # We'll keep deliveries where: (batting_team played against opposition_team) OR (bowling_team played against opposition_team)
            # This works for both batting and bowling analysis
            
            # Get matches where this team played (either team1 or team2)
            team_matches = df[(df['team1'] == opp_team) | (df['team2'] == opp_team)]
            df = df[df['match_id'].isin(team_matches['match_id'])]
            
            df = df.drop(columns=['id', 'team1', 'team2'], errors='ignore')
        
        # Match phase filter: powerplay (0-6), middle (6-16), death (16+)
        if filters.get('match_phase'):
            phase = filters['match_phase'].lower()
            if phase == 'powerplay':
                # Powerplay is overs 0-6 (balls 0-35)
                df = df[df['over'] <= 5]
            elif phase == 'middle_overs':
                # Middle overs: overs 7-15 (balls 36-89)
                df = df[(df['over'] >= 6) & (df['over'] <= 15)]
            elif phase == 'death_overs':
                # Death overs: overs 16+ (balls 90+)
                df = df[df['over'] >= 16]
            elif phase == 'opening':
                # Opening phase: first 3 overs (balls 0-17)
                df = df[df['over'] <= 2]
            elif phase == 'closing':
                # Closing phase: last 3 overs (overs 17-19)
                df = df[df['over'] >= 17]
        
        # Match situation filter: chasing vs defending
        if filters.get('match_situation'):
            situation = filters['match_situation'].lower()
            df = df.merge(self.matches_df[['id', 'team1']], left_on='match_id', right_on='id', how='left')
            
            if situation == 'chasing':
                # Chasing: batting_team is team2 (batting second, inning == 2)
                df = df[(df['batting_team'] != df['team1']) & (df['inning'] == 2)]
            elif situation == 'defending':
                # Defending: batting_team is team1 (batting first, inning == 1)
                df = df[(df['batting_team'] == df['team1']) & (df['inning'] == 1)]
            elif situation == 'batting_first':
                # Batting first: inning == 1
                df = df[df['inning'] == 1]
            elif situation == 'pressure_chase':
                # Pressure chase: chasing AND (rough estimate based on low runs/overs at start)
                df = df[(df['batting_team'] != df['team1']) & (df['inning'] == 2)]
            elif situation == 'winning_position':
                # Winning position: batting team ahead (difficult without match state - skip for now)
                pass
            
            df = df.drop(columns=['id', 'team1'], errors='ignore')
        
        # Bowler type filter: pace vs spin, left_arm vs right_arm
        # NOTE: This requires bowler classification data which isn't in the current dataset
        if filters.get('bowler_type'):
            # TODO: Add bowler_type classification dataset
            pass
        
        # Batter role filter: opener, middle_order, lower_order, finisher
        # NOTE: This requires batting order data which requires deeper match analysis
        if filters.get('batter_role'):
            # TODO: Add batting order detection
            pass
        
        # VS conditions: vs_pace, vs_spin, vs_off_spin, vs_leg_spin, vs_left_arm, vs_right_arm, vs_left_arm_spin, vs_right_arm_spin
        # And sub-types: right_arm_pace, left_arm_pace, right_arm_off_spin, left_arm_off_spin, right_arm_leg_spin, left_arm_leg_spin
        # Filter deliveries against specific bowling types
        if filters.get('vs_conditions'):
            vs_cond = filters['vs_conditions'].lower()
            # Get list of bowlers matching the condition type
            matching_bowlers = set()
            
            if vs_cond == 'vs_pace':
                pace_bowlers = self._bowler_types.get('pace_bowlers', [])
                matching_bowlers.update(pace_bowlers)
            elif vs_cond == 'vs_spin':
                spin_bowlers = self._bowler_types.get('spin_bowlers', [])
                matching_bowlers.update(spin_bowlers)
            elif vs_cond == 'vs_left_arm_spin':
                # Left arm spinners only (left-armers who are spinners)
                left_arm = set(self._bowler_types.get('left_arm_bowlers', []))
                spin = set(self._bowler_types.get('spin_bowlers', []))
                matching_bowlers.update(left_arm & spin)  # Intersection
            elif vs_cond == 'vs_right_arm_spin':
                # Right arm spinners only
                right_arm = set(self._bowler_types.get('right_arm_bowlers', []))
                spin = set(self._bowler_types.get('spin_bowlers', []))
                matching_bowlers.update(right_arm & spin)  # Intersection
            elif vs_cond == 'vs_off_spin' or vs_cond == 'vs_offspinner' or vs_cond == 'vs_off_spinner':
                off_spin_bowlers = self._bowler_types.get('off_spin_bowlers', [])
                matching_bowlers.update(off_spin_bowlers)
            elif vs_cond == 'vs_leg_spin' or vs_cond == 'vs_legspinner' or vs_cond == 'vs_leg_spinner':
                leg_spin_bowlers = self._bowler_types.get('leg_spin_bowlers', [])
                matching_bowlers.update(leg_spin_bowlers)
            elif vs_cond == 'vs_left_arm':
                left_arm = self._bowler_types.get('left_arm_bowlers', [])
                matching_bowlers.update(left_arm)
            elif vs_cond == 'vs_right_arm':
                right_arm = self._bowler_types.get('right_arm_bowlers', [])
                matching_bowlers.update(right_arm)
            # Sub-types for breakdown
            elif vs_cond == 'right_arm_pace':
                bowlers = self._bowler_types.get('right_arm_pace', [])
                matching_bowlers.update(bowlers)
            elif vs_cond == 'left_arm_pace':
                bowlers = self._bowler_types.get('left_arm_pace', [])
                matching_bowlers.update(bowlers)
            elif vs_cond == 'right_arm_off_spin':
                bowlers = self._bowler_types.get('right_arm_off_spin', [])
                matching_bowlers.update(bowlers)
            elif vs_cond == 'left_arm_off_spin':
                bowlers = self._bowler_types.get('left_arm_off_spin', [])
                matching_bowlers.update(bowlers)
            elif vs_cond == 'right_arm_leg_spin':
                bowlers = self._bowler_types.get('right_arm_leg_spin', [])
                matching_bowlers.update(bowlers)
            elif vs_cond == 'left_arm_leg_spin':
                bowlers = self._bowler_types.get('left_arm_leg_spin', [])
                matching_bowlers.update(bowlers)
            
            # Filter deliveries to only those bowled by matching bowlers
            if matching_bowlers:
                df = df[df['bowler'].isin(matching_bowlers)].copy()
        
        # ===== NEW FILTERS =====
        
        # Ground/Venue filter
        if filters.get('ground'):
            ground = filters['ground']
            df = df.merge(self.matches_df[['id', 'venue']], left_on='match_id', right_on='id', how='left')
            df = df[df['venue'] == ground]
            df = df.drop(columns=['id', 'venue'], errors='ignore')
        
        # Inning filter (1 = batting first, 2 = batting second/chasing)
        if filters.get('innings_order'):
            inning = filters['innings_order']
            df = df[df['inning'] == inning]
        
        # Handedness filter (filter deliveries facing/bowled by left/right handers)
        if filters.get('handedness'):
            handedness = filters['handedness']
            if handedness == 'left_handed':
                # Filter for deliveries against left-handed batters
                left_handers = self._batter_handedness.get('left_hand_batters', [])
                df = df[df['batter'].isin(left_handers)]
            elif handedness == 'right_handed':
                # Filter for deliveries against right-handed batters
                right_handers = self._batter_handedness.get('right_hand_batters', [])
                df = df[df['batter'].isin(right_handers)]
        
        # Match type filter (home/away)
        if filters.get('match_type'):
            match_type = filters['match_type']
            df = df.merge(self.matches_df[['id', 'team1', 'team2']], left_on='match_id', right_on='id', how='left')
            
            # Determine if this is home or away for the relevant team
            # For batting stats: check if batting_team is home (team1)
            # For bowling stats: check if bowling_team is home (team1)
            if match_type == 'home':
                # Filter for matches where team1 is batting/bowling
                df = df[((df['batting_team'] == df['team1']) | (df['bowling_team'] == df['team1']))]
            elif match_type == 'away':
                # Filter for matches where team2 is batting/bowling
                df = df[((df['batting_team'] == df['team2']) | (df['bowling_team'] == df['team2']))]
            
            df = df.drop(columns=['id', 'team1', 'team2'], errors='ignore')
        
        # Drop temporary columns
        df = df.drop(columns=['ball_number'], errors='ignore')
        
        return df
    
    def _get_batting_stats(self, player: str, filters: Dict = None, total_matches: int = None) -> Dict:
        """Calculate comprehensive batting statistics"""
        player_deliveries = self.deliveries_df[self.deliveries_df['batter'] == player].copy()
        
        # Apply basic filters (season, venue) first
        if filters:
            if filters.get('seasons'):
                player_deliveries = player_deliveries.merge(
                    self.matches_df[['id', 'year']], 
                    left_on='match_id', right_on='id', how='inner'
                )
                player_deliveries = player_deliveries[player_deliveries['year'].isin(filters['seasons'])]
                player_deliveries = player_deliveries.drop(columns=['id', 'year'])
            
            if filters.get('venue'):
                player_deliveries = player_deliveries.merge(
                    self.matches_df[['id', 'venue']], 
                    left_on='match_id', right_on='id', how='inner'
                )
                player_deliveries = player_deliveries[player_deliveries['venue'].isin(filters['venue'])]
                player_deliveries = player_deliveries.drop(columns=['id', 'venue'])
        
        # Apply cricket-specific filters (match_phase, match_situation, vs_conditions, etc)
        player_deliveries = self._apply_cricket_filters(player_deliveries, filters)
        
        if len(player_deliveries) == 0:
            return {}
        
        runs = player_deliveries['batsman_runs'].sum()
        balls = len(player_deliveries)
        
        # Count unique innings where player batted (only inning 1 and 2, exclude super overs)
        valid_innings = player_deliveries[player_deliveries['inning'].isin([1, 2])][['match_id', 'inning']].drop_duplicates()
        innings = valid_innings.shape[0]
        
        # Use provided total_matches or calculate from batting data
        matches = total_matches if total_matches is not None else len(player_deliveries['match_id'].unique())
        
        # Calculate scores per match
        match_scores = player_deliveries.groupby('match_id')['batsman_runs'].sum()
        highest_score = int(match_scores.max()) if len(match_scores) > 0 else 0
        centuries = len(match_scores[match_scores >= 100])
        fifties = len(match_scores[(match_scores >= 50) & (match_scores < 100)])
        
        # Count fours (batsman_runs == 4)
        fours = len(player_deliveries[player_deliveries['batsman_runs'] == 4])
        sixes = len(player_deliveries[player_deliveries['batsman_runs'] == 6])
        
        # FIX #1: Count dismissals (innings where player got out) for accurate batting average
        dismissals = player_deliveries[player_deliveries['is_wicket'] == 1][['match_id', 'inning']].drop_duplicates().shape[0]
        
        # FIX #2 & #3: Valid deliveries exclude wides and no balls for strike rate and dot balls
        valid_deliveries = player_deliveries[
            (player_deliveries['extras_type'] != 'wides') &
            (player_deliveries['extras_type'] != 'noballs')
        ]
        dot_balls = len(valid_deliveries[valid_deliveries['batsman_runs'] == 0])
        valid_count = len(valid_deliveries)
        dot_ball_percentage = round((dot_balls / valid_count * 100), 2) if valid_count > 0 else 0
        
        return {
            'matches': matches,
            'innings': innings,
            'runs': int(runs),
            'balls': balls,
            'average': round(runs / dismissals, 2) if dismissals > 0 else 0,
            'strike_rate': round((runs / valid_count * 100), 2) if valid_count > 0 else 0,
            'highest_score': highest_score,
            'centuries': centuries,
            'fifties': fifties,
            'fours': fours,
            'sixes': sixes,
            'dot_balls': dot_balls,
            'dot_ball_percentage': dot_ball_percentage
        }
    
    def _get_bowling_stats(self, player: str, filters: Dict = None, total_matches: int = None) -> Dict:
        """Calculate comprehensive bowling statistics"""
        player_deliveries = self.deliveries_df[self.deliveries_df['bowler'] == player].copy()
        
        # CRITICAL: Exclude super overs (innings 3 and above) - Cricinfo only counts regular innings
        player_deliveries = player_deliveries[player_deliveries['inning'].isin([1, 2])]
        
        # Apply basic filters (season, venue) first
        if filters:
            if filters.get('seasons'):
                player_deliveries = player_deliveries.merge(
                    self.matches_df[['id', 'year']], 
                    left_on='match_id', right_on='id', how='inner'
                )
                player_deliveries = player_deliveries[player_deliveries['year'].isin(filters['seasons'])]
                player_deliveries = player_deliveries.drop(columns=['id', 'year'])
            
            if filters.get('venue'):
                player_deliveries = player_deliveries.merge(
                    self.matches_df[['id', 'venue']], 
                    left_on='match_id', right_on='id', how='inner'
                )
                player_deliveries = player_deliveries[player_deliveries['venue'].isin(filters['venue'])]
                player_deliveries = player_deliveries.drop(columns=['id', 'venue'])
        
        # Apply cricket-specific filters (match_phase, match_situation, vs_conditions, etc)
        player_deliveries = self._apply_cricket_filters(player_deliveries, filters)
        
        if len(player_deliveries) == 0:
            return {}
        
        # Count wickets - EXCLUDE run outs (not credited to bowler in cricket rules)
        # Bowler gets credit for: caught, bowled, caught & bowled, stumped, hit wicket, LBW
        # Does NOT get credit for: run out, retired, obstructing field, etc.
        wickets = len(player_deliveries[
            (player_deliveries['is_wicket'] == 1) & 
            (player_deliveries['dismissal_kind'] != 'run out')
        ])
        
        # FIX #4: Bowler runs conceded = exclude leg byes and byes (cricket rule: only credited for runs off bat, wides, no balls)
        runs_conceded = player_deliveries[
            ~player_deliveries['extras_type'].isin(['legbyes', 'byes'])
        ]['total_runs'].sum()
        
        # CRITICAL: Count only valid deliveries (exclude wides and no balls) - Cricinfo counts 6 balls per over
        valid_deliveries_count = player_deliveries[
            (player_deliveries['extras_type'] != 'wides') &
            (player_deliveries['extras_type'] != 'noballs')
        ]
        balls = len(valid_deliveries_count)
        
        # Count unique innings where player bowled (only inning 1 and 2, exclude super overs)
        valid_innings = player_deliveries[player_deliveries['inning'].isin([1, 2])][['match_id', 'inning']].drop_duplicates()
        innings = valid_innings.shape[0]
        
        # Use provided total_matches or calculate from bowling data
        matches = total_matches if total_matches is not None else len(player_deliveries['match_id'].unique())
        
        # FIX #5: Dot balls - exclude wides and no balls (only valid deliveries with 0 runs)
        valid_deliveries_bowling = player_deliveries[
            (player_deliveries['extras_type'] != 'wides') &
            (player_deliveries['extras_type'] != 'noballs')
        ]
        dot_balls = len(valid_deliveries_bowling[valid_deliveries_bowling['total_runs'] == 0])
        valid_balls_count = len(valid_deliveries_bowling)
        dot_ball_percentage = round((dot_balls / valid_balls_count * 100), 2) if valid_balls_count > 0 else 0
        
        # FIX #6: Best figures - use correct runs (exclude leg byes and byes)
        best_figures_data = []
        for match_id in player_deliveries['match_id'].unique():
            match_data = player_deliveries[player_deliveries['match_id'] == match_id]
            wickets_in_match = match_data['is_wicket'].sum()
            runs_in_match = match_data[
                ~match_data['extras_type'].isin(['legbyes', 'byes'])
            ]['total_runs'].sum()
            best_figures_data.append({
                'match_id': match_id,
                'wickets': wickets_in_match,
                'runs': runs_in_match
            })
        
        if best_figures_data:
            # Find best figures: max wickets, then min runs (e.g., 5/10 is better than 5/29)
            best_match = max(best_figures_data, key=lambda x: (x['wickets'], -x['runs']), default={'wickets': 0, 'runs': 0})
            best_figures = f"{int(best_match['wickets'])}/{int(best_match['runs'])}"
        else:
            best_figures = "0/0"
        
        # Count 4-wicket hauls
        match_wickets = player_deliveries.groupby('match_id')['is_wicket'].sum()
        four_wickets = len(match_wickets[match_wickets >= 4])
        
        # Count maiden overs (6 balls with 0 runs)
        over_runs = player_deliveries.groupby(['match_id', 'inning', 'over'])['total_runs'].sum()
        maiden_overs = len(over_runs[over_runs == 0])
        
        return {
            'matches': matches,
            'innings': innings,
            'wickets': int(wickets),
            'runs_conceded': int(runs_conceded),
            'balls': balls,
            'overs': round(balls / 6, 1),
            'economy': round((runs_conceded / (balls / 6)), 2) if balls > 0 else 0,
            'average': round(runs_conceded / wickets, 2) if wickets > 0 else 0,
            'best_figures': best_figures,
            'four_wickets': four_wickets,
            'maiden_overs': maiden_overs,
            'dot_balls': dot_balls,
            'dot_ball_percentage': dot_ball_percentage
        }
    
    def _get_highest_score(self, player: str) -> int:
        """Get highest score by a player"""
        player_deliveries = self.deliveries_df[self.deliveries_df['batter'] == player]
        match_scores = player_deliveries.groupby('match_id')['batsman_runs'].sum()
        return match_scores.max() if len(match_scores) > 0 else 0
    
    def get_team_stats(self, team: str, filters: Dict = None) -> Dict:
        """Get team statistics with optional filters"""
        # Try to find the team first
        found_team = self.find_team(team)
        if not found_team:
            return {'error': f'Team {team} not found'}
        
        team_matches = self.matches_df[
            (self.matches_df['team1'] == found_team) | (self.matches_df['team2'] == found_team)
        ].copy()
        
        # Apply filters if provided
        if filters:
            if filters.get('seasons'):
                team_matches = team_matches[team_matches['year'].isin(filters['seasons'])]
            
            if filters.get('venue'):
                venues = filters['venue'] if isinstance(filters['venue'], list) else [filters['venue']]
                team_matches = team_matches[team_matches['venue'].isin(venues)]
            
            # Home/Away filter
            if filters.get('home_away'):
                if filters['home_away'] == 'home':
                    team_matches = team_matches[team_matches['team1'] == found_team]
                elif filters['home_away'] == 'away':
                    team_matches = team_matches[team_matches['team2'] == found_team]
            
            # Innings order filter - filter deliveries and get match_ids
            if filters.get('innings_order'):
                # Get deliveries for this team's matches with specified inning order
                team_match_ids = set(team_matches['id'].unique())
                team_deliveries = self.deliveries_df[
                    (self.deliveries_df['match_id'].isin(team_match_ids)) &
                    (self.deliveries_df['inning'] == filters['innings_order'])
                ]
                if len(team_deliveries) > 0:
                    team_matches = team_matches[team_matches['id'].isin(team_deliveries['match_id'].unique())]
                else:
                    team_matches = team_matches.iloc[0:0]  # Empty dataframe
        
        wins = len(team_matches[team_matches['winner'] == found_team])
        total_matches = len(team_matches)
        
        return {
            'team': found_team,
            'matches': total_matches,
            'wins': wins,
            'win_percentage': round((wins / total_matches * 100), 2) if total_matches > 0 else 0,
            'win_rate': round((wins / total_matches), 2) if total_matches > 0 else 0
        }
    
    def get_venue_stats(self, venue: str) -> Dict:
        """Get statistics for a specific venue"""
        venue_matches = self.matches_df[self.matches_df['venue'] == venue]
        
        return {
            'venue': venue,
            'total_matches': len(venue_matches),
            'avg_runs_team1': round(venue_matches[venue_matches['team1'] == venue_matches['team1']].shape[0] / len(venue_matches) * 100, 2) if len(venue_matches) > 0 else 0,
            'seasons': venue_matches['season'].nunique()
        }
    
    def get_player_form(self, player: str, last_n_matches: int = 10) -> Dict:
        """Get recent form of a player"""
        player_deliveries = self.deliveries_df[self.deliveries_df['batter'] == player]
        # Group by unique innings (match_id + inning) to get scores per innings
        recent_innings = player_deliveries.groupby(['match_id', 'inning'])['batsman_runs'].sum().tail(last_n_matches)
        
        return {
            'player': player,
            'recent_runs': recent_innings.to_dict(),
            'avg_recent': round(recent_innings.mean(), 2),
            'last_match_runs': int(recent_innings.iloc[-1]) if len(recent_innings) > 0 else 0
        }
    
    def get_top_performers(self, category: str, n: int = 10) -> List[Dict]:
        """Get top performers by category"""
        if category == 'batting':
            top_batsmen = self.deliveries_df.groupby('batter')['batsman_runs'].sum().nlargest(n)
            return [{'player': player, 'runs': int(runs)} for player, runs in top_batsmen.items()]
        
        elif category == 'bowling':
            top_bowlers = self.deliveries_df[self.deliveries_df['is_wicket'] == 1].groupby('bowler').size().nlargest(n)
            return [{'player': player, 'wickets': int(wickets)} for player, wickets in top_bowlers.items()]
        
        return []
    
    def get_player_head_to_head(self, player1: str, player2: str, filters: Dict = None) -> Dict:
        """Get head-to-head statistics between two players (batter vs bowler)"""
        try:
            # Get deliveries where player1 batted and player2 bowled
            h2h_deliveries = self.deliveries_df[
                (self.deliveries_df['batter'] == player1) & 
                (self.deliveries_df['bowler'] == player2)
            ].copy()
            
            # Apply basic filters (seasons, venue) first
            if filters:
                if filters.get('seasons'):
                    h2h_deliveries = h2h_deliveries.merge(
                        self.matches_df[['id', 'year']], 
                        left_on='match_id', right_on='id', how='inner'
                    )
                    h2h_deliveries = h2h_deliveries[h2h_deliveries['year'].isin(filters['seasons'])]
                    h2h_deliveries = h2h_deliveries.drop(columns=['id', 'year'])
                
                if filters.get('venue'):
                    h2h_deliveries = h2h_deliveries.merge(
                        self.matches_df[['id', 'venue']], 
                        left_on='match_id', right_on='id', how='inner'
                    )
                    h2h_deliveries = h2h_deliveries[h2h_deliveries['venue'].isin(filters['venue'])]
                    h2h_deliveries = h2h_deliveries.drop(columns=['id', 'venue'])
                
                # Apply cricket-specific filters (match_phase, match_situation, etc)
                h2h_deliveries = self._apply_cricket_filters(h2h_deliveries, filters)
            
            if len(h2h_deliveries) == 0:
                return {
                    'message': f'{player1} and {player2} have not faced each other',
                    'error': True
                }
            
            # Calculate stats
            deliveries = len(h2h_deliveries)
            runs = h2h_deliveries['batsman_runs'].sum()
            strike_rate = (runs / deliveries * 100) if deliveries > 0 else 0
            dot_balls = len(h2h_deliveries[h2h_deliveries['batsman_runs'] == 0])
            
            return {
                'deliveries': deliveries,
                'runs': int(runs),
                'strike_rate': round(strike_rate, 2),
                'dot_balls': dot_balls,
                'summary': f'{player1} has faced {deliveries} balls from {player2}, scoring {int(runs)} runs at a strike rate of {strike_rate:.1f}'
            }
        except Exception as e:
            return {'error': True, 'message': str(e)}
    
    def get_bowling_subtype_breakdown(self, player: str, vs_condition: str, filters: Dict = None) -> Dict:
        """Get batting stats breakdown by bowling sub-types
        
        For vs_spin, returns: vs_right_arm_off_spin, vs_left_arm_off_spin, vs_right_arm_leg_spin, vs_left_arm_leg_spin
        For vs_pace, returns: vs_right_arm_pace, vs_left_arm_pace
        """
        base_filters = filters.copy() if filters else {}
        breakdown = {}
        
        # Determine which sub-types to calculate
        if vs_condition == 'vs_spin':
            sub_types = [
                ('vs_right_arm_off_spin', 'right_arm_off_spin'),
                ('vs_left_arm_off_spin', 'left_arm_off_spin'),
                ('vs_right_arm_leg_spin', 'right_arm_leg_spin'),
                ('vs_left_arm_leg_spin', 'left_arm_leg_spin'),
            ]
        elif vs_condition == 'vs_pace':
            sub_types = [
                ('vs_right_arm_pace', 'right_arm_pace'),
                ('vs_left_arm_pace', 'left_arm_pace'),
            ]
        else:
            return breakdown
        
        # Calculate stats for each sub-type
        for display_name, bowler_type_key in sub_types:
            sub_filters = base_filters.copy()
            sub_filters['vs_conditions'] = bowler_type_key
            stats = self._get_batting_stats(player, sub_filters)
            if stats and stats.get('balls', 0) > 0:  # Only include if there are balls faced
                breakdown[display_name] = stats
        
        return breakdown

    def get_bowling_handedness_breakdown(self, player: str, filters: Dict = None) -> Dict:
        """Get bowling stats breakdown by batter handedness (RHB vs LHB)"""
        base_filters = filters.copy() if filters else {}
        breakdown = {}
        
        right_hand_batters = set(self._batter_handedness.get('right_hand_batters', []))
        left_hand_batters = set(self._batter_handedness.get('left_hand_batters', []))
        
        # Get bowler's deliveries
        player_deliveries = self.deliveries_df[self.deliveries_df['bowler'] == player].copy()
        
        # Apply basic filters first
        if base_filters:
            if base_filters.get('seasons'):
                player_deliveries = player_deliveries.merge(
                    self.matches_df[['id', 'year']], 
                    left_on='match_id', right_on='id', how='inner'
                )
                player_deliveries = player_deliveries[player_deliveries['year'].isin(base_filters['seasons'])]
                player_deliveries = player_deliveries.drop(columns=['id', 'year'])
        
        # Calculate stats vs RHB
        rhb_deliveries = player_deliveries[player_deliveries['batter'].isin(right_hand_batters)].copy()
        if len(rhb_deliveries) > 0:
            breakdown['vs_RHB'] = self._get_bowling_stats_from_deliveries(rhb_deliveries, player)
        
        # Calculate stats vs LHB
        lhb_deliveries = player_deliveries[player_deliveries['batter'].isin(left_hand_batters)].copy()
        if len(lhb_deliveries) > 0:
            breakdown['vs_LHB'] = self._get_bowling_stats_from_deliveries(lhb_deliveries, player)
        
        return breakdown
    
    def _get_bowling_stats_from_deliveries(self, deliveries_df: pd.DataFrame, player: str) -> Dict:
        """Calculate bowling stats from a pre-filtered deliveries dataframe"""
        if len(deliveries_df) == 0:
            return {}
        
        # Count wickets - is_wicket column already filters for valid dismissals in the source data
        # (includes: caught, bowled, caught & bowled, stumped, hit wicket, LBW)
        # (excludes: run out, retired, obstructing field, etc.)
        wickets = deliveries_df['is_wicket'].sum()
        
        runs_conceded = deliveries_df[
            ~deliveries_df['extras_type'].isin(['legbyes', 'byes'])
        ]['total_runs'].sum()
        balls = len(deliveries_df)
        
        # Valid deliveries for dot balls and economy
        valid_deliveries = deliveries_df[
            (deliveries_df['extras_type'] != 'wides') &
            (deliveries_df['extras_type'] != 'noballs')
        ]
        dot_balls = len(valid_deliveries[valid_deliveries['total_runs'] == 0])
        valid_count = len(valid_deliveries)
        
        return {
            'wickets': int(wickets),
            'runs_conceded': int(runs_conceded),
            'balls': balls,
            'overs': round(balls / 6, 1),
            'economy': round((runs_conceded / (balls / 6)), 2) if balls > 0 else 0,
            'average': round(runs_conceded / wickets, 2) if wickets > 0 else 0,
            'strike_rate': round((wickets / balls * 100), 2) if balls > 0 else 0,
        }

    def get_primary_skill(self, player: str) -> str:
        """Determine a player's primary skill (batter/bowler) based on participation
        
        Returns: 'batter', 'bowler', or 'all-rounder'
        """
        found_player = self.find_player(player)
        if not found_player:
            return None
        
        batting_deliveries = len(self.deliveries_df[self.deliveries_df['batter'] == found_player])
        bowling_deliveries = len(self.deliveries_df[self.deliveries_df['bowler'] == found_player])
        
        # If no participation in either, can't determine
        if batting_deliveries == 0 and bowling_deliveries == 0:
            return None
        
        # If only one, that's the skill
        if batting_deliveries > 0 and bowling_deliveries == 0:
            return 'batter'
        if bowling_deliveries > 0 and batting_deliveries == 0:
            return 'bowler'
        
        # Both present - determine primary based on deliveries ratio
        # If one has significantly more activity, it's primary
        ratio = batting_deliveries / bowling_deliveries
        
        if ratio > 2:  # At least 2x more batting
            return 'batter'
        elif ratio < 0.5:  # At least 2x more bowling (bowling > 2x batting)
            return 'bowler'
        else:
            return 'all-rounder'

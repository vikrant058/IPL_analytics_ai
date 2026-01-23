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
    
    def _load_aliases(self) -> Dict:
        """Load player and team aliases from JSON file"""
        try:
            alias_file = os.path.join(os.path.dirname(__file__), 'player_aliases.json')
            with open(alias_file, 'r') as f:
                data = json.load(f)
                return data.get('aliases', {})
        except FileNotFoundError:
            return {}
    
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
    
    def _get_batting_stats(self, player: str, filters: Dict = None, total_matches: int = None) -> Dict:
        """Calculate comprehensive batting statistics"""
        player_deliveries = self.deliveries_df[self.deliveries_df['batter'] == player].copy()
        
        # Apply filters manually without merging to avoid data duplication
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
        
        if len(player_deliveries) == 0:
            return {}
        
        runs = player_deliveries['batsman_runs'].sum()
        balls = len(player_deliveries)
        
        # Count unique innings where player batted (only inning 1 and 2, exclude super overs)
        valid_innings = player_deliveries[player_deliveries['inning'].isin([1, 2])][['match_id', 'inning']].drop_duplicates()
        innings = valid_innings.shape[0]
        
        # Use provided total_matches or calculate from batting data
        matches = total_matches if total_matches is not None else len(player_deliveries['match_id'].unique())
        
        # Count dot balls (balls faced with 0 runs)
        dot_balls = len(player_deliveries[player_deliveries['batsman_runs'] == 0])
        dot_ball_percentage = round((dot_balls / balls * 100), 2) if balls > 0 else 0
        
        # Calculate scores per match
        match_scores = player_deliveries.groupby('match_id')['batsman_runs'].sum()
        highest_score = int(match_scores.max()) if len(match_scores) > 0 else 0
        centuries = len(match_scores[match_scores >= 100])
        fifties = len(match_scores[(match_scores >= 50) & (match_scores < 100)])
        
        # Count fours (batsman_runs == 4)
        fours = len(player_deliveries[player_deliveries['batsman_runs'] == 4])
        sixes = len(player_deliveries[player_deliveries['batsman_runs'] == 6])
        
        return {
            'matches': matches,
            'innings': innings,
            'runs': int(runs),
            'balls': balls,
            'average': round(runs / innings, 2) if innings > 0 else 0,
            'strike_rate': round((runs / balls * 100), 2) if balls > 0 else 0,
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
        
        # Apply filters manually without merging to avoid data duplication
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
        
        if len(player_deliveries) == 0:
            return {}
        
        wickets = player_deliveries['is_wicket'].sum()
        runs_conceded = player_deliveries['total_runs'].sum()
        balls = len(player_deliveries)
        
        # Count unique innings where player bowled (only inning 1 and 2, exclude super overs)
        valid_innings = player_deliveries[player_deliveries['inning'].isin([1, 2])][['match_id', 'inning']].drop_duplicates()
        innings = valid_innings.shape[0]
        
        # Use provided total_matches or calculate from bowling data
        matches = total_matches if total_matches is not None else len(player_deliveries['match_id'].unique())
        
        # Count dot balls (balls with 0 runs conceded)
        dot_balls = len(player_deliveries[player_deliveries['total_runs'] == 0])
        dot_ball_percentage = round((dot_balls / balls * 100), 2) if balls > 0 else 0
        
        # Best figures (wickets/runs in a match)
        match_stats = player_deliveries.groupby('match_id').agg({
            'is_wicket': 'sum',
            'total_runs': 'sum'
        }).reset_index()
        
        if len(match_stats) > 0:
            # Find match with most wickets
            best_match_idx = match_stats['is_wicket'].idxmax()
            best_wickets = int(match_stats.loc[best_match_idx, 'is_wicket'])
            best_runs = int(match_stats.loc[best_match_idx, 'total_runs'])
            best_figures = f"{best_wickets}/{best_runs}"
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
            
            # Apply filters if provided
            if filters and h2h_deliveries.shape[0] > 0:
                if filters.get('seasons'):
                    h2h_deliveries = h2h_deliveries.merge(
                        self.matches_df[['id', 'year']], 
                        left_on='match_id', right_on='id', how='inner'
                    )
                    h2h_deliveries = h2h_deliveries[h2h_deliveries['year'].isin(filters['seasons'])]
                    h2h_deliveries = h2h_deliveries.drop(columns=['id', 'year'])
            
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
                'summary': f'{player1} has faced {deliveries} balls from {player2}, scoring {int(runs)} runs at a strike rate of {strike_rate:.1f}%'
            }
        except Exception as e:
            return {'error': True, 'message': str(e)}
    
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

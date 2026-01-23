import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from data_loader import IPLDataLoader
from stats_engine import StatsEngine
import warnings
warnings.filterwarnings('ignore')

class AIEngine:
    """AI-powered cricket analytics and predictions"""
    
    def __init__(self, matches_df: pd.DataFrame, deliveries_df: pd.DataFrame):
        self.matches_df = matches_df
        self.deliveries_df = deliveries_df
        self.stats_engine = StatsEngine(matches_df, deliveries_df)
        self.models = {}
        self._prepare_features()
    
    def _prepare_features(self):
        """Prepare feature engineering for ML models"""
        self.team_performance = self._calculate_team_features()
        self.player_performance = self._calculate_player_features()
    
    def _calculate_team_features(self) -> pd.DataFrame:
        """Calculate team-level features"""
        teams = pd.concat([
            self.matches_df['team1'],
            self.matches_df['team2']
        ]).unique()
        
        team_features = []
        for team in teams:
            team_matches = self.matches_df[
                (self.matches_df['team1'] == team) | (self.matches_df['team2'] == team)
            ]
            
            wins = len(self.matches_df[self.matches_df['winner'] == team])
            total = len(team_matches)
            
            team_features.append({
                'team': team,
                'total_matches': total,
                'wins': wins,
                'win_rate': wins / total if total > 0 else 0,
                'avg_result_margin': team_matches['result_margin'].mean()
            })
        
        return pd.DataFrame(team_features)
    
    def _calculate_player_features(self) -> Dict:
        """Calculate player-level features (lazy-loaded)"""
        # Initialize as empty dict - features will be calculated on-demand
        return {}
    
    def predict_match_winner(self, team1: str, team2: str) -> Dict:
        """Predict match winner between two teams"""
        team1_stats = self.team_performance[self.team_performance['team'] == team1]
        team2_stats = self.team_performance[self.team_performance['team'] == team2]
        
        if len(team1_stats) == 0 or len(team2_stats) == 0:
            return {
                'team1': team1,
                'team2': team2,
                'error': 'Team statistics not found'
            }
        
        team1_wr = team1_stats['win_rate'].values[0]
        team2_wr = team2_stats['win_rate'].values[0]
        
        total_wr = team1_wr + team2_wr
        confidence1 = team1_wr / total_wr if total_wr > 0 else 0.5
        confidence2 = team2_wr / total_wr if total_wr > 0 else 0.5
        
        predicted_winner = team1 if confidence1 > confidence2 else team2
        
        return {
            'team1': team1,
            'team2': team2,
            'predicted_winner': predicted_winner,
            'confidence': round(max(confidence1, confidence2), 3),
            'team1_win_probability': round(confidence1, 3),
            'team2_win_probability': round(confidence2, 3),
            'key_factors': [
                f'{team1} win rate: {round(team1_wr*100, 1)}%',
                f'{team2} win rate: {round(team2_wr*100, 1)}%'
            ]
        }
    
    def predict_player_performance(self, player: str, match_type: str = 'batting') -> Dict:
        """Predict player performance"""
        if player not in self.player_performance:
            return {'error': f'Player {player} not found'}
        
        stats = self.player_performance[player]
        
        if match_type == 'batting' and stats['batting']:
            avg_runs = stats['batting'].get('average', 0)
            sr = stats['batting'].get('strike_rate', 0)
            predicted_runs = int(avg_runs * 1.1)  # Simple prediction: 10% above average
            
            return {
                'player': player,
                'type': 'batting',
                'predicted_runs': predicted_runs,
                'historical_average': stats['batting'].get('average', 0),
                'strike_rate': sr,
                'confidence': 0.65
            }
        
        elif match_type == 'bowling' and stats['bowling']:
            avg_wickets = stats['bowling'].get('matches', 0) / len(
                self.deliveries_df[self.deliveries_df['bowler'] == player]['match_id'].unique()
            ) if len(self.deliveries_df[self.deliveries_df['bowler'] == player]) > 0 else 0
            
            return {
                'player': player,
                'type': 'bowling',
                'predicted_wickets': max(0, int(avg_wickets)),
                'economy': stats['bowling'].get('economy', 0),
                'confidence': 0.60
            }
        
        return {'error': 'No statistics found for player'}
    
    def get_trend_analysis(self, team: str, years: int = 5) -> Dict:
        """Analyze team performance trends"""
        team_matches = self.matches_df[
            (self.matches_df['team1'] == team) | (self.matches_df['team2'] == team)
        ].sort_values('date')
        
        if len(team_matches) == 0:
            return {'error': f'No matches found for {team}'}
        
        recent_matches = team_matches.tail(years * 15)  # ~15 matches per season
        wins_by_year = {}
        
        for year in recent_matches['year'].unique():
            year_matches = recent_matches[recent_matches['year'] == year]
            wins = len(self.matches_df[
                (self.matches_df['year'] == year) & (self.matches_df['winner'] == team)
            ])
            wins_by_year[int(year)] = wins
        
        return {
            'team': team,
            'trend': wins_by_year,
            'current_form': 'improving' if len(wins_by_year) >= 2 and list(wins_by_year.values())[-1] > list(wins_by_year.values())[-2] else 'declining'
        }
    
    def get_head_to_head(self, team1: str, team2: str) -> Dict:
        """Get head-to-head statistics between two teams"""
        matches = self.matches_df[
            ((self.matches_df['team1'] == team1) & (self.matches_df['team2'] == team2)) |
            ((self.matches_df['team1'] == team2) & (self.matches_df['team2'] == team1))
        ]
        
        team1_wins = len(matches[matches['winner'] == team1])
        team2_wins = len(matches[matches['winner'] == team2])
        
        return {
            'type': 'team',
            'team1': team1,
            'team2': team2,
            'total_matches': len(matches),
            'team1_wins': team1_wins,
            'team2_wins': team2_wins,
            'team1_win_rate': round(team1_wins / len(matches) * 100, 1) if len(matches) > 0 else 0
        }
    
    def get_player_head_to_head(self, player1: str, player2: str, match_type: str = 'auto') -> Dict:
        """
        Get head-to-head statistics between two players
        
        Args:
            player1: First player name
            player2: Second player name
            match_type: 'batter_vs_bowler', 'batter_vs_batter', 'bowler_vs_bowler', or 'auto'
        
        Returns:
            Dictionary with comparison stats
        """
        # Use fuzzy matching to find actual player names
        found_player1 = self.stats_engine.find_player(player1)
        found_player2 = self.stats_engine.find_player(player2)
        
        if not found_player1 or not found_player2:
            return {'error': f'Could not find players: {player1}, {player2}'}
        
        player1 = found_player1
        player2 = found_player2
        
        # Determine player types using primary skill detection
        p1_skill = self.stats_engine.get_primary_skill(player1)
        p2_skill = self.stats_engine.get_primary_skill(player2)
        
        # Auto-detect match type if not specified
        if match_type == 'auto':
            # Both are batters or all-rounders with batting focus
            if p1_skill in ['batter', 'all-rounder'] and p2_skill in ['batter', 'all-rounder']:
                match_type = 'batter_vs_batter'
            # Both are bowlers
            elif p1_skill == 'bowler' and p2_skill == 'bowler':
                match_type = 'bowler_vs_bowler'
            # One is batter, one is bowler
            elif p1_skill in ['batter', 'all-rounder'] and p2_skill == 'bowler':
                match_type = 'batter_vs_bowler'
            elif p1_skill == 'bowler' and p2_skill in ['batter', 'all-rounder']:
                match_type = 'batter_vs_bowler'
                player1, player2 = player2, player1  # Swap to keep batter first
            else:
                return {'error': f'Could not determine compatible match type for {player1} and {player2}'}
        
        if match_type == 'batter_vs_bowler':
            return self._batter_vs_bowler(player1, player2)
        elif match_type == 'batter_vs_batter':
            return self._batter_vs_batter(player1, player2)
        elif match_type == 'bowler_vs_bowler':
            return self._bowler_vs_bowler(player1, player2)
        else:
            return {'error': 'Invalid match_type. Use: batter_vs_bowler, batter_vs_batter, bowler_vs_bowler'}
    
    def _batter_vs_bowler(self, batter: str, bowler: str) -> Dict:
        """Compare batter vs bowler head-to-head"""
        # Get deliveries where batter faced this bowler
        head_to_head_deliveries = self.deliveries_df[
            (self.deliveries_df['batter'] == batter) & 
            (self.deliveries_df['bowler'] == bowler)
        ]
        
        if len(head_to_head_deliveries) == 0:
            return {
                'type': 'batter_vs_bowler',
                'batter': batter,
                'bowler': bowler,
                'message': f'{batter} has not faced {bowler}'
            }
        
        # Batter stats against this bowler
        batter_runs = head_to_head_deliveries['batsman_runs'].sum()
        batter_balls = len(head_to_head_deliveries)
        batter_dismissals = len(head_to_head_deliveries[head_to_head_deliveries['is_wicket'] == 1])
        
        # Overall batter stats
        overall_batter_stats = self.stats_engine.get_player_stats(batter)
        
        # Overall bowler stats
        overall_bowler_stats = self.stats_engine.get_player_stats(bowler)
        
        return {
            'type': 'batter_vs_bowler',
            'batter': batter,
            'bowler': bowler,
            'deliveries_faced': batter_balls,
            'batter': {
                'player': batter,
                'runs_vs_bowler': int(batter_runs),
                'balls_vs_bowler': batter_balls,
                'sr_vs_bowler': round((batter_runs / batter_balls * 100), 2) if batter_balls > 0 else 0,
                'dismissals_vs_bowler': batter_dismissals,
                'overall_average': overall_batter_stats['batting'].get('average', 0),
                'overall_sr': overall_batter_stats['batting'].get('strike_rate', 0)
            },
            'bowler': {
                'player': bowler,
                'runs_conceded_to_batter': int(batter_runs),
                'balls_bowled_to_batter': batter_balls,
                'economy_vs_batter': round((batter_runs / (batter_balls / 6)), 2) if batter_balls > 0 else 0,
                'wickets_vs_batter': batter_dismissals,
                'overall_economy': overall_bowler_stats['bowling'].get('economy', 0),
                'overall_strike_rate': round(overall_bowler_stats['bowling'].get('balls', 1) / max(overall_bowler_stats['bowling'].get('wickets', 1), 1), 1)
            },
            'analysis': {
                'batter_advantage': 'Yes' if batter_runs / max(batter_balls, 1) * 100 > overall_batter_stats['batting'].get('strike_rate', 0) else 'No',
                'bowler_advantage': 'Yes' if (batter_runs / (batter_balls / 6)) > overall_bowler_stats['bowling'].get('economy', 0) else 'No'
            }
        }
    
    def _batter_vs_batter(self, batter1: str, batter2: str) -> Dict:
        """Compare batting performance of two batters"""
        stats1 = self.stats_engine.get_player_stats(batter1)
        stats2 = self.stats_engine.get_player_stats(batter2)
        
        if not stats1['batting'] or not stats2['batting']:
            return {'error': f'One or both players are not batters'}
        
        batting1 = stats1['batting']
        batting2 = stats2['batting']
        
        return {
            'type': 'batter_vs_batter',
            'batter1': batter1,
            'batter2': batter2,
            'comparison': {
                'innings': {
                    batter1: batting1['matches'],
                    batter2: batting2['matches']
                },
                'runs': {
                    batter1: batting1['runs'],
                    batter2: batting2['runs'],
                    'difference': batting1['runs'] - batting2['runs']
                },
                'average': {
                    batter1: batting1['average'],
                    batter2: batting2['average'],
                    'better': batter1 if batting1['average'] > batting2['average'] else batter2
                },
                'strike_rate': {
                    batter1: batting1['strike_rate'],
                    batter2: batting2['strike_rate'],
                    'better': batter1 if batting1['strike_rate'] > batting2['strike_rate'] else batter2
                },
                'highest_score': {
                    batter1: batting1['highest_score'],
                    batter2: batting2['highest_score']
                },
                'balls_faced': {
                    batter1: batting1.get('balls', 0),
                    batter2: batting2.get('balls', 0)
                },
                'fours': {
                    batter1: batting1.get('fours', 0),
                    batter2: batting2.get('fours', 0)
                },
                'sixes': {
                    batter1: batting1.get('sixes', 0),
                    batter2: batting2.get('sixes', 0)
                },
                'fifties': {
                    batter1: batting1.get('fifties', 0),
                    batter2: batting2.get('fifties', 0)
                },
                'centuries': {
                    batter1: batting1.get('centuries', 0),
                    batter2: batting2.get('centuries', 0)
                }
            }
        }
    
    def _bowler_vs_bowler(self, bowler1: str, bowler2: str) -> Dict:
        """Compare bowling performance of two bowlers"""
        stats1 = self.stats_engine.get_player_stats(bowler1)
        stats2 = self.stats_engine.get_player_stats(bowler2)
        
        if not stats1['bowling'] or not stats2['bowling']:
            return {'error': f'One or both players are not bowlers'}
        
        bowling1 = stats1['bowling']
        bowling2 = stats2['bowling']
        
        return {
            'type': 'bowler_vs_bowler',
            'bowler1': bowler1,
            'bowler2': bowler2,
            'comparison': {
                'innings': {
                    bowler1: bowling1['matches'],
                    bowler2: bowling2['matches']
                },
                'wickets': {
                    bowler1: bowling1['wickets'],
                    bowler2: bowling2['wickets'],
                    'difference': bowling1['wickets'] - bowling2['wickets']
                },
                'runs_conceded': {
                    bowler1: bowling1['runs_conceded'],
                    bowler2: bowling2['runs_conceded']
                },
                'economy': {
                    bowler1: bowling1['economy'],
                    bowler2: bowling2['economy'],
                    'better': bowler1 if bowling1['economy'] < bowling2['economy'] else bowler2
                },
                'overs': {
                    bowler1: bowling1.get('overs', 0),
                    bowler2: bowling2.get('overs', 0)
                },
                'matches': {
                    bowler1: bowling1.get('matches', 0),
                    bowler2: bowling2.get('matches', 0)
                },
                'average': {
                    bowler1: bowling1.get('average', 0),
                    bowler2: bowling2.get('average', 0)
                },
                'best_figures': {
                    bowler1: bowling1.get('best_figures', '—'),
                    bowler2: bowling2.get('best_figures', '—')
                },
                'four_wickets': {
                    bowler1: bowling1.get('four_wickets', 0),
                    bowler2: bowling2.get('four_wickets', 0)
                },
                'maiden_overs': {
                    bowler1: bowling1.get('maiden_overs', 0),
                    bowler2: bowling2.get('maiden_overs', 0)
                }
            }
        }
    
    def get_insights(self) -> List[str]:
        """Generate general insights from the data"""
        insights = []
        
        # Most successful team
        best_team = self.team_performance.loc[self.team_performance['win_rate'].idxmax()]
        insights.append(f"Best performing team: {best_team['team']} with {round(best_team['win_rate']*100, 1)}% win rate")
        
        # Top batsman
        top_batsman = self.stats_engine.get_top_performers('batting', 1)[0]
        insights.append(f"All-time leading run scorer: {top_batsman['player']} with {top_batsman['runs']} runs")
        
        # Top bowler
        top_bowler = self.stats_engine.get_top_performers('bowling', 1)[0]
        insights.append(f"All-time leading wicket-taker: {top_bowler['player']} with {top_bowler['wickets']} wickets")
        
        # Total matches
        insights.append(f"Total IPL matches analyzed: {len(self.matches_df)}")
        
        return insights


if __name__ == "__main__":
    loader = IPLDataLoader()
    matches, deliveries = loader.load_data()
    matches, deliveries = loader.preprocess_data()
    
    ai_engine = AIEngine(matches, deliveries)
    print("AI Engine initialized successfully")
    
    # Test predictions
    print("\nMatch Prediction Example:")
    pred = ai_engine.predict_match_winner("Mumbai Indians", "Chennai Super Kings")
    print(pred)

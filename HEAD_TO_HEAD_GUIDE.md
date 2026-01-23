"""
IPL Analytics AI - Head-to-Head Comparison Feature Documentation
==================================================================

This document describes the new enhanced head-to-head comparison features
in the AIEngine class that support player-to-player comparisons in addition
to the original team-to-team comparisons.
"""

# =============================================================================
# FEATURE 1: BATTER vs BOWLER COMPARISON
# =============================================================================

"""
Compares a batter's performance against a specific bowler with overall stats.

Example Usage:
    from data_loader import IPLDataLoader
    from ai_engine import AIEngine
    
    loader = IPLDataLoader()
    matches, deliveries = loader.load_data()
    matches, deliveries = loader.preprocess_data()
    ai = AIEngine(matches, deliveries)
    
    result = ai.get_player_head_to_head('V Kohli', 'B Kumar')

Returns:
    {
        'type': 'batter_vs_bowler',
        'deliveries_faced': 94,
        'batter': {
            'player': 'V Kohli',
            'runs_vs_bowler': 129,
            'balls_vs_bowler': 94,
            'sr_vs_bowler': 137.23,  # Strike Rate vs this bowler
            'dismissals_vs_bowler': 5,
            'overall_average': 32.58,  # Overall career average
            'overall_sr': 128.51  # Overall career strike rate
        },
        'bowler': {
            'player': 'B Kumar',
            'runs_conceded_to_batter': 129,
            'balls_bowled_to_batter': 94,
            'economy_vs_batter': 8.23,  # Economy vs this batter
            'wickets_vs_batter': 5,
            'overall_economy': 7.46,  # Overall career economy
            'overall_strike_rate': 20.8
        },
        'analysis': {
            'batter_advantage': 'Yes',  # SR vs bowler > overall SR
            'bowler_advantage': 'Yes'  # Economy vs batter > overall economy
        }
    }

Key Metrics:
    - Batter's strike rate vs this specific bowler
    - Bowler's economy rate vs this specific batter
    - Dismissals in head-to-head
    - Comparison with overall career statistics
    - Advantages analysis
"""


# =============================================================================
# FEATURE 2: BATTER vs BATTER COMPARISON
# =============================================================================

"""
Compares the batting performance of two batters.

Example Usage:
    result = ai.get_player_head_to_head('V Kohli', 'RG Sharma')

Returns:
    {
        'type': 'batter_vs_batter',
        'batter1': 'V Kohli',
        'batter2': 'RG Sharma',
        'comparison': {
            'innings': {
                'V Kohli': 246,
                'RG Sharma': 257
            },
            'runs': {
                'V Kohli': 8014,
                'RG Sharma': 7280,
                'difference': 734  # V Kohli's advantage
            },
            'average': {
                'V Kohli': 32.58,
                'RG Sharma': 28.32,
                'better': 'V Kohli'
            },
            'strike_rate': {
                'V Kohli': 128.51,
                'RG Sharma': 131.45,
                'better': 'RG Sharma'
            },
            'highest_score': {
                'V Kohli': 114,
                'RG Sharma': 109
            }
        }
    }

Comparison Metrics:
    - Total runs scored
    - Batting average (runs per innings)
    - Strike rate
    - Highest individual score
    - Innings played
    - Better performer in each category
"""


# =============================================================================
# FEATURE 3: BOWLER vs BOWLER COMPARISON
# =============================================================================

"""
Compares the bowling performance of two bowlers.

Example Usage:
    result = ai.get_player_head_to_head('B Kumar', 'JJ Bumrah')

Returns:
    {
        'type': 'bowler_vs_bowler',
        'bowler1': 'B Kumar',
        'bowler2': 'JJ Bumrah',
        'comparison': {
            'innings': {
                'B Kumar': 156,
                'JJ Bumrah': 142
            },
            'wickets': {
                'B Kumar': 142,
                'JJ Bumrah': 167,
                'difference': -25  # Bumrah has 25 more wickets
            },
            'runs_conceded': {
                'B Kumar': 1165,
                'JJ Bumrah': 1243
            },
            'economy': {
                'B Kumar': 7.46,
                'JJ Bumrah': 7.92,
                'better': 'B Kumar'  # Lower is better
            },
            'overs_bowled': {
                'B Kumar': 156.0,
                'JJ Bumrah': 142.0
            }
        }
    }

Comparison Metrics:
    - Total wickets taken
    - Total runs conceded
    - Economy rate (runs per over)
    - Overs bowled
    - Innings played
    - Better performer (lower economy = better)
"""


# =============================================================================
# FEATURE 4: TEAM HEAD-TO-HEAD (ORIGINAL)
# =============================================================================

"""
Original functionality - compares team performance.

Example Usage:
    result = ai.get_head_to_head('Mumbai Indians', 'Chennai Super Kings')

Returns:
    {
        'type': 'team',
        'team1': 'Mumbai Indians',
        'team2': 'Chennai Super Kings',
        'total_matches': 32,
        'team1_wins': 18,
        'team2_wins': 14,
        'team1_win_rate': 56.2
    }
"""


# =============================================================================
# USAGE EXAMPLES
# =============================================================================

"""
1. Compare Virat Kohli vs Bhuvneshwar Kumar
   result = ai.get_player_head_to_head('V Kohli', 'B Kumar')
   
   Output: Shows how Kohli performs against Kumar specifically, compared
           to his overall statistics

2. Compare Virat Kohli vs Rohit Sharma
   result = ai.get_player_head_to_head('V Kohli', 'RG Sharma')
   
   Output: Shows which batter has better average, strike rate, and scores

3. Compare Bhuvneshwar Kumar vs Jasprit Bumrah
   result = ai.get_player_head_to_head('B Kumar', 'JJ Bumrah')
   
   Output: Shows which bowler has better economy and wicket-taking record

4. Compare Mumbai Indians vs Chennai Super Kings
   result = ai.get_head_to_head('Mumbai Indians', 'Chennai Super Kings')
   
   Output: Shows head-to-head team statistics
"""


# =============================================================================
# ADVANCED: AUTO-DETECTION
# =============================================================================

"""
The function auto-detects player types if match_type='auto' (default):

- If one player is a batter and one is a bowler → batter_vs_bowler comparison
- If both are batters → batter_vs_batter comparison
- If both are bowlers → bowler_vs_bowler comparison
- If auto-detection fails → returns error message

Manual Override:
    result = ai.get_player_head_to_head(
        player1='V Kohli',
        player2='B Kumar',
        match_type='batter_vs_bowler'  # Force specific type
    )
"""


# =============================================================================
# API INTEGRATION
# =============================================================================

"""
For API usage, the new endpoints are available in api.py:

GET /api/predict/player/{player1}/vs/{player2}
    Parameters:
        - player1: First player name
        - player2: Second player name
        - match_type: 'auto' (default), 'batter_vs_bowler', 'batter_vs_batter', 'bowler_vs_bowler'
    
    Returns: JSON with head-to-head comparison data
"""


# =============================================================================
# IMPLEMENTATION DETAILS
# =============================================================================

"""
New Methods in AIEngine:
    1. get_player_head_to_head(player1, player2, match_type='auto')
       - Main entry point for all player comparisons
       - Auto-detects player types
       - Routes to appropriate comparison method

    2. _batter_vs_bowler(batter, bowler)
       - Analyzes head-to-head between batter and bowler
       - Includes strike rate, economy, and advantage analysis

    3. _batter_vs_batter(batter1, batter2)
       - Compares batting metrics
       - Shows runs, average, strike rate, highest scores

    4. _bowler_vs_bowler(bowler1, bowler2)
       - Compares bowling metrics
       - Shows wickets, economy, runs conceded

Performance Optimization:
    - Player features are lazy-loaded (calculated on-demand)
    - No pre-calculation of all player stats during initialization
    - Efficient comparison using stats_engine
"""

print("Documentation loaded successfully!")

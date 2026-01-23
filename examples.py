"""
IPL Analytics AI Platform - Usage Examples
============================================

This file demonstrates various ways to use the IPL Analytics AI Platform.
Run individual examples to understand the platform's capabilities.
"""

from data_loader import IPLDataLoader
from stats_engine import StatsEngine
from ai_engine import AIEngine
import pandas as pd


# ============================================================================
# EXAMPLE 1: Load and Explore Data
# ============================================================================

def example_load_data():
    """Load and explore IPL dataset"""
    print("\n" + "="*70)
    print("EXAMPLE 1: Load and Explore Data")
    print("="*70)
    
    loader = IPLDataLoader()
    matches, deliveries = loader.load_data()
    matches, deliveries = loader.preprocess_data()
    
    summary = loader.get_summary_stats()
    
    print(f"\n📊 Dataset Overview:")
    print(f"   Total Matches: {summary['total_matches']}")
    print(f"   Seasons Covered: {summary['seasons']}")
    print(f"   Teams: {summary['teams']}")
    print(f"   Venues: {summary['venues']}")
    print(f"   Date Range: {summary['date_range'][0].date()} to {summary['date_range'][1].date()}")
    
    print(f"\n📋 Matches Data Shape: {matches.shape}")
    print(f"📋 Deliveries Data Shape: {deliveries.shape}")
    
    return loader, matches, deliveries


# ============================================================================
# EXAMPLE 2: Analyze Top Players
# ============================================================================

def example_top_players(stats_engine):
    """Get top performers across different categories"""
    print("\n" + "="*70)
    print("EXAMPLE 2: Analyze Top Players")
    print("="*70)
    
    # Top batsmen
    print("\n🏏 Top 10 Batsmen (by total runs):")
    top_batsmen = stats_engine.get_top_performers('batting', 10)
    for i, player in enumerate(top_batsmen, 1):
        print(f"   {i:2d}. {player['player']:<25} - {player['runs']:>5} runs")
    
    # Top bowlers
    print("\n🎯 Top 10 Bowlers (by wickets):")
    top_bowlers = stats_engine.get_top_performers('bowling', 10)
    for i, player in enumerate(top_bowlers, 1):
        print(f"   {i:2d}. {player['player']:<25} - {player['wickets']:>3} wickets")


# ============================================================================
# EXAMPLE 3: Detailed Player Analysis
# ============================================================================

def example_player_analysis(stats_engine):
    """Analyze detailed statistics for a specific player"""
    print("\n" + "="*70)
    print("EXAMPLE 3: Detailed Player Analysis")
    print("="*70)
    
    player_name = "Virat Kohli"
    stats = stats_engine.get_player_stats(player_name)
    
    print(f"\n👤 Player: {player_name}")
    
    if stats['batting']:
        batting = stats['batting']
        print(f"\n   Batting Statistics:")
        print(f"      Matches: {batting.get('matches', 0)}")
        print(f"      Runs: {batting.get('runs', 0)}")
        print(f"      Balls: {batting.get('balls', 0)}")
        print(f"      Average: {batting.get('average', 0):.2f}")
        print(f"      Strike Rate: {batting.get('strike_rate', 0):.2f}")
        print(f"      Highest Score: {batting.get('highest_score', 0)}")
    
    if stats['bowling']:
        bowling = stats['bowling']
        print(f"\n   Bowling Statistics:")
        print(f"      Matches: {bowling.get('matches', 0)}")
        print(f"      Wickets: {bowling.get('wickets', 0)}")
        print(f"      Runs Conceded: {bowling.get('runs_conceded', 0)}")
        print(f"      Economy: {bowling.get('economy', 0):.2f}")
        print(f"      Overs Bowled: {bowling.get('overs', 0)}")


# ============================================================================
# EXAMPLE 4: Team Performance Analysis
# ============================================================================

def example_team_analysis(stats_engine, loader):
    """Analyze team statistics and performance"""
    print("\n" + "="*70)
    print("EXAMPLE 4: Team Performance Analysis")
    print("="*70)
    
    teams = sorted(set(
        list(loader.matches_df['team1'].unique()) + 
        list(loader.matches_df['team2'].unique())
    ))
    
    print(f"\n📊 Top 10 Teams by Win Rate:")
    team_stats_list = []
    for team in teams:
        team_stat = stats_engine.get_team_stats(team)
        team_stats_list.append(team_stat)
    
    team_stats_list.sort(key=lambda x: x['win_percentage'], reverse=True)
    
    for i, team_stat in enumerate(team_stats_list[:10], 1):
        win_pct = team_stat['win_percentage']
        wins = team_stat['wins']
        total = team_stat['matches']
        print(f"   {i:2d}. {team_stat['team']:<30} - {win_pct:>5.1f}% ({wins}/{total} wins)")


# ============================================================================
# EXAMPLE 5: Player Recent Form
# ============================================================================

def example_player_form(stats_engine):
    """Analyze recent form of a player"""
    print("\n" + "="*70)
    print("EXAMPLE 5: Player Recent Form")
    print("="*70)
    
    player_name = "AB de Villiers"
    
    form = stats_engine.get_player_form(player_name, last_n_matches=10)
    
    print(f"\n📈 Recent Form: {player_name}")
    print(f"   Last 10 Matches (Runs):")
    
    recent_runs = form['recent_runs']
    if recent_runs:
        runs_list = list(recent_runs.values())
        for i, runs in enumerate(runs_list[-10:], 1):
            bar = "█" * (runs // 5) if runs > 0 else ""
            print(f"   Match {i:2d}: {runs:>3} runs {bar}")
        print(f"\n   Average (Last 10): {form['avg_recent']:.2f} runs")
        print(f"   Last Match: {form['last_match_runs']} runs")


# ============================================================================
# EXAMPLE 6: Match Predictions
# ============================================================================

def example_match_predictions(ai_engine):
    """Predict match outcomes between teams"""
    print("\n" + "="*70)
    print("EXAMPLE 6: Match Predictions")
    print("="*70)
    
    matchups = [
        ("Mumbai Indians", "Chennai Super Kings"),
        ("Kolkata Knight Riders", "Royal Challengers Bengaluru"),
        ("Delhi Capitals", "Rajasthan Royals"),
    ]
    
    print("\n🔮 Match Outcome Predictions:")
    
    for team1, team2 in matchups:
        prediction = ai_engine.predict_match_winner(team1, team2)
        
        if 'error' not in prediction:
            winner = prediction['predicted_winner']
            confidence = prediction['confidence'] * 100
            
            t1_prob = prediction['team1_win_probability'] * 100
            t2_prob = prediction['team2_win_probability'] * 100
            
            print(f"\n   {team1} vs {team2}")
            print(f"      Predicted Winner: {winner}")
            print(f"      Confidence: {confidence:.1f}%")
            print(f"      {team1} Win Probability: {t1_prob:.1f}%")
            print(f"      {team2} Win Probability: {t2_prob:.1f}%")


# ============================================================================
# EXAMPLE 7: Head-to-Head Analysis
# ============================================================================

def example_head_to_head(ai_engine):
    """Compare teams in head-to-head matchups"""
    print("\n" + "="*70)
    print("EXAMPLE 7: Head-to-Head Analysis")
    print("="*70)
    
    matchups = [
        ("Mumbai Indians", "Chennai Super Kings"),
        ("Kolkata Knight Riders", "Royal Challengers Bengaluru"),
    ]
    
    print("\n📊 Head-to-Head Statistics:")
    
    for team1, team2 in matchups:
        h2h = ai_engine.get_head_to_head(team1, team2)
        
        print(f"\n   {team1} vs {team2}")
        print(f"      Total Matches: {h2h['total_matches']}")
        print(f"      {team1} Wins: {h2h['team1_wins']}")
        print(f"      {team2} Wins: {h2h['team2_wins']}")
        print(f"      {team1} Win Rate: {h2h['team1_win_rate']:.1f}%")


# ============================================================================
# EXAMPLE 8: Team Trend Analysis
# ============================================================================

def example_trend_analysis(ai_engine):
    """Analyze performance trends over years"""
    print("\n" + "="*70)
    print("EXAMPLE 8: Team Trend Analysis")
    print("="*70)
    
    teams = ["Mumbai Indians", "Chennai Super Kings", "Kolkata Knight Riders"]
    
    print("\n📈 Performance Trends:")
    
    for team in teams:
        trend = ai_engine.get_trend_analysis(team)
        
        if 'error' not in trend:
            print(f"\n   {team}:")
            print(f"      Current Form: {trend['current_form']}")
            print(f"      Wins by Year:")
            
            for year in sorted(trend['trend'].keys()):
                wins = trend['trend'][year]
                bar = "█" * wins
                print(f"         {year}: {wins} wins {bar}")


# ============================================================================
# EXAMPLE 9: AI Insights
# ============================================================================

def example_ai_insights(ai_engine):
    """Get AI-generated insights from data"""
    print("\n" + "="*70)
    print("EXAMPLE 9: AI-Generated Insights")
    print("="*70)
    
    insights = ai_engine.get_insights()
    
    print(f"\n💡 Key Insights from IPL Data:\n")
    for i, insight in enumerate(insights, 1):
        print(f"   {i}. {insight}")


# ============================================================================
# EXAMPLE 10: Data Export
# ============================================================================

def example_data_export(loader):
    """Export processed data to CSV"""
    print("\n" + "="*70)
    print("EXAMPLE 10: Data Export")
    print("="*70)
    
    matches = loader.matches_df
    deliveries = loader.deliveries_df
    
    print(f"\n💾 Exporting Data...")
    
    # Export matches data
    matches.to_csv('exported_matches.csv', index=False)
    print(f"   ✅ Exported matches: exported_matches.csv ({len(matches)} rows)")
    
    # Export deliveries data
    deliveries.to_csv('exported_deliveries.csv', index=False)
    print(f"   ✅ Exported deliveries: exported_deliveries.csv ({len(deliveries)} rows)")
    
    print(f"\n   Files are ready for further analysis in Excel, Python, or other tools.")


# ============================================================================
# EXAMPLE 11: Custom Analysis
# ============================================================================

def example_custom_analysis(loader, stats_engine):
    """Perform custom analysis on the data"""
    print("\n" + "="*70)
    print("EXAMPLE 11: Custom Analysis")
    print("="*70)
    
    matches = loader.matches_df
    deliveries = loader.deliveries_df
    
    # Analysis 1: Most successful batters in final overs
    print(f"\n🎯 Analysis 1: Score Distribution by Year")
    matches_by_year = matches.groupby('year').size()
    print(f"   Year-wise Match Count:")
    for year, count in matches_by_year.items():
        print(f"      {int(year)}: {count} matches")
    
    # Analysis 2: Most frequent match winners
    print(f"\n🏆 Analysis 2: Most Frequent Winners")
    winners = matches['winner'].value_counts().head(5)
    for team, wins in winners.items():
        print(f"      {team}: {wins} victories")
    
    # Analysis 3: Most productive venues
    print(f"\n🏟️  Analysis 3: Most Active Venues")
    venues = matches['venue'].value_counts().head(5)
    for venue, count in venues.items():
        print(f"      {venue}: {count} matches")


# ============================================================================
# EXAMPLE 12: Player Comparison
# ============================================================================

def example_player_comparison(stats_engine):
    """Compare statistics between multiple players"""
    print("\n" + "="*70)
    print("EXAMPLE 12: Player Comparison")
    print("="*70)
    
    players = ["Virat Kohli", "Rohit Sharma", "MS Dhoni"]
    
    print(f"\n📊 Comparison: Top Batsmen")
    print(f"\n{'Player':<20} {'Matches':<10} {'Runs':<10} {'Average':<10} {'SR':<10}")
    print("-" * 60)
    
    for player in players:
        stats = stats_engine.get_player_stats(player)
        if stats['batting']:
            batting = stats['batting']
            print(f"{player:<20} {batting['matches']:<10} {batting['runs']:<10} " +
                  f"{batting['average']:<10.2f} {batting['strike_rate']:<10.2f}")


# ============================================================================
# Main Execution
# ============================================================================

def main():
    """Run all examples"""
    print("\n" + "🏏" * 35)
    print("IPL Analytics AI Platform - Examples")
    print("🏏" * 35)
    
    try:
        # Initialize
        print("\n⏳ Loading and initializing platform...")
        loader, matches, deliveries = example_load_data()
        stats_engine = StatsEngine(matches, deliveries)
        ai_engine = AIEngine(matches, deliveries)
        print("✅ Platform initialized successfully!\n")
        
        # Run examples
        example_top_players(stats_engine)
        example_player_analysis(stats_engine)
        example_team_analysis(stats_engine, loader)
        example_player_form(stats_engine)
        example_match_predictions(ai_engine)
        example_head_to_head(ai_engine)
        example_trend_analysis(ai_engine)
        example_ai_insights(ai_engine)
        example_custom_analysis(loader, stats_engine)
        example_player_comparison(stats_engine)
        
        # Optional: export data
        print("\n📊 To export data, uncomment the line below:")
        print("   # example_data_export(loader)")
        
        print("\n" + "="*70)
        print("✅ All examples completed successfully!")
        print("="*70)
        print("\n📚 Next Steps:")
        print("   1. Run Streamlit Dashboard: streamlit run app.py")
        print("   2. Run FastAPI Server: python3 api.py")
        print("   3. View API Docs: http://localhost:8000/docs")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

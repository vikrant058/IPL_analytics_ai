import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from data_loader import IPLDataLoader
from stats_engine import StatsEngine
from ai_engine import AIEngine
from openai_handler import CricketChatbot
import requests
import os
import warnings
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

DOTENV_PATH = Path(__file__).resolve().parent / ".env"


def _read_dotenv_openai_key(dotenv_path: Path = DOTENV_PATH) -> str | None:
    """Read OPENAI_API_KEY from a .env file without printing it."""
    try:
        content = dotenv_path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return None
    except OSError:
        return None

    for line in content:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("OPENAI_API_KEY="):
            return stripped.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def _mask_key(key: str) -> str:
    if not key:
        return "(missing)"
    if len(key) <= 12:
        return "(set)"
    return f"{key[:7]}…{key[-4:]}"


def _get_openai_api_key() -> tuple[str | None, str]:
    """Return (api_key, source_label) without exposing the key.
    
    Force reload from .env to avoid Streamlit caching stale values.
    Prioritizes .env over shell environment to prevent old exported keys from interfering.
    """
    from dotenv import dotenv_values
    
    # First priority: Streamlit secrets (for Streamlit Cloud)
    try:
        secrets_key = st.secrets.get("OPENAI_API_KEY")
        if secrets_key:
            return secrets_key, "streamlit_secrets"
    except Exception:
        pass
    
    # Second priority: .env file (explicit, controlled, clean)
    dotenv_dict = dotenv_values(DOTENV_PATH)
    dotenv_key = dotenv_dict.get("OPENAI_API_KEY")
    if dotenv_key:
        return dotenv_key, "env_file"
    
    # Last resort: shell environment variable (may be old/revoked)
    env_key = os.getenv("OPENAI_API_KEY")
    if env_key:
        return env_key, "shell_env"
    
    return None, "missing"


# Load environment variables from .env file (explicit path so Streamlit CWD doesn't matter).
# We set override=True to avoid the common situation where an old exported shell variable
# silently overrides the intended .env key and causes confusing 401s.
load_dotenv(dotenv_path=DOTENV_PATH, override=True)

warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="IPL Analytics AI",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom styling
st.markdown("""
    <style>
    .main {
        padding-top: 2rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize data
@st.cache_resource
def load_data():
    loader = IPLDataLoader()
    matches, deliveries = loader.load_data()
    matches, deliveries = loader.preprocess_data()
    return loader, StatsEngine(matches, deliveries), AIEngine(matches, deliveries)

loader, stats_engine, ai_engine = load_data()

# Sidebar navigation
st.sidebar.title("🏏 IPL Analytics AI")
page = st.sidebar.radio(
    "Navigation",
    ["Player Analysis", "Team Analysis", "Head-to-Head", "AI Chatbot"]
    # "Predictions" - Will be enabled later
)

# Main content
st.title("🏏 IPL Analytics AI Platform")

if page == "Player Analysis":
    st.header("Player Analysis")
    
    # Get unique players and teams
    all_batters = loader.deliveries_df['batter'].unique()
    all_bowlers = loader.deliveries_df['bowler'].unique()
    all_players = sorted(set(all_batters).union(set(all_bowlers)))
    all_teams = sorted(set(
        list(loader.matches_df['team1'].unique()) + 
        list(loader.matches_df['team2'].unique())
    ))
    years = sorted(loader.matches_df['year'].unique())
    venues = sorted(loader.matches_df['venue'].unique())
    
    # Player selection
    col1 = st.columns(1)[0]
    
    with col1:
        player_name = st.selectbox("👤 Select Player", all_players)
    
    # Filters section
    st.markdown("### 🎯 Filters")
    
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    
    with filter_col1:
        selected_seasons = st.multiselect("Season(s)", years)
    
    with filter_col2:
        selected_venues = st.multiselect("Venue(s)", venues)
    
    with filter_col3:
        home_away = st.selectbox("Home/Away", ["All", "Home", "Away"])
    
    filter_col4, filter_col5 = st.columns(2)
    
    with filter_col4:
        innings_order = st.selectbox("Innings Order", ["All", "1st Innings", "2nd Innings"])
    
    with filter_col5:
        selected_team = st.selectbox("Team", ["All"] + all_teams)
    
    # Build filters dict
    filters = {}
    
    # Only apply filters if options are actually selected
    if selected_seasons:
        filters['seasons'] = selected_seasons
    
    if selected_venues:
        filters['venue'] = selected_venues
    
    filters['home_away'] = home_away.lower() if home_away != "All" else None
    filters['innings_order'] = int(innings_order[0]) if innings_order != "All" else None
    filters['team'] = selected_team if selected_team != "All" else None
    
    # Get player stats
    if player_name:
        stats = stats_engine.get_player_stats(player_name, filters)
        
        # Show filter summary
        filter_summary = []
        if selected_seasons and selected_seasons != ["All"]:
            filter_summary.append(f"Seasons: {', '.join(map(str, selected_seasons))}")
        if selected_venues and selected_venues != ["All"]:
            filter_summary.append(f"Venues: {', '.join(selected_venues)}")
        if home_away != "All":
            filter_summary.append(f"Type: {home_away}")
        if innings_order != "All":
            filter_summary.append(f"Innings: {innings_order}")
        if selected_team != "All":
            filter_summary.append(f"Team: {selected_team}")
        
        if filter_summary:
            st.info("📌 " + " | ".join(filter_summary))
        
        # Display batting stats
        if stats.get('batting'):
            batting = stats['batting']
            
            st.markdown("### 🏏 Batting Summary")
            
            # Create batting summary table (transposed - metrics as columns)
            batting_data = {
                'Matches': [batting.get('matches', 0)],
                'Innings': [batting.get('innings', 0)],
                'Runs': [batting.get('runs', 0)],
                'Average': [f"{batting.get('average', 0):.2f}"],
                'Strike Rate': [f"{batting.get('strike_rate', 0):.2f}"],
                '4s': [batting.get('fours', 0)],
                '6s': [batting.get('sixes', 0)],
                '50s': [batting.get('fifties', 0)],
                '100s': [batting.get('centuries', 0)],
                'Highest Score': [batting.get('highest_score', 0)],
                'Balls Faced': [batting.get('balls', 0)],
                'Dot Ball %': [f"{batting.get('dot_ball_percentage', 0):.2f}%"]
            }
            batting_df = pd.DataFrame(batting_data)
            st.dataframe(batting_df, use_container_width=True, hide_index=True)
        
        # Display bowling stats
        if stats.get('bowling'):
            bowling = stats['bowling']
            
            st.markdown("### ⚡ Bowling Summary")
            
            # Create bowling summary table (transposed - metrics as columns)
            bowling_data = {
                'Matches': [bowling.get('matches', 0)],
                'Innings': [bowling.get('innings', 0)],
                'Overs': [bowling.get('overs', 0)],
                'Wickets': [bowling.get('wickets', 0)],
                'Runs Conceded': [bowling.get('runs_conceded', 0)],
                'Economy': [f"{bowling.get('economy', 0):.2f}"],
                'Average': [f"{bowling.get('average', 0):.2f}"],
                'Best Figures': [bowling.get('best_figures', 0)],
                '4W Hauls': [bowling.get('four_wickets', 0)],
                'Maiden Overs': [bowling.get('maiden_overs', 0)],
                'Dot Ball %': [f"{bowling.get('dot_ball_percentage', 0):.2f}%"]
            }
            bowling_df = pd.DataFrame(bowling_data)
            st.dataframe(bowling_df, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # Top performers
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Top 10 Batsmen")
        top_batsmen = stats_engine.get_top_performers('batting', 10)
        df = pd.DataFrame(top_batsmen)
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    with col2:
        st.subheader("Top 10 Bowlers")
        top_bowlers = stats_engine.get_top_performers('bowling', 10)
        df = pd.DataFrame(top_bowlers)
        st.dataframe(df, use_container_width=True, hide_index=True)

elif page == "Team Analysis":
    st.header("Team Analysis")
    
    all_teams = sorted(set(
        list(loader.matches_df['team1'].unique()) + 
        list(loader.matches_df['team2'].unique())
    ))
    years = sorted(loader.matches_df['year'].unique())
    venues = sorted(loader.matches_df['venue'].unique())
    
    # Team selection
    col1 = st.columns(1)[0]
    with col1:
        team = st.selectbox("🏏 Select Team", all_teams)
    
    # Filters section
    st.markdown("### 🎯 Filters")
    
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    
    with filter_col1:
        selected_seasons = st.multiselect("Season(s)", years)
    
    with filter_col2:
        selected_venues = st.multiselect("Venue(s)", venues)
    
    with filter_col3:
        home_away = st.selectbox("Home/Away", ["All", "Home", "Away"])
    
    filter_col4, filter_col5 = st.columns(2)
    
    with filter_col4:
        innings_order = st.selectbox("Innings Order", ["All", "1st Innings", "2nd Innings"])
    
    with filter_col5:
        st.markdown("")  # Empty space for alignment
    
    # Build filters dict
    filters = {}
    
    # Only apply filters if options are actually selected
    if selected_seasons:
        filters['seasons'] = selected_seasons
    
    if selected_venues:
        filters['venue'] = selected_venues
    
    filters['home_away'] = home_away.lower() if home_away != "All" else None
    filters['innings_order'] = int(innings_order[0]) if innings_order != "All" else None
    
    if team:
        team_stats = stats_engine.get_team_stats(team, filters)
        
        # Show filter summary
        filter_summary = []
        if selected_seasons:
            filter_summary.append(f"Seasons: {', '.join(map(str, selected_seasons))}")
        if selected_venues:
            filter_summary.append(f"Venues: {', '.join(selected_venues)}")
        if home_away != "All":
            filter_summary.append(f"Type: {home_away}")
        if innings_order != "All":
            filter_summary.append(f"Innings: {innings_order}")
        
        if filter_summary:
            st.info("📌 " + " | ".join(filter_summary))
        
        # Display team stats summary
        st.markdown("### 📊 Team Summary")
        
        team_data = {
            'Matches': [team_stats.get('matches', 0)],
            'Wins': [team_stats.get('wins', 0)],
            'Losses': [team_stats.get('matches', 0) - team_stats.get('wins', 0)],
            'Win %': [f"{team_stats.get('win_percentage', 0):.1f}%"],
            'Win Rate': [f"{team_stats.get('win_rate', 0):.2f}"]
        }
        team_df = pd.DataFrame(team_data)
        st.dataframe(team_df, use_container_width=True, hide_index=True)
        
        st.divider()
        
        # Team trend
        trend = ai_engine.get_trend_analysis(team)
        if 'trend' in trend:
            st.subheader("Performance Trend")
            trend_data = trend['trend']
            fig = px.line(x=list(trend_data.keys()), y=list(trend_data.values()),
                         labels={'x': 'Year', 'y': 'Wins'},
                         markers=True)
            st.plotly_chart(fig, use_container_width=True)

elif page == "AI Chatbot":
    st.header("🤖 AI Cricket Analytics Chatbot")
    
    st.markdown("""
    Ask me anything about IPL cricket analytics! Try natural language queries like:
    - "kohli vs bumrah" - Head-to-head comparison
    - "virat kohli statistics" - Player profile
    - "mumbai indians performance" - Team stats
    """)
    
    # Auto-load API key (no UI prompts)
    api_key, key_source = _get_openai_api_key()
    
    if not api_key:
        st.error("❌ OpenAI API key not found in `.env` or Streamlit secrets.")
        st.markdown("""
Add your API key to `.env` file:
```bash
OPENAI_API_KEY=sk-proj-your-key-here
```
Then restart the app.
""")
    else:
        # Initialize chatbot if API key is available
        try:
            # Initialize chatbot (no caching - always use fresh key)
            chatbot = CricketChatbot(loader.matches_df, loader.deliveries_df, api_key)
            
            st.divider()
            
            # Chat interface with better styling
            st.markdown("### 💬 Query Builder")
            
            # Create columns for input and buttons
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                user_query = st.text_input(
                    "Ask about cricket analytics:",
                    placeholder="e.g., 'kohli vs bumrah' or 'virat kohli stats'",
                    key="chatbot_input",
                    label_visibility="collapsed"
                )
            
            with col2:
                search_btn = st.button("🔍 Search", key="search_btn", use_container_width=True)
            
            with col3:
                st.markdown("**Quick Queries:**")
            
            # Quick query buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Kohli Stats", key="q1", use_container_width=True):
                    user_query = "virat kohli statistics"
                    search_btn = True
            with col2:
                if st.button("Kohli vs Bumrah", key="q2", use_container_width=True):
                    user_query = "virat kohli vs jasprit bumrah"
                    search_btn = True
            with col3:
                if st.button("Top Players", key="q3", use_container_width=True):
                    user_query = "top batsmen in IPL"
                    search_btn = True
            
            # Process query
            if search_btn and user_query:
                st.markdown("---")
                with st.spinner("🔍 Analyzing your query..."):
                    response = chatbot.get_response(user_query)
                
                st.markdown("### 📊 Response:")
                st.markdown(response)
            
            st.divider()
            
            # Collapsible capabilities section
            with st.expander("💡 What can the chatbot do?"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("""
                    ✅ Player Statistics
                    - Individual player profiles
                    - Batting/Bowling records
                    - Career highlights
                    
                    ✅ Comparisons
                    - Head-to-head matchups
                    - Player vs Player
                    - Performance analysis
                    """)
                with col2:
                    st.markdown("""
                    ✅ Team Analysis
                    - Team performance
                    - Win rates
                    - Season trends
                    
                    ✅ Natural Language
                    - Conversational queries
                    - Multiple ways to ask
                    - Smart interpretation
                    """)
        except Exception as e:
            st.error(f"❌ Error initializing chatbot: {str(e)}")
            st.info("Make sure your OpenAI API key is valid and has access to the GPT API.")


elif page == "Head-to-Head":
    st.header("Head-to-Head Comparisons")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏏 Compare Players")
        st.markdown("Select any two players to compare based on their primary skills")
    
    with col2:
        st.subheader("🎯 How it Works")
        st.markdown("""
        - **Batter vs Batter**: Compares batting stats
        - **Bowler vs Bowler**: Compares bowling stats
        - **Batter vs Bowler**: Shows head-to-head matchup stats
        """)
    
    st.divider()
    
    all_players = sorted(set(
        list(loader.deliveries_df['batter'].unique()) + 
        list(loader.deliveries_df['bowler'].unique())
    ))
    
    col1, col2 = st.columns(2)
    
    with col1:
        player1 = st.selectbox("Select Player 1", all_players, key="h2h_player1")
    
    with col2:
        player2 = st.selectbox("Select Player 2", [p for p in all_players if p != player1], key="h2h_player2")
    
    if st.button("Compare Players", key="h2h_compare_btn", use_container_width=True):
        st.markdown(f"### 📊 Comparison: {player1} vs {player2}")
        
        # Let AI engine auto-detect and handle everything
        result = ai_engine.get_player_head_to_head(player1, player2)
        
        if 'error' in result:
            st.error(f"❌ {result['error']}")
        
        # Batter vs Bowler case
        elif result.get('type') == 'batter_vs_bowler':
            st.success(f"🎯 **Batter vs Bowler Matchup**")
            st.divider()
            
            batter = result['batter']['player']
            bowler = result['bowler']['player']
            batter_info = result['batter']
            bowler_info = result['bowler']
            
            # Create comprehensive head-to-head comparison table
            h2h_data = {
                'Metric': [
                    'Deliveries',
                    'Runs',
                    'Strike Rate / Economy',
                    'Dismissals / Wickets',
                    'Average / Balls per Wicket'
                ],
                batter: [
                    result['deliveries_faced'],
                    batter_info['runs_vs_bowler'],
                    f"{batter_info['sr_vs_bowler']:.2f}",
                    batter_info['dismissals_vs_bowler'],
                    f"{batter_info['overall_average']:.2f}"
                ],
                bowler: [
                    bowler_info['balls_bowled_to_batter'],
                    bowler_info['runs_conceded_to_batter'],
                    f"{bowler_info['economy_vs_batter']:.2f}",
                    bowler_info['wickets_vs_batter'],
                    f"{bowler_info.get('overall_strike_rate', '—')}"
                ]
            }
            
            h2h_df = pd.DataFrame(h2h_data)
            st.dataframe(h2h_df, use_container_width=True, hide_index=True)
            
            st.subheader("Career Stats")
            
            # Create career stats comparison table
            career_data = {
                'Metric': ['Strike Rate / Economy', 'Average'],
                batter: [
                    f"{batter_info['overall_sr']:.2f}",
                    f"{batter_info['overall_average']:.2f}"
                ],
                bowler: [
                    f"{bowler_info['overall_economy']:.2f}",
                    f"{bowler_info.get('overall_strike_rate', '—')}"
                ]
            }
            
            career_df = pd.DataFrame(career_data)
            st.dataframe(career_df, use_container_width=True, hide_index=True)
            
            st.divider()
            
            # Advantage analysis
            analysis = result['analysis']
            col1, col2 = st.columns(2)
            
            with col1:
                if analysis['batter_advantage'] == 'Yes':
                    st.success(f"✅ **{batter} has ADVANTAGE**")
                    st.caption(f"Vs this bowler: {batter_info['sr_vs_bowler']:.1f}% | Career: {batter_info['overall_sr']:.1f}%")
                else:
                    st.warning(f"⚠️ **{batter} at DISADVANTAGE**")
                    st.caption(f"Vs this bowler: {batter_info['sr_vs_bowler']:.1f}% | Career: {batter_info['overall_sr']:.1f}%")
            
            with col2:
                if analysis['bowler_advantage'] == 'Yes':
                    st.success(f"✅ **{bowler} has ADVANTAGE**")
                    st.caption(f"Vs this batter: {bowler_info['economy_vs_batter']:.2f} | Career: {bowler_info['overall_economy']:.2f}")
                else:
                    st.warning(f"⚠️ **{bowler} at DISADVANTAGE**")
                    st.caption(f"Vs this batter: {bowler_info['economy_vs_batter']:.2f} | Career: {bowler_info['overall_economy']:.2f}")
        
        # Batter vs Batter case
        elif result.get('type') == 'batter_vs_batter':
            st.success(f"🏏 **Batter vs Batter Comparison**")
            st.divider()
            
            batter1 = result['batter1']
            batter2 = result['batter2']
            comp = result['comparison']
            
            # Create comprehensive batting comparison table
            comparison_data = {
                'Metric': [
                    'Matches',
                    'Innings',
                    'Runs',
                    'Average',
                    'Strike Rate',
                    'Highest Score',
                    'Balls Faced',
                    '4s',
                    '6s',
                    '50s',
                    '100s'
                ],
                batter1: [
                    comp['innings'][batter1],
                    comp['innings'][batter1],
                    comp['runs'][batter1],
                    f"{comp['average'][batter1]:.2f}",
                    f"{comp['strike_rate'][batter1]:.2f}",
                    comp['highest_score'][batter1],
                    comp.get('balls_faced', {}).get(batter1, '—'),
                    comp.get('fours', {}).get(batter1, '—'),
                    comp.get('sixes', {}).get(batter1, '—'),
                    comp.get('fifties', {}).get(batter1, '—'),
                    comp.get('centuries', {}).get(batter1, '—')
                ],
                batter2: [
                    comp['innings'][batter2],
                    comp['innings'][batter2],
                    comp['runs'][batter2],
                    f"{comp['average'][batter2]:.2f}",
                    f"{comp['strike_rate'][batter2]:.2f}",
                    comp['highest_score'][batter2],
                    comp.get('balls_faced', {}).get(batter2, '—'),
                    comp.get('fours', {}).get(batter2, '—'),
                    comp.get('sixes', {}).get(batter2, '—'),
                    comp.get('fifties', {}).get(batter2, '—'),
                    comp.get('centuries', {}).get(batter2, '—')
                ]
            }
            
            comparison_df = pd.DataFrame(comparison_data)
            st.dataframe(comparison_df, use_container_width=True, hide_index=True)
        
        # Bowler vs Bowler case
        elif result.get('type') == 'bowler_vs_bowler':
            st.success(f"⚡ **Bowler vs Bowler Comparison**")
            st.divider()
            
            bowler1 = result['bowler1']
            bowler2 = result['bowler2']
            comp = result['comparison']
            
            # Create comprehensive bowling comparison table
            comparison_data = {
                'Metric': [
                    'Matches',
                    'Innings',
                    'Wickets',
                    'Runs Conceded',
                    'Economy',
                    'Average',
                    'Best Figures',
                    'Overs',
                    '4W Hauls',
                    'Maiden Overs'
                ],
                bowler1: [
                    comp['innings'][bowler1],
                    comp['innings'][bowler1],
                    comp['wickets'][bowler1],
                    comp['runs_conceded'][bowler1],
                    f"{comp['economy'][bowler1]:.2f}",
                    f"{comp.get('average', {}).get(bowler1, 0):.2f}" if comp.get('average', {}).get(bowler1) else '—',
                    comp.get('best_figures', {}).get(bowler1, '—'),
                    comp.get('overs', {}).get(bowler1, '—'),
                    comp.get('four_wickets', {}).get(bowler1, '—'),
                    comp.get('maiden_overs', {}).get(bowler1, '—')
                ],
                bowler2: [
                    comp['innings'][bowler2],
                    comp['innings'][bowler2],
                    comp['wickets'][bowler2],
                    comp['runs_conceded'][bowler2],
                    f"{comp['economy'][bowler2]:.2f}",
                    f"{comp.get('average', {}).get(bowler2, 0):.2f}" if comp.get('average', {}).get(bowler2) else '—',
                    comp.get('best_figures', {}).get(bowler2, '—'),
                    comp.get('overs', {}).get(bowler2, '—'),
                    comp.get('four_wickets', {}).get(bowler2, '—'),
                    comp.get('maiden_overs', {}).get(bowler2, '—')
                ]
            }
            
            comparison_df = pd.DataFrame(comparison_data)
            st.dataframe(comparison_df, use_container_width=True, hide_index=True)
        
        else:
            st.info(f"No comparison data found. Result: {result}")
# Footer
st.divider()
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col2:
    st.caption("IPL Analytics AI Platform")

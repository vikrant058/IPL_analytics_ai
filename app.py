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
        padding-top: 1rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
    h1, h2, h3, h4 {
        color: #1f77b4;
        font-weight: 600;
    }
    .stButton > button {
        border-radius: 5px;
        font-weight: 500;
    }
    .stDataFrame {
        font-size: 13px;
    }
    .section-header {
        padding: 10px 0;
        border-bottom: 2px solid #1f77b4;
        margin-bottom: 15px;
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
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Choose Section",
    ["💬 Chat & Analytics", "📊 Player & Team Data"],
    label_visibility="collapsed"
)

# Main content based on page
if page == "💬 Chat & Analytics":
    st.title("🏏 Cricket Analytics")
    
    # Create a section selector for better organization
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("💬 Chatbot", key="nav_chatbot", use_container_width=True):
            st.session_state.active_section = "chatbot"
    
    with col2:
        if st.button("⚡ Compare", key="nav_h2h", use_container_width=True):
            st.session_state.active_section = "h2h"
    
    st.divider()
    
    # Initialize session state
    if "active_section" not in st.session_state:
        st.session_state.active_section = "chatbot"
    
    active_section = st.session_state.active_section
    
    # Get all players and teams for H2H
    all_players = sorted(set(
        list(loader.deliveries_df['batter'].unique()) + 
        list(loader.deliveries_df['bowler'].unique())
    ))
    
    # CHATBOT SECTION
    if active_section == "chatbot":
        st.markdown("Ask me anything about IPL! Try queries like:")
        st.markdown("""
        • **Player stats**: "virat kohli statistics"  
        • **Head-to-head**: "kohli vs bumrah"  
        • **Comparisons**: "top batsmen this season"
        """)
        
        # Auto-load API key (no UI prompts)
        api_key, key_source = _get_openai_api_key()
        
        if not api_key:
            st.error("❌ OpenAI API key not found in `.env` or Streamlit secrets.")
            st.markdown("""Add your API key to `.env` file:
```bash
OPENAI_API_KEY=sk-proj-your-key-here
```
Then restart the app.""")
        else:
            # Initialize chatbot if API key is available
            try:
                # Initialize chatbot (no caching - always use fresh key)
                chatbot = CricketChatbot(loader.matches_df, loader.deliveries_df, api_key)
                
                # Chat interface - compact layout
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    user_query = st.text_input(
                        "Query:",
                        placeholder="e.g., 'kohli vs bumrah'",
                        key="chatbot_input",
                        label_visibility="collapsed"
                    )
                
                with col2:
                    search_btn = st.button("🔍 Search", key="search_btn", use_container_width=True)
                
                # Quick query buttons - compact
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
                    if st.button("Top Batsmen", key="q3", use_container_width=True):
                        user_query = "top batsmen in IPL"
                        search_btn = True
                
                # Process query
                if search_btn and user_query:
                    st.divider()
                    with st.spinner("🔍 Analyzing..."):
                        response = chatbot.get_response(user_query)
                    
                    st.markdown(response)
                
            except Exception as e:
                st.error(f"❌ Error initializing chatbot: {str(e)[:100]}")
                st.info("Make sure your OpenAI API key is valid.")
    
    elif active_section == "h2h":
        # Head-to-Head Comparison section
        st.markdown("Compare any two players side by side.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            player1 = st.selectbox("Select Player 1", all_players, key="h2h_player1")
        
        with col2:
            player2 = st.selectbox("Select Player 2", [p for p in all_players if p != player1], key="h2h_player2")
        
        if st.button("📊 Compare Players", key="h2h_compare_btn", use_container_width=True):
            st.divider()
            
            # Let AI engine auto-detect and handle everything
            result = ai_engine.get_player_head_to_head(player1, player2)
            
            if 'error' in result:
                st.error(f"❌ {result['error']}")
            
            # Batter vs Bowler case
            elif result.get('type') == 'batter_vs_bowler':
                st.markdown(f"### {player1} vs {player2}")
                
                batter = result['batter']['player']
                bowler = result['bowler']['player']
                batter_info = result['batter']
                bowler_info = result['bowler']
                
                # Head-to-head matchup visualization
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**🏏 {batter}** (Batter)")
                    st.metric("Deliveries Faced", result['deliveries_faced'])
                    st.metric("Runs", batter_info['runs_vs_bowler'])
                    st.metric("Strike Rate", f"{batter_info['sr_vs_bowler']:.2f}%")
                    st.metric("Dismissals", batter_info['dismissals_vs_bowler'])
                
                with col2:
                    st.markdown(f"**⚡ {bowler}** (Bowler)")
                    st.metric("Balls Bowled", bowler_info['balls_bowled_to_batter'])
                    st.metric("Runs Conceded", bowler_info['runs_conceded_to_batter'])
                    st.metric("Economy", f"{bowler_info['economy_vs_batter']:.2f}")
                    st.metric("Wickets", bowler_info['wickets_vs_batter'])
                
                st.divider()
                
                # Head-to-head stats table
                st.markdown("**Head-to-Head Statistics**")
                h2h_data = {
                    'Metric': ['Deliveries', 'Runs', 'SR/Economy', 'Dismissals/Wickets'],
                    batter: [
                        result['deliveries_faced'],
                        batter_info['runs_vs_bowler'],
                        f"{batter_info['sr_vs_bowler']:.2f}%",
                        batter_info['dismissals_vs_bowler']
                    ],
                    bowler: [
                        bowler_info['balls_bowled_to_batter'],
                        bowler_info['runs_conceded_to_batter'],
                        f"{bowler_info['economy_vs_batter']:.2f}",
                        bowler_info['wickets_vs_batter']
                    ]
                }
                
                st.dataframe(pd.DataFrame(h2h_data), use_container_width=True, hide_index=True)
                
                st.divider()
                
                # Advantage analysis
                analysis = result['analysis']
                col1, col2 = st.columns(2)
                
                with col1:
                    if analysis['batter_advantage'] == 'Yes':
                        st.success(f"✅ {batter} HAS ADVANTAGE vs this bowler")
                    else:
                        st.warning(f"⚠️ {batter} AT DISADVANTAGE vs this bowler")
                
                with col2:
                    if analysis['bowler_advantage'] == 'Yes':
                        st.success(f"✅ {bowler} HAS ADVANTAGE vs this batter")
                    else:
                        st.warning(f"⚠️ {bowler} AT DISADVANTAGE vs this batter")
            
            # Batter vs Batter case
            elif result.get('type') == 'batter_vs_batter':
                st.success(f"🏏 **{player1} vs {player2} (Batters Comparison)**")
                
                batter1 = result['batter1']
                batter2 = result['batter2']
                comp = result['comparison']
                
                comparison_data = {
                    'Metric': ['Runs', 'Average', 'Strike Rate', '50s', '100s'],
                    batter1: [
                        comp['runs'][batter1],
                        f"{comp['average'][batter1]:.2f}",
                        f"{comp['strike_rate'][batter1]:.2f}",
                        comp.get('fifties', {}).get(batter1, '—'),
                        comp.get('centuries', {}).get(batter1, '—')
                    ],
                    batter2: [
                        comp['runs'][batter2],
                        f"{comp['average'][batter2]:.2f}",
                        f"{comp['strike_rate'][batter2]:.2f}",
                        comp.get('fifties', {}).get(batter2, '—'),
                        comp.get('centuries', {}).get(batter2, '—')
                    ]
                }
                
                st.dataframe(pd.DataFrame(comparison_data), use_container_width=True, hide_index=True)
            
            # Bowler vs Bowler case
            elif result.get('type') == 'bowler_vs_bowler':
                st.success(f"⚡ **{player1} vs {player2} (Bowlers Comparison)**")
                
                bowler1 = result['bowler1']
                bowler2 = result['bowler2']
                comp = result['comparison']
                
                comparison_data = {
                    'Metric': ['Wickets', 'Economy', 'Runs Conceded', 'Best Figures'],
                    bowler1: [
                        comp['wickets'][bowler1],
                        f"{comp['economy'][bowler1]:.2f}",
                        comp['runs_conceded'][bowler1],
                        comp.get('best_figures', {}).get(bowler1, '—')
                    ],
                    bowler2: [
                        comp['wickets'][bowler2],
                        f"{comp['economy'][bowler2]:.2f}",
                        comp['runs_conceded'][bowler2],
                        comp.get('best_figures', {}).get(bowler2, '—')
                    ]
                }
                
                st.dataframe(pd.DataFrame(comparison_data), use_container_width=True, hide_index=True)

elif page == "� Player & Team Data":
    st.title("Data & Analytics")
    
    # Section selector
    col1, col2 = st.columns([1, 4])
    
    with col1:
        if st.button("🏏 Players", key="nav_player", use_container_width=True):
            st.session_state.data_section = "player"
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🏆 Teams", key="nav_team", use_container_width=True):
            st.session_state.data_section = "team"
    
    st.divider()
    
    if "data_section" not in st.session_state:
        st.session_state.data_section = "player"
    
    data_section = st.session_state.data_section
    
    # Get all players and teams
    all_batters = loader.deliveries_df['batter'].unique()
    all_bowlers = loader.deliveries_df['bowler'].unique()
    all_players = sorted(set(all_batters).union(set(all_bowlers)))
    all_teams = sorted(set(
        list(loader.matches_df['team1'].unique()) + 
        list(loader.matches_df['team2'].unique())
    ))
    
    if data_section == "player":
        # Player Profile - Tables only
        st.markdown("### Player Statistics")
        player_name = st.selectbox("Select Player", all_players, key="profile_player")
        
        if player_name:
            stats = stats_engine.get_player_stats(player_name)
            
            # Display batting stats as table
            if stats.get('batting'):
                batting = stats['batting']
                st.markdown("**Batting Statistics**")
                
                batting_data = {
                    'Metric': ['Matches', 'Innings', 'Runs', 'Average', 'Strike Rate', '50s', '100s', '4s', '6s', 'Highest Score', 'Balls Faced'],
                    'Value': [
                        batting.get('matches', 0),
                        batting.get('innings', 0),
                        batting.get('runs', 0),
                        f"{batting.get('average', 0):.2f}",
                        f"{batting.get('strike_rate', 0):.2f}",
                        batting.get('fifties', 0),
                        batting.get('centuries', 0),
                        batting.get('fours', 0),
                        batting.get('sixes', 0),
                        batting.get('highest_score', 0),
                        batting.get('balls', 0)
                    ]
                }
                
                st.dataframe(pd.DataFrame(batting_data), use_container_width=True, hide_index=True)
            
            # Display bowling stats as table
            if stats.get('bowling'):
                bowling = stats['bowling']
                st.markdown("**Bowling Statistics**")
                
                bowling_data = {
                    'Metric': ['Matches', 'Innings', 'Overs', 'Wickets', 'Runs Conceded', 'Economy', 'Average', 'Best Figures', '4W Hauls', 'Maiden Overs'],
                    'Value': [
                        bowling.get('matches', 0),
                        bowling.get('innings', 0),
                        bowling.get('overs', '—'),
                        bowling.get('wickets', 0),
                        bowling.get('runs_conceded', 0),
                        f"{bowling.get('economy', 0):.2f}",
                        f"{bowling.get('average', 0):.2f}",
                        bowling.get('best_figures', '—'),
                        bowling.get('four_wickets', 0),
                        bowling.get('maiden_overs', 0)
                    ]
                }
                
                st.dataframe(pd.DataFrame(bowling_data), use_container_width=True, hide_index=True)
    
    elif data_section == "team":
        # Team Profile - Tables only
        st.markdown("### Team Statistics")
        team = st.selectbox("Select Team", all_teams, key="profile_team")
        
        if team:
            team_stats = stats_engine.get_team_stats(team)
            
            st.markdown("**Team Summary**")
            
            team_data = {
                'Metric': ['Matches', 'Wins', 'Losses', 'Win Rate', 'Win Percentage'],
                'Value': [
                    team_stats.get('matches', 0),
                    team_stats.get('wins', 0),
                    team_stats.get('matches', 0) - team_stats.get('wins', 0),
                    f"{team_stats.get('win_rate', 0):.2f}",
                    f"{team_stats.get('win_percentage', 0):.1f}%"
                ]
            }
            
            st.dataframe(pd.DataFrame(team_data), use_container_width=True, hide_index=True)
            
            st.divider()
            
            # Team performance trend
            trend = ai_engine.get_trend_analysis(team)
            if 'trend' in trend:
                st.markdown("**Performance by Year**")
                
                trend_data = trend['trend']
                trend_table = {
                    'Year': list(trend_data.keys()),
                    'Wins': list(trend_data.values())
                }
                
                st.dataframe(pd.DataFrame(trend_table), use_container_width=True, hide_index=True)
            
            st.divider()
            
            # Top performers
            st.markdown("**Top Performers**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("Top Batsmen (All Teams)")
                top_batsmen = stats_engine.get_top_performers('batting', 10)
                if top_batsmen:
                    df = pd.DataFrame(top_batsmen)
                    st.dataframe(df, use_container_width=True, hide_index=True)
            
            with col2:
                st.markdown("Top Bowlers (All Teams)")
                top_bowlers = stats_engine.get_top_performers('bowling', 10)
                if top_bowlers:
                    df = pd.DataFrame(top_bowlers)
                    st.dataframe(df, use_container_width=True, hide_index=True)

# Footer
st.divider()
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("🏏 IPL Analytics AI")
with col2:
    st.caption("Powered by Streamlit + OpenAI")
with col3:
    st.caption(f"Data: 1,169 matches | 278K+ deliveries")

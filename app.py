# IPL Analytics ChatBot - Modern Bottom Navigation UI
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


# Load environment variables from .env file
load_dotenv(dotenv_path=DOTENV_PATH, override=True)

warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="IPL Analytics AI",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "Get Help": "https://github.com",
        "About": "# IPL Analytics AI\nMobile-friendly cricket analytics powered by AI"
    }
)

# Custom styling - Modern app design with bottom navigation
st.markdown("""
    <style>
    .main {
        padding-top: 0.5rem;
        padding-bottom: 120px;
    }
    
    /* Card container styling */
    .stat-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #f0f1f3 100%);
        padding: 20px;
        border-radius: 8px;
        border-left: 4px solid #556b82;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 12px;
    }
    
    .stat-card-title {
        font-size: 13px;
        color: #666;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
    }
    
    .stat-card-value {
        font-size: 28px;
        color: #333;
        font-weight: 700;
        margin-bottom: 4px;
    }
    
    .stat-card-subtitle {
        font-size: 12px;
        color: #888;
        font-weight: 500;
    }
    
    /* BOTTOM NAVIGATION BAR */
    .bottom-nav {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: white;
        border-top: 2px solid #e8eaed;
        display: flex;
        justify-content: space-around;
        align-items: center;
        height: 80px;
        z-index: 999;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.08);
    }
    
    .nav-button {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 80px;
        cursor: pointer;
        border: none;
        background: none;
        text-decoration: none;
        transition: all 0.3s ease;
        font-size: 12px;
        color: #888;
        font-weight: 500;
    }
    
    .nav-button:hover {
        color: #2c3e50;
        background-color: #f8f9fa;
    }
    
    .nav-button.active {
        color: #556b82;
        background-color: #f0f1f3;
        border-top: 3px solid #556b82;
    }
    
    .nav-icon {
        font-size: 24px;
        margin-bottom: 4px;
    }
    
    .nav-label {
        font-size: 11px;
        text-align: center;
    }
    
    /* Metric styling */
    .stMetric {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 6px;
        border: 1px solid #e8eaed;
    }
    
    .stMetric label {
        font-size: 12px;
        color: #666;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.3px;
    }
    
    /* Typography */
    h1 {
        color: #2c3e50;
        font-weight: 700;
        letter-spacing: -0.5px;
        margin-bottom: 20px;
    }
    
    h2 {
        color: #556b82;
        font-weight: 600;
        margin-top: 20px;
        margin-bottom: 15px;
        border-bottom: 2px solid #e8eaed;
        padding-bottom: 10px;
    }
    
    h3, h4 {
        color: #556b82;
        font-weight: 600;
    }
    
    /* Buttons */
    .stButton > button {
        border-radius: 6px;
        font-weight: 500;
        background-color: #f0f1f3;
        color: #2c3e50;
        border: 1px solid #d0d1d3;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        background-color: #e0e1e3;
        border-color: #556b82;
    }
    
    /* Tables */
    .stDataFrame {
        font-size: 13px;
        background-color: #f8f9fa;
        border: 1px solid #e8eaed;
    }
    
    .stDataFrame table {
        background-color: white;
    }
    
    /* Divider */
    hr {
        border-color: #e8eaed;
        margin: 20px 0;
    }
    
    /* Text input styling */
    .stTextInput input {
        background-color: #f8f9fa;
        border: 1px solid #d0d1d3;
        color: #2c3e50;
        border-radius: 6px;
    }
    
    /* Select styling */
    .stSelectbox select {
        background-color: #f8f9fa;
        border: 1px solid #d0d1d3;
        color: #2c3e50;
        border-radius: 6px;
    }
    
    /* H2H player card */
    .h2h-player-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 20px;
        border-radius: 8px;
        border-left: 4px solid #556b82;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    .h2h-player-name {
        font-size: 16px;
        color: #2c3e50;
        font-weight: 700;
        margin-bottom: 15px;
    }
    
    /* Success/Error/Warning styling */
    .success {
        background-color: #e8f5e9;
        color: #2e7d32;
        padding: 12px 16px;
        border-radius: 6px;
        border-left: 4px solid #2e7d32;
    }
    
    .warning {
        background-color: #fff3e0;
        color: #e65100;
        padding: 12px 16px;
        border-radius: 6px;
        border-left: 4px solid #e65100;
    }
    
    /* ===== MOBILE RESPONSIVE DESIGN ===== */
    @media (max-width: 768px) {
        .main {
            padding-top: 0.5rem !important;
            padding-left: 8px !important;
            padding-right: 8px !important;
        }
        
        h1 {
            font-size: 24px !important;
            margin-bottom: 12px !important;
        }
        
        h2 {
            font-size: 18px !important;
            margin-top: 12px !important;
            margin-bottom: 10px !important;
            padding-bottom: 8px !important;
        }
        
        h3, h4 {
            font-size: 16px !important;
        }
        
        .stat-card {
            padding: 12px !important;
            margin-bottom: 8px !important;
            border-left: 3px solid #556b82 !important;
        }
        
        .stButton > button {
            width: 100% !important;
            padding: 10px 12px !important;
            font-size: 14px !important;
            border-radius: 5px !important;
            margin-bottom: 8px !important;
        }
        
        .stTextInput input,
        .stSelectbox select,
        .stTextArea textarea {
            font-size: 16px !important;
            padding: 10px !important;
            border-radius: 5px !important;
        }
        
        .stDataFrame {
            font-size: 12px !important;
            overflow-x: auto !important;
        }
        
        p {
            font-size: 14px !important;
            line-height: 1.5 !important;
        }
        
        .stMetric {
            padding: 10px !important;
            margin-bottom: 8px !important;
        }
    }
    
    @media (max-width: 480px) {
        .main {
            padding-left: 4px !important;
            padding-right: 4px !important;
        }
        
        h1 {
            font-size: 20px !important;
        }
        
        .stat-card {
            padding: 10px !important;
        }
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

# Initialize session state for page navigation
if "current_page" not in st.session_state:
    st.session_state.current_page = "chatbot"

# Handle page navigation from columns
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("💬 Chatbot", key="nav_chatbot", use_container_width=True):
        st.session_state.current_page = "chatbot"
        st.rerun()

with col2:
    if st.button("📊 Profiles", key="nav_profiles", use_container_width=True):
        st.session_state.current_page = "profiles"
        st.rerun()

with col3:
    if st.button("⚔️ Compare", key="nav_compare", use_container_width=True):
        st.session_state.current_page = "compare"
        st.rerun()

with col4:
    if st.button("📈 Trends", key="nav_trends", use_container_width=True):
        st.session_state.current_page = "trends"
        st.rerun()

st.divider()

# ===== MAIN CONTENT AREA =====
st.markdown("""
    <div style="text-align: center; padding-top: 10px; margin-bottom: 20px;">
        <h1 style="margin: 0; color: #2c3e50;">🏏 IPL Analytics AI</h1>
        <p style="margin: 0; color: #888; font-size: 13px;">Cricket Intelligence Powered by AI</p>
    </div>
""", unsafe_allow_html=True)

st.divider()

# ===== PAGE ROUTING =====
current_page = st.session_state.current_page

# CHATBOT PAGE
if current_page == "chatbot":
    st.markdown("### 💬 Ask me anything about IPL Cricket")
    st.markdown("*Get instant insights on player statistics, records, and performance trends*")
    st.markdown("")
    
    # Auto-load API key
    api_key, key_source = _get_openai_api_key()
    
    if not api_key:
        st.error("❌ OpenAI API key not found in `.env` or Streamlit secrets.")
        st.markdown("""Add your API key to `.env` file:
```bash
OPENAI_API_KEY=sk-proj-your-key-here
```
Then restart the app.""")
    else:
        # Initialize chatbot
        try:
            chatbot = CricketChatbot(loader.matches_df, loader.deliveries_df, api_key)
            
            # Chat interface
            col1, col2 = st.columns([4, 1])
            
            with col1:
                user_query = st.text_input(
                    "Your query:",
                    placeholder="e.g., 'kohli vs bumrah in powerplay'",
                    key="chatbot_input",
                    label_visibility="collapsed"
                )
            
            with col2:
                search_btn = st.button("🔍", key="search_btn", use_container_width=True, help="Search")
            
            # Quick suggestions
            st.markdown("**💡 Try asking:**")
            
            col1, col2, col3, col4 = st.columns(4)
            suggestions = [
                ("Kohli Stats", "virat kohli statistics", "q1"),
                ("Bumrah", "jasprit bumrah bowling", "q2"),
                ("Kohli vs Bumrah", "virat kohli vs jasprit bumrah", "q3"),
                ("Records", "highest score in ipl", "q4"),
            ]
            
            for i, (label, query, key) in enumerate(suggestions):
                with [col1, col2, col3, col4][i]:
                    if st.button(label, key=key, use_container_width=True):
                        user_query = query
                        search_btn = True
            
            col1, col2, col3, col4 = st.columns(4)
            suggestions2 = [
                ("Bumrah Records", "bumrah bowling records", "q5"),
                ("Top Runs", "most runs in ipl", "q6"),
                ("Trends", "kohli last 5 matches", "q7"),
                ("Wickets", "most wickets in ipl", "q8"),
            ]
            
            for i, (label, query, key) in enumerate(suggestions2):
                with [col1, col2, col3, col4][i]:
                    if st.button(label, key=key, use_container_width=True):
                        user_query = query
                        search_btn = True
            
            st.markdown("")
            
            # Process query
            if search_btn and user_query:
                st.divider()
                with st.spinner("🔍 Analyzing..."):
                    response = chatbot.get_response(user_query)
                
                # Display response
                st.markdown(response)
            
        except Exception as e:
            st.error(f"❌ Error initializing chatbot: {str(e)[:100]}")
            st.info("Make sure your OpenAI API key is valid.")

# PROFILES PAGE
elif current_page == "profiles":
    st.markdown("### 📊 Player & Team Statistics")
    st.markdown("*Explore detailed career performance data*")
    st.markdown("")
    
    # Get all players and teams
    all_batters = loader.deliveries_df['batter'].unique()
    all_bowlers = loader.deliveries_df['bowler'].unique()
    all_players = sorted(set(all_batters).union(set(all_bowlers)))
    all_teams = sorted(set(
        list(loader.matches_df['team1'].unique()) + 
        list(loader.matches_df['team2'].unique())
    ))
    
    profile_type = st.radio("Select Type", ["🏏 Players", "🏆 Teams"], horizontal=True, key="profile_type")
    
    st.divider()
    
    if profile_type == "🏏 Players":
        player_name = st.selectbox("Select Player", all_players, key="profile_player")
        
        if player_name:
            stats = stats_engine.get_player_stats(player_name)
            
            # Display batting and bowling stats side by side
            col1, col2 = st.columns(2)
            
            if stats.get('batting'):
                batting = stats['batting']
                with col1:
                    st.markdown("**Batting Statistics**")
                    
                    batting_data = {
                        'Stat': ['Matches', 'Innings', 'Runs', 'Average', 'Strike Rate', '50s', '100s', 'Highest'],
                        'Value': [
                            batting.get('matches', 0),
                            batting.get('innings', 0),
                            batting.get('runs', 0),
                            f"{batting.get('average', 0):.2f}",
                            f"{batting.get('strike_rate', 0):.2f}",
                            batting.get('fifties', 0),
                            batting.get('centuries', 0),
                            batting.get('highest_score', 0),
                        ]
                    }
                    
                    st.dataframe(pd.DataFrame(batting_data), use_container_width=True, hide_index=True)
            
            if stats.get('bowling'):
                bowling = stats['bowling']
                with col2:
                    st.markdown("**Bowling Statistics**")
                    
                    bowling_data = {
                        'Stat': ['Matches', 'Innings', 'Wickets', 'Economy', 'Average', 'Best Figures'],
                        'Value': [
                            bowling.get('matches', 0),
                            bowling.get('innings', 0),
                            bowling.get('wickets', 0),
                            f"{bowling.get('economy', 0):.2f}",
                            f"{bowling.get('average', 0):.2f}",
                            bowling.get('best_figures', '—'),
                        ]
                    }
                    
                    st.dataframe(pd.DataFrame(bowling_data), use_container_width=True, hide_index=True)
    
    else:  # Teams
        team = st.selectbox("Select Team", all_teams, key="profile_team")
        
        if team:
            team_stats = stats_engine.get_team_stats(team)
            
            team_data = {
                'Metric': ['Matches', 'Wins', 'Losses', 'Win Rate'],
                'Value': [
                    team_stats.get('matches', 0),
                    team_stats.get('wins', 0),
                    team_stats.get('matches', 0) - team_stats.get('wins', 0),
                    f"{team_stats.get('win_percentage', 0):.1f}%",
                ]
            }
            
            st.dataframe(pd.DataFrame(team_data), use_container_width=True, hide_index=True)

# COMPARE PAGE
elif current_page == "compare":
    st.markdown("### ⚔️ Head-to-Head Comparison")
    st.markdown("*Compare any two players and analyze their matchup*")
    st.markdown("")
    
    # Get all players
    all_batters = loader.deliveries_df['batter'].unique()
    all_bowlers = loader.deliveries_df['bowler'].unique()
    all_players = sorted(set(all_batters).union(set(all_bowlers)))
    
    col1, col2 = st.columns(2)
    
    with col1:
        player1 = st.selectbox("🏏 Player 1", all_players, key="h2h_player1")
    
    with col2:
        player2 = st.selectbox("⚡ Player 2", [p for p in all_players if p != player1], key="h2h_player2")
    
    if st.button("📊 Compare Players", key="h2h_compare_btn", use_container_width=True):
        st.divider()
        
        # Let AI engine auto-detect and handle everything
        result = ai_engine.get_player_head_to_head(player1, player2)
        
        if 'error' in result:
            st.error(f"❌ {result['error']}")
        else:
            # Display comparison results
            st.markdown(f"### {player1} vs {player2}")
            if isinstance(result, dict) and 'analysis' in result:
                st.markdown(result['analysis'])
            else:
                st.info("Comparison data processing...")

# TRENDS PAGE
elif current_page == "trends":
    st.markdown("### 📈 Player Trends & Form")
    st.markdown("*Track player performance over recent matches*")
    st.markdown("")
    
    # Get all players
    all_batters = loader.deliveries_df['batter'].unique()
    all_bowlers = loader.deliveries_df['bowler'].unique()
    all_players = sorted(set(all_batters).union(set(all_bowlers)))
    
    player = st.selectbox("Select Player", all_players, key="trend_player")
    
    if player:
        st.markdown(f"**Recent Form - {player}**")
        
        # Get recent matches
        recent_matches = stats_engine.get_last_n_matches(player, n=10)
        if recent_matches is not None and not recent_matches.empty:
            st.dataframe(recent_matches, use_container_width=True)
        else:
            st.info("No recent match data available for this player.")

# Footer
st.divider()
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("🏏 IPL Analytics AI")
with col2:
    st.caption("Powered by Streamlit + OpenAI")
with col3:
    st.caption(f"Data: 1,169 matches | 278K+ deliveries")

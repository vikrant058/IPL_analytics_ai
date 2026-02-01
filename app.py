# IPL Analytics ChatBot - Modern UI with Working Bottom Navigation
import streamlit as st
import pandas as pd
from data_loader import IPLDataLoader
from stats_engine import StatsEngine
from ai_engine import AIEngine
from openai_handler import CricketChatbot
import os
import warnings
from pathlib import Path
from dotenv import load_dotenv

DOTENV_PATH = Path(__file__).resolve().parent / ".env"

def _get_openai_api_key() -> tuple[str | None, str]:
    """Return (api_key, source_label) without exposing the key."""
    from dotenv import dotenv_values
    
    try:
        secrets_key = st.secrets.get("OPENAI_API_KEY")
        if secrets_key:
            return secrets_key, "streamlit_secrets"
    except Exception:
        pass
    
    dotenv_dict = dotenv_values(DOTENV_PATH)
    dotenv_key = dotenv_dict.get("OPENAI_API_KEY")
    if dotenv_key:
        return dotenv_key, "env_file"
    
    env_key = os.getenv("OPENAI_API_KEY")
    if env_key:
        return env_key, "shell_env"
    
    return None, "missing"

load_dotenv(dotenv_path=DOTENV_PATH, override=True)
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="IPL Analytics AI",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Modern styling with Streamlit tabs
st.markdown("""
    <style>
    .main {
        padding-top: 0.5rem;
        padding-bottom: 0;
    }
    
    /* Tab styling for better sizing */
    button[data-baseweb="tab"] {
        font-size: 16px !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        width: 100% !important;
    }
    
    /* Typography */
    h1 {
        color: #2c3e50;
        font-weight: 700;
        margin-bottom: 10px;
    }
    
    h2, h3 {
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
        width: 100% !important;
        padding: 10px 20px !important;
        font-size: 14px !important;
    }
    
    .stButton > button:hover {
        background-color: #e0e1e3;
        border-color: #556b82;
    }
    
    /* Radio buttons */
    .stRadio > label {
        font-size: 14px !important;
        font-weight: 500 !important;
    }
    
    /* Selectbox */
    .stSelectbox {
        width: 100% !important;
    }
    
    /* Mobile responsive */
    @media (max-width: 768px) {
        .main {
            padding-left: 8px !important;
            padding-right: 8px !important;
        }
        
        h1 {
            font-size: 24px !important;
        }
        
        h2 {
            font-size: 18px !important;
        }
        
        button[data-baseweb="tab"] {
            font-size: 13px !important;
            padding: 8px 12px !important;
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
    st.session_state.current_page = "cricbot"

# Initialize navigation history for back button
if "show_output" not in st.session_state:
    st.session_state.show_output = False

# Header
st.markdown("""
    <div style="text-align: center; padding: 10px 0 20px 0;">
        <h1 style="margin: 0;">🏏 IPL Analytics AI</h1>
        <p style="margin: 0; color: #888; font-size: 13px;">Cricket Intelligence Powered by AI</p>
    </div>
""", unsafe_allow_html=True)

# Show back button only when output is displayed (small version)
if st.session_state.show_output:
    col_back, col_spacer = st.columns([0.15, 5])
    with col_back:
        st.markdown("""
        <style>
            .back-btn-container button {
                height: 24px !important;
                width: 30px !important;
                padding: 2px 4px !important;
                font-size: 16px !important;
            }
        </style>
        """, unsafe_allow_html=True)
        if st.button("←", key="back_btn"):
            st.session_state.show_output = False
            st.rerun()

st.divider()

# ============ MULTI-PAGE NAVIGATION USING STREAMLIT TABS ============
# Use Streamlit's built-in tabs for proper navigation
tab_cricbot, tab_profiles, tab_h2h, tab_form = st.tabs([
    "🤖 Cricbot",
    "👤 Profiles", 
    "⚔️ H2H",
    "📈 Form"
])

# ============ CRICBOT PAGE ============
with tab_cricbot:
    st.markdown("### 🤖 Cricbot - Your Cricket Assistant")
    st.markdown("*Ask me anything about IPL cricket*")
    st.markdown("")
    
    api_key, _ = _get_openai_api_key()
    
    if not api_key:
        st.error("❌ OpenAI API key not found in `.env` or Streamlit secrets.")
        st.markdown("""Add to `.env`:
```
OPENAI_API_KEY=sk-proj-your-key-here
```""")
    else:
        try:
            chatbot = CricketChatbot(loader.matches_df, loader.deliveries_df, api_key)
            
            col1, col2 = st.columns([4, 1])
            with col1:
                user_query = st.text_input(
                    "Your query:",
                    placeholder="e.g., 'kohli statistics' or 'bumrah vs csk'",
                    key="chatbot_input",
                    label_visibility="collapsed"
                )
            with col2:
                search_btn = st.button("Search", key="search_btn", use_container_width=True)
            
            st.info("💡 **Try asking**: Player stats • Records & Rankings • Head-to-Head • Recent Form • Team Performance • Specific Filters")
            
            if search_btn and user_query:
                st.divider()
                with st.spinner("🔍 Analyzing..."):
                    response = chatbot.get_response(user_query)
                st.markdown(response)
                st.session_state.show_output = True
                
        except Exception as e:
            st.error(f"❌ Error: {str(e)[:100]}")

# ============ PLAYER PROFILES PAGE ============
with tab_profiles:
    st.markdown("### 👤 Player Profiles")
    st.markdown("*Browse IPL player and team data*")
    st.markdown("")
    
    all_batters = loader.deliveries_df['batter'].unique()
    all_bowlers = loader.deliveries_df['bowler'].unique()
    all_players = sorted(set(all_batters).union(set(all_bowlers)))
    all_teams = sorted(set(
        list(loader.matches_df['team1'].unique()) + 
        list(loader.matches_df['team2'].unique())
    ))
    
    # Normalize team names to avoid duplicates (Royal Challengers Bangalore -> Royal Challengers Bengaluru)
    normalized_teams = []
    seen = set()
    for team in all_teams:
        if team == 'Royal Challengers Bangalore':
            normalized_team = 'Royal Challengers Bengaluru'
        else:
            normalized_team = team
        
        if normalized_team not in seen:
            normalized_teams.append(normalized_team)
            seen.add(normalized_team)
    
    all_teams = sorted(normalized_teams)
    
    prof_type = st.radio("Select Type", ["🏏 Players", "🏆 Teams"], horizontal=True, key="prof_type")
    st.divider()
    
    if prof_type == "🏏 Players":
        player = st.selectbox("Select Player", all_players, key="sel_player")
        if player:
            stats = stats_engine.get_player_stats(player)
            
            # Display comprehensive player stats like Cricinfo
            st.markdown(f"### 🏏 {player} - Complete Career Stats")
            
            if stats.get('batting'):
                batting = stats['batting']
                st.markdown("#### 📊 **Batting Statistics**")
                
                # Main stats in two columns
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Matches", batting.get('matches', 0))
                with col2:
                    st.metric("Runs", batting.get('runs', 0))
                with col3:
                    st.metric("Average", f"{batting.get('average', 0):.2f}")
                with col4:
                    st.metric("Strike Rate", f"{batting.get('strike_rate', 0):.2f}")
                
                st.divider()
                
                # Detailed batting table
                batting_df = pd.DataFrame({
                    'Metric': ['Innings', 'Highest Score', 'Centuries', 'Fifties', 'Fours', 'Sixes', 'Dot Balls', 'Dot Ball %'],
                    'Value': [
                        batting.get('innings', 0),
                        batting.get('highest_score', 0),
                        batting.get('centuries', 0),
                        batting.get('fifties', 0),
                        batting.get('fours', 0),
                        batting.get('sixes', 0),
                        batting.get('dot_balls', 0),
                        f"{batting.get('dot_ball_percentage', 0):.1f}%"
                    ]
                })
                st.dataframe(batting_df, use_container_width=True, hide_index=True)
                st.session_state.show_output = True
            
            if stats.get('bowling'):
                bowling = stats['bowling']
                st.markdown("#### 🎯 **Bowling Statistics**")
                
                # Main stats in four columns
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Matches", bowling.get('matches', 0))
                with col2:
                    st.metric("Wickets", bowling.get('wickets', 0))
                with col3:
                    st.metric("Economy", f"{bowling.get('economy', 0):.2f}")
                with col4:
                    st.metric("Average", f"{bowling.get('average', 0):.2f}")
                
                st.divider()
                
                # Detailed bowling table
                bowling_df = pd.DataFrame({
                    'Metric': ['Innings', 'Runs Conceded', 'Balls Bowled', 'Overs', 'Best Figures', '4-Wicket Hauls', 'Maiden Overs', 'Dot Balls', 'Dot Ball %'],
                    'Value': [
                        bowling.get('innings', 0),
                        bowling.get('runs_conceded', 0),
                        bowling.get('balls', 0),
                        f"{bowling.get('overs', 0):.1f}",
                        bowling.get('best_figures', '—'),
                        bowling.get('four_wickets', 0),
                        bowling.get('maiden_overs', 0),
                        bowling.get('dot_balls', 0),
                        f"{bowling.get('dot_ball_percentage', 0):.1f}%"
                    ]
                })
                st.dataframe(bowling_df, use_container_width=True, hide_index=True)
                st.session_state.show_output = True
    
    else:  # Teams
        team = st.selectbox("Select Team", all_teams, key="sel_team")
        if team:
            team_stats = stats_engine.get_team_stats(team)
            team_df = pd.DataFrame({
                'Metric': ['Matches', 'Wins', 'Losses', 'Win %'],
                'Value': [
                    team_stats.get('matches', 0),
                    team_stats.get('wins', 0),
                    team_stats.get('matches', 0) - team_stats.get('wins', 0),
                    f"{team_stats.get('win_percentage', 0):.1f}%",
                ]
            })
            st.dataframe(team_df, use_container_width=True, hide_index=True)
            st.session_state.show_output = True

# ============ HEAD-TO-HEAD PAGE ============
with tab_h2h:
    st.markdown("### ⚔️ Player H2H Comparison")
    st.markdown("*Compare any two players*")
    st.markdown("")
    
    all_batters = loader.deliveries_df['batter'].unique()
    all_bowlers = loader.deliveries_df['bowler'].unique()
    all_players = sorted(set(all_batters).union(set(all_bowlers)))
    
    col1, col2 = st.columns(2)
    
    with col1:
        p1 = st.selectbox("Player 1", all_players, key="p1")
    with col2:
        p2 = st.selectbox("Player 2", [p for p in all_players if p != p1], key="p2")
    
    if st.button("⚔️ Compare", key="compare_btn", use_container_width=True):
        st.divider()
        result = ai_engine.get_player_head_to_head(p1, p2)
        
        if 'error' in result:
            st.error(f"❌ {result['error']}")
        else:
            st.markdown(f"### {p1} vs {p2}")
            if isinstance(result, dict) and 'analysis' in result:
                st.markdown(result['analysis'])
            else:
                st.info("Comparison data processing...")
            st.session_state.show_output = True

# ============ PLAYER FORM PAGE ============
with tab_form:
    st.markdown("### 📈 Player Form & Trends")
    st.markdown("*Track player performance over recent matches*")
    st.markdown("")
    
    all_batters = loader.deliveries_df['batter'].unique()
    all_bowlers = loader.deliveries_df['bowler'].unique()
    all_players = sorted(set(all_batters).union(set(all_bowlers)))
    
    player = st.selectbox("Select Player", all_players, key="trend_player")
    
    if player:
        st.markdown(f"**Recent Form - {player}**")
        recent = stats_engine.get_last_n_matches(player, n=10)
        
        # Handle both DataFrame and list returns
        if recent is not None:
            if isinstance(recent, list):
                if len(recent) > 0:
                    st.dataframe(recent, use_container_width=True)
                    st.session_state.show_output = True
                else:
                    st.info("No recent match data available.")
            elif hasattr(recent, 'empty'):
                if not recent.empty:
                    st.dataframe(recent, use_container_width=True)
                    st.session_state.show_output = True
                else:
                    st.info("No recent match data available.")
            else:
                st.dataframe(recent, use_container_width=True)
                st.session_state.show_output = True
        else:
            st.info("No recent match data available.")

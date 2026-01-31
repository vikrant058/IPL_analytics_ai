# IPL Analytics ChatBot - Modern UI with Bottom Navigation
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

# Modern styling with bottom navigation ready
st.markdown("""
    <style>
    .main {
        padding-top: 0.5rem;
        padding-bottom: 120px;
    }
    
    /* Bottom Navigation Bar */
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
    }
    
    .stButton > button:hover {
        background-color: #e0e1e3;
        border-color: #556b82;
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
    }
    
    @media (max-width: 480px) {
        .main {
            padding-left: 4px !important;
            padding-right: 4px !important;
        }
        
        h1 {
            font-size: 20px !important;
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

# Initialize session state
if "current_page" not in st.session_state:
    st.session_state.current_page = "chatbot"

# Header
st.markdown("""
    <div style="text-align: center; padding: 10px 0 20px 0;">
        <h1 style="margin: 0;">🏏 IPL Analytics AI</h1>
        <p style="margin: 0; color: #888; font-size: 13px;">Cricket Intelligence Powered by AI</p>
    </div>
""", unsafe_allow_html=True)

st.divider()

# Navigation buttons
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

# Page routing
page = st.session_state.current_page

# ============ CHATBOT PAGE ============
if page == "chatbot":
    st.markdown("### 💬 Ask me anything about IPL Cricket")
    st.markdown("*Get instant AI insights on player stats, records, and trends*")
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
                    placeholder="e.g., 'kohli statistics'",
                    key="chatbot_input",
                    label_visibility="collapsed"
                )
            with col2:
                search_btn = st.button("🔍", key="search_btn", use_container_width=True)
            
            st.info("💡 **Try asking all these capabilities**: Player stats • Records & Rankings • Head-to-Head • Recent Form • Team Performance • Specific Filters")
            
            if search_btn and user_query:
                st.divider()
                with st.spinner("🔍 Analyzing..."):
                    response = chatbot.get_response(user_query)
                st.markdown(response)
                
        except Exception as e:
            st.error(f"❌ Error: {str(e)[:100]}")

# ============ PROFILES PAGE ============
elif page == "profiles":
    st.markdown("### 📊 Player & Team Statistics")
    st.markdown("*Browse IPL player and team data*")
    st.markdown("")
    
    all_batters = loader.deliveries_df['batter'].unique()
    all_bowlers = loader.deliveries_df['bowler'].unique()
    all_players = sorted(set(all_batters).union(set(all_bowlers)))
    all_teams = sorted(set(
        list(loader.matches_df['team1'].unique()) + 
        list(loader.matches_df['team2'].unique())
    ))
    
    prof_type = st.radio("Select Type", ["🏏 Players", "🏆 Teams"], horizontal=True, key="prof_type")
    st.divider()
    
    if prof_type == "🏏 Players":
        player = st.selectbox("Select Player", all_players, key="sel_player")
        if player:
            stats = stats_engine.get_player_stats(player)
            
            col1, col2 = st.columns(2)
            
            if stats.get('batting'):
                with col1:
                    st.markdown("**Batting Stats**")
                    batting = stats['batting']
                    batting_df = pd.DataFrame({
                        'Stat': ['Matches', 'Runs', 'Average', 'Strike Rate', '50s', '100s'],
                        'Value': [
                            batting.get('matches', 0),
                            batting.get('runs', 0),
                            f"{batting.get('average', 0):.2f}",
                            f"{batting.get('strike_rate', 0):.2f}",
                            batting.get('fifties', 0),
                            batting.get('centuries', 0),
                        ]
                    })
                    st.dataframe(batting_df, use_container_width=True, hide_index=True)
            
            if stats.get('bowling'):
                with col2:
                    st.markdown("**Bowling Stats**")
                    bowling = stats['bowling']
                    bowling_df = pd.DataFrame({
                        'Stat': ['Matches', 'Wickets', 'Economy', 'Average', 'Best'],
                        'Value': [
                            bowling.get('matches', 0),
                            bowling.get('wickets', 0),
                            f"{bowling.get('economy', 0):.2f}",
                            f"{bowling.get('average', 0):.2f}",
                            bowling.get('best_figures', '—'),
                        ]
                    })
                    st.dataframe(bowling_df, use_container_width=True, hide_index=True)
    
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

# ============ COMPARE PAGE ============
elif page == "compare":
    st.markdown("### ⚔️ Head-to-Head Comparison")
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
    
    if st.button("📊 Compare", key="compare_btn", use_container_width=True):
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

# ============ TRENDS PAGE ============
elif page == "trends":
    st.markdown("### 📈 Recent Form & Trends")
    st.markdown("*Track player performance over recent matches*")
    st.markdown("")
    
    all_batters = loader.deliveries_df['batter'].unique()
    all_bowlers = loader.deliveries_df['bowler'].unique()
    all_players = sorted(set(all_batters).union(set(all_bowlers)))
    
    player = st.selectbox("Select Player", all_players, key="trend_player")
    
    if player:
        st.markdown(f"**Recent Form - {player}**")
        recent = stats_engine.get_last_n_matches(player, n=10)
        
        if recent is not None and not recent.empty:
            st.dataframe(recent, use_container_width=True)
        else:
            st.info("No recent match data available.")

# Footer
st.divider()
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("🏏 IPL Analytics AI")
with col2:
    st.caption("Powered by Streamlit + OpenAI")
with col3:
    st.caption("1,169 matches | 278K+ deliveries")

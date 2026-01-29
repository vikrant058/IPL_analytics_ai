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

# Custom styling - CricMetric-inspired with muted colors
st.markdown("""
    <style>
    .main {
        padding-top: 1rem;
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
    
    /* Section headers */
    .section-header {
        padding: 15px 0;
        border-bottom: 2px solid #e8eaed;
        margin-bottom: 20px;
        margin-top: 10px;
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
    
    /* Comparison section */
    .h2h-container {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 8px;
        border: 1px solid #e8eaed;
        margin-top: 15px;
    }
    
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
    ["Chat & Analytics", "Profiles"],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")
st.sidebar.caption("📊 IPL: 1,169 matches | 278K+ deliveries")

# Main content based on page
if page == "Chat & Analytics":
    st.title("🏏 Cricket Analytics")
    st.markdown("*Powered by AI • IPL Data Intelligence*")
    st.divider()
    
    # Create a section selector for better organization
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("💬 Chatbot", key="nav_chatbot", use_container_width=True):
            st.session_state.active_section = "chatbot"
            st.rerun()
    
    with col2:
        if st.button("⚡ Compare", key="nav_h2h", use_container_width=True):
            st.session_state.active_section = "h2h"
            st.rerun()
    
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
        st.markdown("### Ask me anything about IPL")
        
        # Info cards for query types
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class="stat-card">
                <div class="stat-card-title">📊 Player Stats</div>
                <div class="stat-card-subtitle">Get detailed career statistics for any player</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="stat-card">
                <div class="stat-card-title">⚔️ Head-to-Head</div>
                <div class="stat-card-subtitle">Compare any two players directly</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="stat-card">
                <div class="stat-card-title">📈 Trends</div>
                <div class="stat-card-subtitle">Analyze performance over time</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("")
        
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
                        placeholder="e.g., 'kohli vs bumrah in powerplay'",
                        key="chatbot_input",
                        label_visibility="collapsed"
                    )
                
                with col2:
                    search_btn = st.button("🔍 Search", key="search_btn", use_container_width=True)
                
                # Quick query suggestions - Expanded with functional examples
                st.markdown("**Popular Queries:**")
                
                # Row 1
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    if st.button("📊 Kohli Stats", key="q1", use_container_width=True):
                        user_query = "virat kohli statistics"
                        search_btn = True
                with col2:
                    if st.button("⚡ Bumrah", key="q2", use_container_width=True):
                        user_query = "jasprit bumrah bowling"
                        search_btn = True
                with col3:
                    if st.button("⚔️ Kohli vs Bumrah", key="q3", use_container_width=True):
                        user_query = "virat kohli vs jasprit bumrah"
                        search_btn = True
                with col4:
                    if st.button("🏃 Hardik Vs Rashid", key="q4", use_container_width=True):
                        user_query = "hardik pandya vs rashid khan"
                        search_btn = True
                
                # Row 2
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    if st.button("� Kohli Powerplay", key="q5", use_container_width=True):
                        user_query = "kohli in powerplay"
                        search_btn = True
                with col2:
                    if st.button("🎯 Bumrah Death", key="q6", use_container_width=True):
                        user_query = "bumrah in death overs"
                        search_btn = True
                with col3:
                    if st.button("🏏 Dhoni vs MI", key="q7", use_container_width=True):
                        user_query = "ms dhoni vs mumbai indians"
                        search_btn = True
                with col4:
                    if st.button("⚡ Rohit vs Spin", key="q8", use_container_width=True):
                        user_query = "rohit sharma vs spin bowlers"
                        search_btn = True
                
                # Row 3
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    if st.button("⚔️ Kohli vs Pace", key="q9", use_container_width=True):
                        user_query = "kohli vs pace bowlers"
                        search_btn = True
                with col2:
                    if st.button("💥 Bumrah vs CSK", key="q10", use_container_width=True):
                        user_query = "bumrah vs csk"
                        search_btn = True
                with col3:
                    if st.button("🎪 Suryakumar Powerplay", key="q11", use_container_width=True):
                        user_query = "suryakumar yadav in powerplay"
                        search_btn = True
                with col4:
                    if st.button("🧿 Kuldeep vs MI", key="q12", use_container_width=True):
                        user_query = "kuldeep yadav vs mumbai indians"
                        search_btn = True
                
                # Process query
                if search_btn and user_query:
                    st.divider()
                    with st.spinner("🔍 Analyzing..."):
                        response = chatbot.get_response(user_query)
                    
                    # Split response into sections for side-by-side display
                    if "🏏 **Batting Stats**" in response and "🎳 **Bowling Stats**" in response:
                        # Extract batting and bowling sections
                        batting_start = response.find("🏏 **Batting Stats**")
                        bowling_start = response.find("🎳 **Bowling Stats**")
                        breakdown_start = response.find("**BREAKDOWN")
                        
                        # Get header (before batting stats)
                        header = response[:batting_start].strip()
                        
                        # Get batting section
                        if bowling_start > batting_start:
                            batting_section = response[batting_start:bowling_start].strip()
                        else:
                            batting_section = response[batting_start:breakdown_start if breakdown_start > 0 else len(response)].strip()
                        
                        # Get bowling section
                        if breakdown_start > bowling_start:
                            bowling_section = response[bowling_start:breakdown_start].strip()
                            breakdown_section = response[breakdown_start:].strip()
                        else:
                            bowling_section = response[bowling_start:].strip()
                            breakdown_section = ""
                        
                        # Display header
                        if header:
                            st.markdown(header)
                        
                        # Display batting and bowling side by side
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(batting_section)
                        with col2:
                            st.markdown(bowling_section)
                        
                        # Display breakdown if exists
                        if breakdown_section:
                            st.markdown(breakdown_section)
                    else:
                        # Single stat type or no stats, display normally
                        st.markdown(response)
                
            except Exception as e:
                st.error(f"❌ Error initializing chatbot: {str(e)[:100]}")
                st.info("Make sure your OpenAI API key is valid.")
    
    elif active_section == "h2h":
        # Head-to-Head Comparison section
        st.markdown("### Compare Two Players")
        st.markdown("*Select any two players to see their head-to-head statistics*")
        
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
            
            # Batter vs Bowler case
            elif result.get('type') == 'batter_vs_bowler':
                st.markdown(f"### {player1} vs {player2}")
                
                batter = result['batter']['player']
                bowler = result['bowler']['player']
                batter_info = result['batter']
                bowler_info = result['bowler']
                
                # Head-to-head matchup visualization with cards
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"""
                    <div class="h2h-player-card">
                        <div class="h2h-player-name">🏏 {batter}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.metric("Balls Faced", result['deliveries_faced'], delta=f"vs {bowler}")
                        st.metric("Strike Rate", f"{batter_info['sr_vs_bowler']:.2f}")
                    with col_b:
                        st.metric("Runs", batter_info['runs_vs_bowler'])
                        st.metric("Dismissals", batter_info['dismissals_vs_bowler'])
                
                with col2:
                    st.markdown(f"""
                    <div class="h2h-player-card">
                        <div class="h2h-player-name">⚡ {bowler}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.metric("Balls Bowled", bowler_info['balls_bowled_to_batter'], delta=f"to {batter}")
                        st.metric("Economy", f"{bowler_info['economy_vs_batter']:.2f}")
                    with col_b:
                        st.metric("Runs Conceded", bowler_info['runs_conceded_to_batter'])
                        st.metric("Wickets", bowler_info['wickets_vs_batter'])
                
                st.divider()
                
                # Head-to-head stats table
                st.markdown("**Detailed Head-to-Head Statistics**")
                h2h_data = {
                    'Metric': ['Deliveries', 'Runs', 'SR/Economy', 'Dismissals/Wickets'],
                    batter: [
                        result['deliveries_faced'],
                        batter_info['runs_vs_bowler'],
                        f"{batter_info['sr_vs_bowler']:.2f}",
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
                        st.markdown(f"""
                        <div class="success">
                        ✅ {batter} HAS ADVANTAGE vs this bowler
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="warning">
                        ⚠️ {batter} AT DISADVANTAGE vs this bowler
                        </div>
                        """, unsafe_allow_html=True)
                
                with col2:
                    if analysis['bowler_advantage'] == 'Yes':
                        st.markdown(f"""
                        <div class="success">
                        ✅ {bowler} HAS ADVANTAGE vs this batter
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="warning">
                        ⚠️ {bowler} AT DISADVANTAGE vs this batter
                        </div>
                        """, unsafe_allow_html=True)
            
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

elif page == "Profiles":
    st.title("Data & Analytics")
    st.markdown("*Player & Team Statistics with Filters*")
    st.divider()
    
    # Section selector
    col1, col2, col3 = st.columns([1, 1, 3])
    
    with col1:
        if st.button("🏏 Players", key="nav_player", use_container_width=True):
            st.session_state.data_section = "player"
            st.rerun()
    
    with col2:
        if st.button("🏆 Teams", key="nav_team", use_container_width=True):
            st.session_state.data_section = "team"
            st.rerun()
    
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
        # Player Profile with Filters
        st.markdown("### Player Statistics")
        player_name = st.selectbox("Select Player", all_players, key="profile_player")
        
        st.divider()
        
        # Filters Section
        st.markdown("**Filters**")
        filter_cols = st.columns(5)
        
        with filter_cols[0]:
            season_filter = st.selectbox(
                "Season",
                ["All"] + sorted([str(y) for y in range(2008, 2025)]),
                key="season_filter"
            )
        
        with filter_cols[1]:
            opposition = st.selectbox(
                "Opposition",
                ["All"] + all_teams,
                key="opposition_filter"
            )
        
        with filter_cols[2]:
            match_phase = st.selectbox(
                "Match Phase",
                ["All", "Powerplay", "Middle Overs", "Death Overs"],
                key="match_phase"
            )
        
        with filter_cols[3]:
            home_away = st.selectbox(
                "Home/Away",
                ["All", "Home", "Away"],
                key="home_away"
            )
        
        with filter_cols[4]:
            ground = st.selectbox(
                "Ground",
                ["All"] + sorted(loader.matches_df['venue'].unique().tolist()),
                key="ground_filter"
            )
        
        st.markdown("")
        
        if player_name:
            # Apply filters for stats retrieval
            filters = {}
            if season_filter != "All":
                filters['season'] = season_filter
            if opposition != "All":
                filters['opposition_team'] = opposition
            if match_phase != "All":
                filters['match_phase'] = match_phase.lower().replace(" ", "_")
            if home_away != "All":
                filters['home_away'] = home_away.lower()
            if ground != "All":
                filters['ground'] = ground
            
            stats = stats_engine.get_player_stats(player_name)
            
            # Display batting and bowling stats side by side
            col1, col2 = st.columns(2)

            
            if stats.get('batting'):
                batting = stats['batting']
                with col1:
                    st.markdown("**Batting Statistics**")
                    
                    batting_data = {
                        'Stat': ['Matches', 'Innings', 'Runs', 'Average', 'Strike Rate', '50s', '100s', '4s', '6s', 'Highest'],
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
                        ]
                    }
                    
                    st.dataframe(pd.DataFrame(batting_data), use_container_width=True, hide_index=True)
            
            if stats.get('bowling'):
                bowling = stats['bowling']
                with col2:
                    st.markdown("**Bowling Statistics**")
                    
                    bowling_data = {
                        'Stat': ['Matches', 'Innings', 'Wickets', 'Runs', 'Economy', 'Average', 'Overs', 'Best Figures', '4W Hauls', 'Maidens'],
                        'Value': [
                            bowling.get('matches', 0),
                            bowling.get('innings', 0),
                            bowling.get('wickets', 0),
                            bowling.get('runs_conceded', 0),
                            f"{bowling.get('economy', 0):.2f}",
                            f"{bowling.get('average', 0):.2f}",
                            bowling.get('overs', '—'),
                            bowling.get('best_figures', '—'),
                            bowling.get('four_wickets', 0),
                            bowling.get('maiden_overs', 0)
                        ]
                    }
                    
                    st.dataframe(pd.DataFrame(bowling_data), use_container_width=True, hide_index=True)
            
            # View type selector for top performers
            st.markdown("**View Top Performers:**")
            perf_type = st.radio("Select Type", ["Batsmen", "Bowlers"], horizontal=True, key="perf_type")
            
            # Top performers section below main stats
            st.divider()
            st.markdown("### Top Performers")
            
            if perf_type == "Batsmen":
                st.markdown("**Top Batsmen (Overall)**")
                # Get top batsmen by calculating from stats - loop through ALL batters, not just first 50
                batsmen_stats = []
                for batter in all_batters:  # Check all batters in dataset
                    batter_stats = stats_engine.get_player_stats(batter)
                    if batter_stats.get('batting', {}).get('runs', 0) > 0:
                        batsmen_stats.append({
                            'Player': batter,
                            'Matches': int(batter_stats['batting'].get('matches', 0)),
                            'Innings': int(batter_stats['batting'].get('innings', 0)),
                            'Runs': int(batter_stats['batting'].get('runs', 0)),
                            'Avg': round(batter_stats['batting'].get('average', 0), 2),
                            'SR': round(batter_stats['batting'].get('strike_rate', 0), 2),
                            '50s': int(batter_stats['batting'].get('fifties', 0)),
                            '100s': int(batter_stats['batting'].get('centuries', 0)),
                            'HS': batter_stats['batting'].get('highest_score', 0)
                        })
                
                if batsmen_stats:
                    top_batsmen_df = pd.DataFrame(batsmen_stats).sort_values('Runs', ascending=False).head(10)
                    st.dataframe(top_batsmen_df, use_container_width=True, hide_index=True)
            
            elif perf_type == "Bowlers":
                st.markdown("**Top Bowlers (Overall)**")
                # Get top bowlers by calculating from stats - loop through ALL bowlers, not just first 50
                bowler_stats = []
                for bowler in all_bowlers:  # Check all bowlers in dataset
                    bowler_info = stats_engine.get_player_stats(bowler)
                    if bowler_info.get('bowling', {}).get('wickets', 0) > 0:
                        bowler_stats.append({
                            'Player': bowler,
                            'Matches': int(bowler_info['bowling'].get('matches', 0)),
                            'Innings': int(bowler_info['bowling'].get('innings', 0)),
                            'Wickets': int(bowler_info['bowling'].get('wickets', 0)),
                            'Runs': int(bowler_info['bowling'].get('runs_conceded', 0)),
                            'Economy': round(bowler_info['bowling'].get('economy', 0), 2),
                            'Avg': round(bowler_info['bowling'].get('average', 0), 2),
                            'Best': bowler_info['bowling'].get('best_figures', '—'),
                            '4W': int(bowler_info['bowling'].get('four_wickets', 0))
                        })
                
                if bowler_stats:
                    top_bowlers_df = pd.DataFrame(bowler_stats).sort_values('Wickets', ascending=False).head(10)
                    st.dataframe(top_bowlers_df, use_container_width=True, hide_index=True)
    
    elif data_section == "team":
        # Team Profile with Filters
        col1, col2 = st.columns([2, 1.5], gap="large")
        
        with col1:
            st.markdown("### Team Statistics")
            team = st.selectbox("Select Team", all_teams, key="profile_team")
        
        with col2:
            st.markdown("### League Stats")
        
        st.divider()
        
        # Filters Section
        st.markdown("**Filters**")
        filter_cols = st.columns(4)
        
        with filter_cols[0]:
            venue_filter = st.text_input("Venue (optional)", key="venue_filter")
        
        with filter_cols[1]:
            year_start = st.number_input("From Year", min_value=2008, max_value=2024, value=2008, key="year_start")
        
        with filter_cols[2]:
            year_end = st.number_input("To Year", min_value=2008, max_value=2024, value=2024, key="year_end")
        
        with filter_cols[3]:
            opposition = st.selectbox(
                "vs Specific Team",
                ["All"] + [t for t in all_teams if t != team],
                key="vs_team_filter"
            )
        
        st.markdown("")
        
        if team:
            team_stats = stats_engine.get_team_stats(team)
            
            st.markdown("**Team Summary**")
            
            # Display team stats in table format
            team_data = {
                'Metric': ['Matches', 'Wins', 'Losses', 'Win Rate', 'Win Percentage'],
                'Value': [
                    team_stats.get('matches', 0),
                    team_stats.get('wins', 0),
                    team_stats.get('matches', 0) - team_stats.get('wins', 0),
                    f"{team_stats.get('win_rate', 0):.2f}",
                    f"{team_stats.get('win_percentage', 0):.1f}%",
                ]
            }
            
            st.dataframe(pd.DataFrame(team_data), use_container_width=True, hide_index=True)
            
            st.markdown("")
            
            # Team performance trend
            trend = ai_engine.get_trend_analysis(team)
            if 'trend' in trend:
                st.markdown("**Performance by Year**")
                
                trend_data = trend['trend']
                
                # Show trend data as table
                trend_table = pd.DataFrame({
                    'Year': sorted(trend_data.keys()),
                    'Wins': [trend_data[year] for year in sorted(trend_data.keys())]
                })
                
                st.dataframe(trend_table, use_container_width=True, hide_index=True)
        
        # League stats sidebar
        with col2:
            st.markdown("**League Standings**")
            # Get all teams by wins
            team_records = []
            for t in all_teams:
                t_stats = stats_engine.get_team_stats(t)
                team_records.append({
                    'Team': t,
                    'Matches': t_stats.get('matches', 0),
                    'Wins': t_stats.get('wins', 0),
                    'Win%': t_stats.get('win_percentage', 0)
                })
            
            standings_df = pd.DataFrame(team_records).sort_values('Wins', ascending=False)
            for idx, row in standings_df.head(8).iterrows():
                st.caption(f"{idx+1}. {row['Team']}: {int(row['Wins'])} wins")

# Footer
st.divider()
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("🏏 IPL Analytics AI")
with col2:
    st.caption("Powered by Streamlit + OpenAI")
with col3:
    st.caption(f"Data: 1,169 matches | 278K+ deliveries")

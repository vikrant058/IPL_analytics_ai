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
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 15px;
        border-radius: 8px;
        color: white;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
    }
    h1, h2, h3 {
        color: #2c3e50;
    }
    .stButton > button {
        border-radius: 5px;
        border: 1px solid #667eea;
        color: white;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .stDataFrame {
        font-size: 12px;
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
    ["🤖 Chatbot & H2H", "👥 Profiles"]
)

# Main content based on page
if page == "🤖 Chatbot & H2H":
    st.title("🤖 AI Chatbot & Head-to-Head Comparison")

if page == "🤖 Chatbot & H2H":
    # Tab layout for chatbot and H2H within the same page
    tab1, tab2 = st.tabs(["💬 AI Chatbot", "⚡ Head-to-Head"])
    
    # Get all players and teams for H2H
    all_players = sorted(set(
        list(loader.deliveries_df['batter'].unique()) + 
        list(loader.deliveries_df['bowler'].unique())
    ))
    
    with tab1:
    # AI Chatbot section
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
    
    with tab2:
        # Head-to-Head Comparison section
        st.markdown("Compare any two players to see their performance metrics.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            player1 = st.selectbox("Select Player 1", all_players, key="h2h_player1")
        
        with col2:
            player2 = st.selectbox("Select Player 2", [p for p in all_players if p != player1], key="h2h_player2")
        
        if st.button("📊 Compare", key="h2h_compare_btn", use_container_width=True):
            st.divider()
            
            # Let AI engine auto-detect and handle everything
            result = ai_engine.get_player_head_to_head(player1, player2)
            
            if 'error' in result:
                st.error(f"❌ {result['error']}")
            
            # Batter vs Bowler case
            elif result.get('type') == 'batter_vs_bowler':
                st.success(f"🎯 **{player1} vs {player2} (Batter vs Bowler)**")
                
                batter = result['batter']['player']
                bowler = result['bowler']['player']
                batter_info = result['batter']
                bowler_info = result['bowler']
                
                # Head-to-head stats in compact format
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
                
                # Advantage analysis
                analysis = result['analysis']
                col1, col2 = st.columns(2)
                
                with col1:
                    if analysis['batter_advantage'] == 'Yes':
                        st.success(f"✅ **{batter}** has advantage (SR: {batter_info['sr_vs_bowler']:.1f}%)")
                    else:
                        st.warning(f"⚠️ **{batter}** at disadvantage (SR: {batter_info['sr_vs_bowler']:.1f}%)")
                
                with col2:
                    if analysis['bowler_advantage'] == 'Yes':
                        st.success(f"✅ **{bowler}** has advantage (Economy: {bowler_info['economy_vs_batter']:.2f})")
                    else:
                        st.warning(f"⚠️ **{bowler}** at disadvantage (Economy: {bowler_info['economy_vs_batter']:.2f})")
            
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

elif page == "👥 Profiles":
    st.markdown("Explore detailed profiles for individual players and teams.")
    
    tab1, tab2 = st.tabs(["🏏 Player Profiles", "🏆 Team Profiles"])
    
    # Get all players and teams
    all_batters = loader.deliveries_df['batter'].unique()
    all_bowlers = loader.deliveries_df['bowler'].unique()
    all_players = sorted(set(all_batters).union(set(all_bowlers)))
    all_teams = sorted(set(
        list(loader.matches_df['team1'].unique()) + 
        list(loader.matches_df['team2'].unique())
    ))
    
    with tab1:
        # Player Profile
        st.subheader("Player Profile")
        player_name = st.selectbox("👤 Select Player", all_players, key="profile_player")
        
        if player_name:
            stats = stats_engine.get_player_stats(player_name)
            
            # Display batting stats if available
            if stats.get('batting'):
                batting = stats['batting']
                st.markdown("#### 🏏 Batting Stats")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Runs", batting.get('runs', 0))
                with col2:
                    st.metric("Average", f"{batting.get('average', 0):.2f}")
                with col3:
                    st.metric("Strike Rate", f"{batting.get('strike_rate', 0):.2f}")
                with col4:
                    st.metric("Matches", batting.get('matches', 0))
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("50s", batting.get('fifties', 0))
                with col2:
                    st.metric("100s", batting.get('centuries', 0))
                with col3:
                    st.metric("4s", batting.get('fours', 0))
                with col4:
                    st.metric("6s", batting.get('sixes', 0))
            
            # Display bowling stats if available
            if stats.get('bowling'):
                bowling = stats['bowling']
                st.markdown("#### ⚡ Bowling Stats")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Wickets", bowling.get('wickets', 0))
                with col2:
                    st.metric("Economy", f"{bowling.get('economy', 0):.2f}")
                with col3:
                    st.metric("Average", f"{bowling.get('average', 0):.2f}")
                with col4:
                    st.metric("Matches", bowling.get('matches', 0))
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Best Figures", bowling.get('best_figures', '—'))
                with col2:
                    st.metric("4W Hauls", bowling.get('four_wickets', 0))
                with col3:
                    st.metric("Maiden Overs", bowling.get('maiden_overs', 0))
                with col4:
                    st.metric("Overs", bowling.get('overs', '—'))
    
    with tab2:
        # Team Profile
        st.subheader("Team Profile")
        team = st.selectbox("🏏 Select Team", all_teams, key="profile_team")
        
        if team:
            team_stats = stats_engine.get_team_stats(team)
            
            st.markdown(f"#### 📊 {team} Summary")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Matches", team_stats.get('matches', 0))
            with col2:
                st.metric("Wins", team_stats.get('wins', 0))
            with col3:
                st.metric("Win Rate", f"{team_stats.get('win_percentage', 0):.1f}%")
            with col4:
                st.metric("Losses", team_stats.get('matches', 0) - team_stats.get('wins', 0))
            
            st.divider()
            
            # Team trend
            trend = ai_engine.get_trend_analysis(team)
            if 'trend' in trend:
                st.markdown("#### Performance Trend")
                trend_data = trend['trend']
                fig = px.line(x=list(trend_data.keys()), y=list(trend_data.values()),
                             labels={'x': 'Year', 'y': 'Wins'},
                             title=f"{team} Wins by Year",
                             markers=True)
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            st.divider()
            
            # Top performers in team
            st.markdown("#### Top Team Performers")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Top Batsmen**")
                top_batsmen = stats_engine.get_top_performers('batting', 5)
                if top_batsmen:
                    df = pd.DataFrame(top_batsmen)
                    st.dataframe(df, use_container_width=True, hide_index=True)
            
            with col2:
                st.markdown("**Top Bowlers**")
                top_bowlers = stats_engine.get_top_performers('bowling', 5)
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

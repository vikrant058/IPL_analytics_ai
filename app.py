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

@st.cache_resource
def init_chatbot(api_key):
    """Initialize chatbot once and cache it"""
    loader_cached, _, _ = load_data()
    return CricketChatbot(loader_cached.matches_df, loader_cached.deliveries_df, api_key)

@st.cache_data
def get_all_players_and_teams():
    """Cache player and team lists"""
    loader_cached, _, _ = load_data()
    all_batters = loader_cached.deliveries_df['batter'].unique()
    all_bowlers = loader_cached.deliveries_df['bowler'].unique()
    all_players = sorted(set(all_batters).union(set(all_bowlers)))
    all_teams_raw = sorted(set(
        list(loader_cached.matches_df['team1'].unique()) + 
        list(loader_cached.matches_df['team2'].unique())
    ))
    
    # Normalize team names to avoid duplicates
    normalized_teams = []
    seen = set()
    for team in all_teams_raw:
        if team == 'Royal Challengers Bangalore':
            normalized_team = 'Royal Challengers Bengaluru'
        else:
            normalized_team = team
        
        if normalized_team not in seen:
            normalized_teams.append(normalized_team)
            seen.add(normalized_team)
    
    return all_players, sorted(normalized_teams)

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
            # Use cached chatbot instance
            chatbot = init_chatbot(api_key)
            
            col1, col2 = st.columns([4, 1])
            with col1:
                user_query = st.text_input(
                    "Your query:",
                    placeholder="e.g., 'CSK' • 'kohli' • 'kohli vs bumrah' • 'top scorers 2024'",
                    key="chatbot_input",
                    label_visibility="collapsed"
                )
            with col2:
                search_btn = st.button("Search", key="search_btn", use_container_width=True)
            
            st.info("💡 **Try asking**: Team (CSK, MI) • Player (Kohli, Bumrah) • Stats • Records • Rankings • Head-to-Head • Recent Form • Team Performance")
            
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
    
    # Use cached player and team data
    all_players, all_teams = get_all_players_and_teams()
    
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
    
    # Use cached player data
    all_players, _ = get_all_players_and_teams()
    
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
    
    # Use cached player data
    all_players, _ = get_all_players_and_teams()
    
    player = st.selectbox("Select Player", all_players, key="trend_player")
    
    if player:
        st.markdown(f"**Recent Form - {player}**")
        recent = stats_engine.get_last_n_matches(player, n=10)
        
        # Handle both DataFrame and list returns
        if recent is not None and (isinstance(recent, list) and len(recent) > 0 or (hasattr(recent, 'empty') and not recent.empty)):
            if isinstance(recent, list):
                matches_data = recent
            else:
                matches_data = recent.to_dict('records') if hasattr(recent, 'to_dict') else recent
            
            if matches_data:
                # Extract data for visualizations
                dates = [m.get('date', 'N/A') for m in matches_data]
                batting_runs = [m.get('batting', {}).get('runs', 0) for m in matches_data]
                bowling_wickets = [m.get('bowling', {}).get('wickets', 0) for m in matches_data]
                batting_balls = [m.get('batting', {}).get('balls', 0) for m in matches_data]
                dismissals = [1 if m.get('batting', {}).get('dismissed', False) else 0 for m in matches_data]
                
                # Calculate metrics
                total_runs = sum(batting_runs)
                total_balls = sum(batting_balls)
                total_wickets = sum(bowling_wickets)
                out_count = sum(dismissals)
                not_out_count = len([x for x in dismissals if x == 0])
                avg_runs = total_runs / len(batting_runs) if batting_runs else 0
                strike_rate = (total_runs / total_balls * 100) if total_balls > 0 else 0
                
                # Form status
                if avg_runs >= 30:
                    form_status = "🔥 Excellent Form"
                    form_color = "green"
                elif avg_runs >= 20:
                    form_status = "✅ Good Form"
                    form_color = "blue"
                elif avg_runs >= 10:
                    form_status = "⚠️ Average Form"
                    form_color = "orange"
                else:
                    form_status = "❌ Poor Form"
                    form_color = "red"
                
                # Display key metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Avg Runs (Last 10)", f"{avg_runs:.1f}")
                with col2:
                    st.metric("Total Runs", f"{total_runs}")
                with col3:
                    st.metric("Strike Rate", f"{strike_rate:.1f}%")
                with col4:
                    st.metric("Form Status", form_status)
                
                st.divider()
                
                # Visualizations
                col_chart1, col_chart2 = st.columns(2)
                
                # Chart 1: Runs trend
                with col_chart1:
                    st.markdown("#### 📊 Runs Trend (Last 10 Matches)")
                    import plotly.graph_objects as go
                    fig_runs = go.Figure()
                    fig_runs.add_trace(go.Scatter(
                        x=list(range(len(batting_runs))),
                        y=batting_runs,
                        mode='lines+markers',
                        name='Runs',
                        line=dict(color='#1f77b4', width=3),
                        marker=dict(size=8),
                        hovertemplate='Match %{x+1}: %{y} runs<extra></extra>'
                    ))
                    fig_runs.add_hline(y=avg_runs, line_dash="dash", line_color="green", 
                                      annotation_text=f"Avg: {avg_runs:.1f}", annotation_position="right")
                    fig_runs.update_layout(
                        title="",
                        xaxis_title="Match (Most Recent →)",
                        yaxis_title="Runs Scored",
                        hovermode='x unified',
                        height=350,
                        margin=dict(l=0, r=0, t=0, b=0)
                    )
                    st.plotly_chart(fig_runs, use_container_width=True)
                
                # Chart 2: Out vs Not Out pie
                with col_chart2:
                    st.markdown("#### 🎯 Dismissal Status (Last 10)")
                    fig_pie = go.Figure(data=[go.Pie(
                        labels=['Out', 'Not Out'],
                        values=[out_count, not_out_count],
                        marker=dict(colors=['#ff7f0e', '#2ca02c']),
                        hovertemplate='<b>%{label}</b><br>%{value} matches<extra></extra>'
                    )])
                    fig_pie.update_layout(
                        title="",
                        height=350,
                        margin=dict(l=0, r=0, t=0, b=0)
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                st.divider()
                
                # Additional charts for bowlers
                if total_wickets > 0:
                    col_chart3, col_chart4 = st.columns(2)
                    
                    with col_chart3:
                        st.markdown("#### 🎳 Bowling Wickets Trend")
                        fig_wkts = go.Figure()
                        fig_wkts.add_trace(go.Bar(
                            x=list(range(len(bowling_wickets))),
                            y=bowling_wickets,
                            name='Wickets',
                            marker=dict(color='#d62728'),
                            hovertemplate='Match %{x+1}: %{y} wickets<extra></extra>'
                        ))
                        fig_wkts.update_layout(
                            title="",
                            xaxis_title="Match (Most Recent →)",
                            yaxis_title="Wickets",
                            height=350,
                            margin=dict(l=0, r=0, t=0, b=0),
                            showlegend=False
                        )
                        st.plotly_chart(fig_wkts, use_container_width=True)
                    
                    with col_chart4:
                        st.markdown("#### 📈 Bowling Stats Summary")
                        st.metric("Total Wickets (Last 10)", total_wickets)
                        avg_wickets = total_wickets / len(bowling_wickets) if bowling_wickets else 0
                        st.metric("Avg Wickets/Match", f"{avg_wickets:.2f}")
                        
                        total_bowl_runs = sum([m.get('bowling', {}).get('runs', 0) for m in matches_data])
                        total_bowl_balls = sum([m.get('bowling', {}).get('balls', 0) for m in matches_data])
                        economy = (total_bowl_runs / (total_bowl_balls / 6)) if total_bowl_balls > 0 else 0
                        st.metric("Economy Rate", f"{economy:.2f}")
                
                st.divider()
                
                # Detailed match-by-match table
                st.markdown("#### 📋 Match-by-Match Details")
                
                detailed_data = []
                for i, match in enumerate(matches_data):
                    detailed_data.append({
                        'Match': i + 1,
                        'Date': match.get('date', 'N/A'),
                        'vs': match.get('opposition', 'N/A'),
                        'Runs': match.get('batting', {}).get('runs', 0),
                        'Balls': match.get('batting', {}).get('balls', 0),
                        'SR': f"{(match.get('batting', {}).get('runs', 0) / match.get('batting', {}).get('balls', 1) * 100):.1f}" if match.get('batting', {}).get('balls', 0) > 0 else '-',
                        'Status': '❌ Out' if match.get('batting', {}).get('dismissed', False) else '✅ Not Out',
                        'Wickets': match.get('bowling', {}).get('wickets', 0),
                        'Runs Conceded': match.get('bowling', {}).get('runs', 0)
                    })
                
                df_details = pd.DataFrame(detailed_data)
                st.dataframe(df_details, use_container_width=True, hide_index=True)
                st.session_state.show_output = True
        else:
            st.info("No recent match data available.")

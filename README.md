# 🏏 IPL Analytics AI Platform

An advanced AI-powered cricket analytics platform for Indian Premier League (IPL) data analysis, predictions, and insights (2008-2024).

## 🚀 Features

### Data Analytics
- **Player Analysis**: Comprehensive batting and bowling statistics
- **Team Performance**: Win rates, trends, and head-to-head matchups
- **Venue Statistics**: Performance analysis across different venues
- **Historical Data**: 16+ years of IPL data (2008-2024)

### AI Predictions
- **Match Outcome Prediction**: Predict match winners using team statistics
- **Player Performance Prediction**: Forecast individual player performance
- **Trend Analysis**: Analyze team performance trends over time
- **Head-to-Head Statistics**: Historical comparison between any two teams

### Insights & Visualizations
- Interactive dashboards with Plotly visualizations
- Real-time analytics and statistics
- AI-generated insights from historical data
- RESTful API endpoints for integration

## 📁 Project Structure

```
IPL_analytics_ai/
├── data_loader.py          # Load and preprocess CSV data
├── stats_engine.py         # Calculate cricket statistics
├── ai_engine.py           # AI predictions and insights
├── models.py              # Pydantic models for API validation
├── api.py                 # FastAPI backend endpoints
├── app.py                 # Streamlit frontend application
├── matches.csv            # IPL matches data (2008-2024)
├── deliveries.csv         # Ball-by-ball delivery data
├── requirement.txt        # Python dependencies
└── README.md             # This file
```

## 🛠️ Installation

### 1. Prerequisites
- Python 3.8+
- pip or conda

### 2. Install Dependencies

```bash
# Navigate to project directory
cd /Users/vikrant/Desktop/IPL_analytics_ai

# Install required packages
pip install -r requirement.txt
```

## 📊 Usage

### Option 1: Run Streamlit App (Interactive Dashboard)

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501` with:
- 📈 Overview dashboard
- 🎯 Player analysis tools
- 👥 Team performance metrics
- 🔮 Match predictions
- 📊 Head-to-head comparisons
- 💡 AI-generated insights

### Option 2: Run FastAPI Server (REST API)

```bash
python api.py
```

The API will run on `http://localhost:8000`

**API Documentation**: Visit `http://localhost:8000/docs` for interactive Swagger documentation

### Option 3: Use as a Library

```python
from data_loader import IPLDataLoader
from stats_engine import StatsEngine
from ai_engine import AIEngine

# Load data
loader = IPLDataLoader()
matches, deliveries = loader.load_data()
matches, deliveries = loader.preprocess_data()

# Initialize engines
stats_engine = StatsEngine(matches, deliveries)
ai_engine = AIEngine(matches, deliveries)

# Get player stats
player_stats = stats_engine.get_player_stats("Virat Kohli")
print(player_stats)

# Predict match winner
prediction = ai_engine.predict_match_winner("Mumbai Indians", "Chennai Super Kings")
print(prediction)
```

## 📡 API Endpoints

### Dataset Information
- `GET /api/dataset/summary` - Dataset summary statistics
- `GET /api/dataset/teams` - List all teams
- `GET /api/dataset/years` - List all years

### Player Statistics
- `GET /api/player/{player_name}` - Get player statistics
- `GET /api/players/top?category=batting&limit=10` - Top players
- `GET /api/player/{player_name}/form?last_n_matches=10` - Recent form

### Team Statistics
- `GET /api/team/{team_name}` - Team statistics
- `GET /api/team/{team_name}/matches` - Team's all matches

### Predictions
- `GET /api/predict/match?team1=X&team2=Y` - Match winner prediction
- `GET /api/predict/player/{player_name}?match_type=batting` - Player performance prediction

### Analysis
- `GET /api/analysis/trend/{team_name}` - Team trend analysis
- `GET /api/analysis/head-to-head?team1=X&team2=Y` - Head-to-head stats
- `GET /api/insights` - AI-generated insights

## 📚 Module Documentation

### DataLoader
```python
loader = IPLDataLoader()
matches_df, deliveries_df = loader.load_data()
matches_df, deliveries_df = loader.preprocess_data()

# Get specific data
matches_2024 = loader.get_matches_by_year(2024)
mi_matches = loader.get_team_matches("Mumbai Indians")
```

### StatsEngine
```python
stats = StatsEngine(matches_df, deliveries_df)

# Player statistics
kohli_stats = stats.get_player_stats("Virat Kohli")
top_batsmen = stats.get_top_performers('batting', 10)
bumrah_form = stats.get_player_form("Jasprit Bumrah", last_n_matches=15)

# Team statistics
mi_stats = stats.get_team_stats("Mumbai Indians")
```

### AIEngine
```python
ai = AIEngine(matches_df, deliveries_df)

# Predictions
match_pred = ai.predict_match_winner("Mumbai Indians", "Chennai Super Kings")
player_pred = ai.predict_player_performance("Virat Kohli", match_type="batting")

# Analysis
trend = ai.get_trend_analysis("Mumbai Indians")
h2h = ai.get_head_to_head("Mumbai Indians", "Chennai Super Kings")
insights = ai.get_insights()
```

## 📊 Data Format

### matches.csv
Contains match-level information:
- `id`, `season`, `city`, `date`, `match_type`, `player_of_match`, `venue`
- `team1`, `team2`, `toss_winner`, `toss_decision`
- `winner`, `result`, `result_margin`, `target_runs`, `target_overs`
- `super_over`, `method`, `umpire1`, `umpire2`, `year`

### deliveries.csv
Contains ball-by-ball delivery information:
- `match_id`, `inning`, `batting_team`, `bowling_team`
- `over`, `ball`, `batter`, `bowler`, `non_striker`
- `batsman_runs`, `extra_runs`, `total_runs`, `extras_type`
- `is_wicket`, `player_dismissed`, `dismissal_kind`, `fielder`

## 🔮 AI/ML Capabilities

- **Win Rate Analysis**: Team performance prediction based on historical win rates
- **Player Form Tracking**: Monitor recent performance trends
- **Head-to-Head Analysis**: Historical matchup statistics
- **Trend Prediction**: Team performance trajectory analysis
- **Feature Engineering**: Automated calculation of team and player performance metrics

## 🎯 Future Enhancements

- [ ] Machine learning models (XGBoost, Neural Networks)
- [ ] Real-time match prediction during games
- [ ] Player injury impact analysis
- [ ] Weather and pitch condition integration
- [ ] Advanced visualization dashboards
- [ ] Mobile app integration
- [ ] PostgreSQL database backend
- [ ] Docker containerization

## 📈 Performance

- Loads and processes 1000+ matches with 100k+ deliveries
- Fast data querying and aggregation
- Real-time predictions and analysis
- Sub-second API response times

## 🤝 Contributing

Feel free to fork this project and submit pull requests for any improvements!

## 📝 License

This project is open source and available under the MIT License.

## 👨‍💻 Author

Created with 🏏 for cricket analytics enthusiasts

## 📧 Support

For issues, questions, or suggestions, feel free to reach out!

---

**Last Updated**: January 2026
**Data Range**: 2008-2024 IPL Seasons
**Total Matches Analyzed**: 900+

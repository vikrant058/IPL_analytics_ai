from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, List
from data_loader import IPLDataLoader
from stats_engine import StatsEngine
from ai_engine import AIEngine
from models import PlayerStats, TeamStats, APIResponse
import uvicorn

# Initialize FastAPI app
app = FastAPI(
    title="IPL Analytics AI Platform",
    description="AI-powered cricket analytics for Indian Premier League",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize data and engines globally
loader = IPLDataLoader()
matches_df, deliveries_df = loader.load_data()
matches_df, deliveries_df = loader.preprocess_data()

stats_engine = StatsEngine(matches_df, deliveries_df)
ai_engine = AIEngine(matches_df, deliveries_df)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "IPL Analytics AI Platform is running"
    }

# Dataset endpoints
@app.get("/api/dataset/summary")
async def get_dataset_summary():
    """Get summary statistics of the dataset"""
    summary = loader.get_summary_stats()
    return {
        "status": "success",
        "data": summary
    }

@app.get("/api/dataset/teams")
async def get_all_teams():
    """Get all teams in the dataset"""
    teams = sorted(set(
        list(matches_df['team1'].unique()) + 
        list(matches_df['team2'].unique())
    ))
    return {
        "status": "success",
        "data": {"teams": teams, "count": len(teams)}
    }

@app.get("/api/dataset/years")
async def get_all_years():
    """Get all years covered in the dataset"""
    years = sorted(matches_df['year'].unique())
    return {
        "status": "success",
        "data": {"years": years.tolist(), "count": len(years)}
    }

# Player statistics endpoints
@app.get("/api/player/{player_name}")
async def get_player_stats(player_name: str):
    """Get comprehensive statistics for a player"""
    try:
        stats = stats_engine.get_player_stats(player_name)
        if not stats or (not stats.get('batting') and not stats.get('bowling')):
            raise HTTPException(status_code=404, detail=f"Player {player_name} not found")
        
        return {
            "status": "success",
            "data": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/players/top")
async def get_top_players(
    category: str = Query("batting", enum=["batting", "bowling"]),
    limit: int = Query(10, ge=1, le=50)
):
    """Get top players by category"""
    try:
        players = stats_engine.get_top_performers(category, limit)
        return {
            "status": "success",
            "data": {
                "category": category,
                "players": players,
                "count": len(players)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/player/{player_name}/form")
async def get_player_form(
    player_name: str,
    last_n_matches: int = Query(10, ge=1, le=30)
):
    """Get recent form of a player"""
    try:
        form = stats_engine.get_player_form(player_name, last_n_matches)
        return {
            "status": "success",
            "data": form
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Team statistics endpoints
@app.get("/api/team/{team_name}")
async def get_team_stats(team_name: str):
    """Get statistics for a team"""
    try:
        stats = stats_engine.get_team_stats(team_name)
        return {
            "status": "success",
            "data": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/team/{team_name}/matches")
async def get_team_matches(team_name: str):
    """Get all matches for a team"""
    try:
        matches = loader.get_team_matches(team_name)
        return {
            "status": "success",
            "data": {
                "team": team_name,
                "total_matches": len(matches),
                "matches": matches[['id', 'date', 'team1', 'team2', 'winner', 'venue']].to_dict('records')
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Predictions endpoints
@app.get("/api/predict/match")
async def predict_match(team1: str, team2: str):
    """Predict match outcome between two teams"""
    try:
        prediction = ai_engine.predict_match_winner(team1, team2)
        return {
            "status": "success",
            "data": prediction
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/predict/player/{player_name}")
async def predict_player(
    player_name: str,
    match_type: str = Query("batting", enum=["batting", "bowling"])
):
    """Predict player performance"""
    try:
        prediction = ai_engine.predict_player_performance(player_name, match_type)
        return {
            "status": "success",
            "data": prediction
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Analysis endpoints
@app.get("/api/analysis/trend/{team_name}")
async def get_trend(team_name: str):
    """Get performance trend for a team"""
    try:
        trend = ai_engine.get_trend_analysis(team_name)
        return {
            "status": "success",
            "data": trend
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analysis/head-to-head")
async def get_h2h(team1: str, team2: str):
    """Get head-to-head statistics between teams"""
    try:
        h2h = ai_engine.get_head_to_head(team1, team2)
        return {
            "status": "success",
            "data": h2h
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/insights")
async def get_insights():
    """Get AI-generated insights"""
    try:
        insights = ai_engine.get_insights()
        return {
            "status": "success",
            "data": {"insights": insights}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Error handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": str(exc)
        }
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime

# Match Models
class Match(BaseModel):
    id: int
    season: str
    city: str
    date: datetime
    match_type: str
    player_of_match: str
    venue: str
    team1: str
    team2: str
    toss_winner: str
    toss_decision: str
    winner: Optional[str]
    result: str
    result_margin: Optional[float]
    year: int

class Delivery(BaseModel):
    match_id: int
    inning: int
    batting_team: str
    bowling_team: str
    over: int
    ball: int
    batter: str
    bowler: str
    batsman_runs: int
    extra_runs: int
    total_runs: int
    is_wicket: int

# Player Stats Models
class BattingStats(BaseModel):
    matches: int
    runs: int
    balls: int
    average: float
    strike_rate: float
    highest_score: int

class BowlingStats(BaseModel):
    matches: int
    wickets: int
    runs_conceded: int
    balls: int
    overs: float
    economy: float

class PlayerStats(BaseModel):
    player: str
    batting: Optional[Dict] = {}
    bowling: Optional[Dict] = {}

class TeamStats(BaseModel):
    team: str
    matches: int
    wins: int
    win_percentage: float

class VenueStats(BaseModel):
    venue: str
    total_matches: int
    seasons: int

# Prediction Models
class MatchPrediction(BaseModel):
    match_id: int
    team1: str
    team2: str
    predicted_winner: str
    confidence: float
    key_factors: List[str]

class PlayerPerformancePrediction(BaseModel):
    player: str
    match_id: int
    predicted_runs: int
    predicted_wickets: int
    confidence: float

class APIResponse(BaseModel):
    status: str
    message: str
    data: Optional[Dict] = None
    timestamp: datetime = datetime.now()

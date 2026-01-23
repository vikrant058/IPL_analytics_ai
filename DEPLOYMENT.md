# 🏏 IPL Analytics AI - Deployment & Production Guide

## Table of Contents
1. [Quick Start](#quick-start)
2. [Local Development](#local-development)
3. [Production Deployment](#production-deployment)
4. [API Documentation](#api-documentation)
5. [Troubleshooting](#troubleshooting)

## Quick Start

### Verify Installation
```bash
cd /Users/vikrant/Desktop/IPL_analytics_ai
python3 test_suite.py
```

Expected output: All 8 tests should pass ✅

### Option 1: Streamlit Dashboard (Recommended for Analytics)

```bash
streamlit run app.py
```

- Opens at `http://localhost:8501`
- Interactive dashboards and visualizations
- Real-time analysis and predictions
- No API knowledge required

### Option 2: FastAPI Backend (Recommended for Integration)

```bash
python3 api.py
```

- API runs at `http://localhost:8000`
- Interactive API docs at `http://localhost:8000/docs`
- REST endpoints for programmatic access
- CORS enabled for cross-origin requests

### Option 3: Python Library (Recommended for Development)

```python
from data_loader import IPLDataLoader
from ai_engine import AIEngine

loader = IPLDataLoader()
matches, deliveries = loader.load_data()
ai = AIEngine(matches, deliveries)

# Make predictions
prediction = ai.predict_match_winner("MI", "CSK")
```

## Local Development

### Environment Setup

```bash
# Create virtual environment (optional)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirement.txt

# Run tests
python3 test_suite.py

# View examples
python3 examples.py
```

### Project Structure

```
IPL_analytics_ai/
├── data_loader.py       # Data loading & preprocessing
├── stats_engine.py      # Cricket statistics calculations
├── ai_engine.py         # AI predictions & insights
├── models.py            # Pydantic data models
├── api.py              # FastAPI REST endpoints
├── app.py              # Streamlit web dashboard
├── examples.py         # Usage examples
├── test_suite.py       # Validation tests
├── config.py           # Configuration file
├── matches.csv         # Match data (1095 matches)
├── deliveries.csv      # Ball-by-ball data (260K+ deliveries)
└── README.md           # Documentation
```

### Key Modules

#### DataLoader
```python
loader = IPLDataLoader()
matches, deliveries = loader.load_data()
matches, deliveries = loader.preprocess_data()

# Querying methods
matches_2024 = loader.get_matches_by_year(2024)
mi_matches = loader.get_team_matches("Mumbai Indians")
```

#### StatsEngine
```python
stats = StatsEngine(matches, deliveries)

# Player statistics
kohli_stats = stats.get_player_stats("Virat Kohli")
top_batsmen = stats.get_top_performers('batting', 10)
recent_form = stats.get_player_form("Virat Kohli")

# Team statistics
mi_stats = stats.get_team_stats("Mumbai Indians")
```

#### AIEngine
```python
ai = AIEngine(matches, deliveries)

# Predictions
match_pred = ai.predict_match_winner("MI", "CSK")
player_pred = ai.predict_player_performance("Virat Kohli")

# Analysis
trend = ai.get_trend_analysis("Mumbai Indians")
h2h = ai.get_head_to_head("MI", "CSK")
insights = ai.get_insights()
```

## Production Deployment

### Using Gunicorn (FastAPI)

```bash
# Install gunicorn
pip install gunicorn

# Run with multiple workers
gunicorn api:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Using Docker

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirement.txt .
RUN pip install --no-cache-dir -r requirement.txt

COPY . .

EXPOSE 8000

CMD ["python3", "api.py"]
```

Build and run:
```bash
docker build -t ipl-analytics .
docker run -p 8000:8000 ipl-analytics
```

### Using Docker Compose

Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - LOG_LEVEL=INFO
    volumes:
      - ./matches.csv:/app/matches.csv
      - ./deliveries.csv:/app/deliveries.csv
  
  streamlit:
    build: .
    ports:
      - "8501:8501"
    command: streamlit run app.py
    volumes:
      - ./matches.csv:/app/matches.csv
      - ./deliveries.csv:/app/deliveries.csv
```

Run:
```bash
docker-compose up
```

### Production Environment Variables

Create `.env` file:
```
DEBUG=False
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
```

### Nginx Configuration (Reverse Proxy)

```nginx
upstream api {
    server localhost:8000;
}

server {
    listen 80;
    server_name api.example.com;

    location / {
        proxy_pass http://api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## API Documentation

### Base URL
```
http://localhost:8000
```

### Authentication
Currently no authentication required. Add security as needed.

### Core Endpoints

#### Dataset Information
```
GET /api/dataset/summary
GET /api/dataset/teams
GET /api/dataset/years
```

#### Player Endpoints
```
GET /api/player/{player_name}
GET /api/players/top?category=batting&limit=10
GET /api/player/{player_name}/form?last_n_matches=10
```

#### Team Endpoints
```
GET /api/team/{team_name}
GET /api/team/{team_name}/matches
```

#### Predictions
```
GET /api/predict/match?team1=MI&team2=CSK
GET /api/predict/player/{player_name}?match_type=batting
```

#### Analysis
```
GET /api/analysis/trend/{team_name}
GET /api/analysis/head-to-head?team1=MI&team2=CSK
GET /api/insights
```

### Example API Calls

```bash
# Get dataset summary
curl http://localhost:8000/api/dataset/summary

# Get player stats
curl "http://localhost:8000/api/player/Virat%20Kohli"

# Get top batsmen
curl "http://localhost:8000/api/players/top?category=batting&limit=5"

# Predict match winner
curl "http://localhost:8000/api/predict/match?team1=Mumbai%20Indians&team2=Chennai%20Super%20Kings"

# Get head-to-head stats
curl "http://localhost:8000/api/analysis/head-to-head?team1=Mumbai%20Indians&team2=Kolkata%20Knight%20Riders"
```

## Troubleshooting

### Issue: "No module named 'pandas'"
**Solution**: Install dependencies
```bash
pip install -r requirement.txt
```

### Issue: "Port 8000 already in use"
**Solution**: Use different port
```bash
python3 api.py --port 8001
```
Or kill existing process:
```bash
lsof -ti:8000 | xargs kill -9
```

### Issue: "CSV file not found"
**Solution**: Ensure CSV files are in the correct directory
```bash
ls -la *.csv
```

### Issue: "Memory error with large dataset"
**Solution**: Use data sampling or pagination
```python
# Load only recent matches
matches = loader.get_matches_by_year(2023)
```

### Issue: Streamlit crashes on load
**Solution**: Clear cache and restart
```bash
rm -rf ~/.streamlit/cache
streamlit run app.py --logger.level=debug
```

### Issue: API returns 500 errors
**Solution**: Check logs and verify data
```bash
# Run test suite
python3 test_suite.py

# Check API logs
tail -f ipl_analytics.log
```

## Performance Optimization

### Caching
- Data loading is cached with `@st.cache_resource` in Streamlit
- API responses can be cached with Redis (future enhancement)

### Database Migration (Future)
For production, consider migrating from CSV to:
- PostgreSQL
- MongoDB
- SQLite with indexing

### Code Optimization
- Use pandas vectorization instead of loops
- Implement batch processing
- Add query optimization for large datasets

## Security Considerations

1. **Add Authentication**
```python
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.get("/api/protected")
async def protected(credentials: HTTPAuthCredentials = Depends(security)):
    # Validate token
    pass
```

2. **Add Rate Limiting**
```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)
@app.get("/api/data")
@limiter.limit("100/minute")
async def limited_endpoint():
    pass
```

3. **CORS Configuration**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific origins
    allow_credentials=True,
    allow_methods=["GET"],  # Specific methods
    allow_headers=["*"],
)
```

4. **Environment Variables**
- Store sensitive data in `.env`
- Never commit `.env` to git
- Use `python-dotenv` for loading

## Monitoring & Logging

### Application Logging
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    filename='ipl_analytics.log',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Health Check Endpoint
The platform includes a built-in health check:
```bash
curl http://localhost:8000/health
```

## Next Steps

1. **Add Database**: Migrate from CSV to PostgreSQL
2. **Add Authentication**: Implement JWT tokens
3. **Add Caching**: Implement Redis for performance
4. **Add Testing**: Write unit and integration tests
5. **Add Monitoring**: Set up Prometheus/Grafana
6. **Add CI/CD**: GitHub Actions workflow
7. **Add Documentation**: Generate API documentation

## Support & Issues

For issues:
1. Check troubleshooting section above
2. Run `python3 test_suite.py`
3. Review logs in `ipl_analytics.log`
4. Check API documentation at `http://localhost:8000/docs`

---

**Last Updated**: January 2026
**Version**: 1.0.0
**Status**: Production Ready ✅

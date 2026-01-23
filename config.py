# IPL Analytics AI Platform - Configuration File

# Data Settings
DATA_DIR = "."
MATCHES_CSV = "matches.csv"
DELIVERIES_CSV = "deliveries.csv"

# API Settings
API_HOST = "0.0.0.0"
API_PORT = 8000
API_WORKERS = 4
DEBUG = False

# Streamlit Settings
STREAMLIT_HOST = "localhost"
STREAMLIT_PORT = 8501

# Analysis Settings
DEFAULT_TOP_N = 10
DEFAULT_RECENT_MATCHES = 10

# Prediction Settings
PREDICTION_CONFIDENCE_THRESHOLD = 0.5
MIN_MATCHES_FOR_PREDICTION = 5

# Model Settings
RANDOM_SEED = 42
TEST_SIZE = 0.2

# Caching
CACHE_ENABLED = True
CACHE_TTL = 3600  # seconds

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = "ipl_analytics.log"

# Performance
MAX_PLAYERS_TO_LOAD = None  # None = all
MAX_MATCHES_TO_LOAD = None  # None = all

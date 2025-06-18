# BoardGameArena Configuration Template
# Copy this file to config.py and update with your values

# Test URLs for initial development
TEST_URLS = [
    "https://boardgamearena.com/archive/replay/REPLAY_ID/?table=TABLE_ID&player=PLAYER_ID&comments=PLAYER_ID"
]

# URL templates for constructing BGA URLs
TABLE_URL_TEMPLATE = "https://boardgamearena.com/table?table={table_id}"
# NOTE: REPLAY_URL_TEMPLATE is now used as fallback only. The scraper dynamically extracts 
# the correct version number from the gamereview page for each game.
REPLAY_URL_TEMPLATE = "https://boardgamearena.com/archive/replay/250604-1037/?table={table_id}&player={player_id}&comments={player_id}"


# Request settings
REQUEST_DELAY = 2  # Seconds between requests
TIMEOUT = 30  # Request timeout in seconds
MAX_RETRIES = 3  # Maximum retry attempts

# Data storage paths
RAW_DATA_DIR = 'data/raw'
PROCESSED_DATA_DIR = 'data/processed'
URLS_DIR = 'data/urls'

# Chrome settings
CHROME_PATH = r'C:\Program Files\Google\Chrome\Application\chrome.exe'  # Update this path
CHROMEDRIVER_PATH = r'C:\path\to\chromedriver.exe'  # Update this path - download from https://chromedriver.chromium.org/

# BGA Login Credentials
BGA_EMAIL = "your_email@example.com"
BGA_PASSWORD = "your_password"

# Leaderboard settings
TERRAFORMING_MARS_GAME_ID = 1924
DEFAULT_PLAYER_COUNT = 100
TOP_N_PLAYERS = 100
SEASON_21_FILTER = True  # Only get Season 21 games
TWO_PLAYER_ONLY = True   # Only get 2-player games

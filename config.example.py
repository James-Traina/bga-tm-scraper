# BoardGameArena Configuration Template
# Copy this file to config.py and update with your values

# Test URLs for initial development
TEST_URLS = [
    "https://boardgamearena.com/archive/replay/REPLAY_ID/?table=TABLE_ID&player=PLAYER_ID&comments=PLAYER_ID"
]

# Authentication - Extract these from your browser's developer tools
# After logging into BoardGameArena, go to Developer Tools > Application > Cookies
# Copy the values for these cookies:
BGA_COOKIES = {
    'PHPSESSID': 'your_session_id_here',
    'TournoiEnLigne_sso_id': 'your_sso_id_here',
    'TournoiEnLigne_sso_user': 'your_sso_user_here',
    'TournoiEnLigneid': 'your_id_here',
    'TournoiEnLigneidt': 'your_idt_here',
    'TournoiEnLignetk': 'your_tk_here',
    'TournoiEnLignetkt': 'your_tkt_here'
}

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

# Leaderboard settings (for future use)
TOP_N_PLAYERS = 100
SEASON_21_FILTER = True  # Only get Season 21 games
TWO_PLAYER_ONLY = True   # Only get 2-player games

# BoardGameArena Configuration
# Copy this file to config.py and update with your values

# Test URLs for initial development
TEST_URLS = [
    "https://boardgamearena.com/archive/replay/250604-1037/?table=688769496&player=86296239&comments=86296239;"
]

# Authentication - Extract these from your browser's developer tools
# After logging into BoardGameArena, go to Developer Tools > Application > Cookies
# Copy the values for these cookies:
BGA_COOKIES = {
    'PHPSESSID': 'sbsphdtn228b6f7qbmjfpfpfv4',
    'TournoiEnLigne_sso_id': '90e1c553ba2dfce3f7be9e93c1652853',
    'TournoiEnLigne_sso_user': 'StrandedKnight%243%24hhstrand%40gmail.com',
    'TournoiEnLigneid': 'eEVInxOUKi9CLHW',
    'TournoiEnLigneidt': 'w82HUWmcccB8TS',
    'TournoiEnLignetk': 'iopuXUzN0kTOIrIjC4P3UTnZl4MQUCgG6KbxQUHwcDDnQaeGFkZjElv618YyDixJ',
    'TournoiEnLignetkt': 'NQJNO3WLXbCWfjfEkVAEpnr5YyHE9x5iPY10slxo2Y8d1fJtR63EZp7WwRTvRgvs'
}

# Request settings
REQUEST_DELAY = 2  # Seconds between requests
TIMEOUT = 30  # Request timeout in seconds
MAX_RETRIES = 3  # Maximum retry attempts

# Data storage paths
RAW_DATA_DIR = 'data/raw'
PROCESSED_DATA_DIR = 'data/processed'
URLS_DIR = 'data/urls'

# Chrome debug mode settings
CHROME_PATH = r'C:\Program Files\Google\Chrome\Application\chrome.exe'  # Update this path
CHROMEDRIVER_PATH = r'C:\Code\chromedriver-win64\chromedriver.exe'  # Update this path - download from https://chromedriver.chromium.org/

# Leaderboard settings (for future use)
TOP_N_PLAYERS = 100
SEASON_21_FILTER = True  # Only get Season 21 games
TWO_PLAYER_ONLY = True   # Only get 2-player games

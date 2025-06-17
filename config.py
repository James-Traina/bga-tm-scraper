# BoardGameArena Configuration
# Copy this file to config.py and update with your values

# Test table IDs for initial development
TEST_TABLE_IDS = [
    "672224577"  # Extracted from original replay URL
]

# URL templates for constructing BGA URLs
TABLE_URL_TEMPLATE = "https://boardgamearena.com/table?table={table_id}"
# NOTE: REPLAY_URL_TEMPLATE is now used as fallback only. The scraper dynamically extracts 
# the correct version number from the gamereview page for each game.
REPLAY_URL_TEMPLATE = "https://boardgamearena.com/archive/replay/250604-1037/?table={table_id}&player={player_id}&comments={player_id}"

# Legacy URLs (for migration reference)
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
REQUEST_DELAY = 1  # Seconds between requests
TIMEOUT = 30  # Request timeout in seconds
MAX_RETRIES = 3  # Maximum retry attempts

# Speed settings - choose your preferred speed profile
SPEED_PROFILE = "FAST"  # Options: "FAST", "NORMAL", "SAFE"

# Speed profiles configuration
SPEED_PROFILES = {
    "FAST": {
        "page_load_delay": 2,      # Seconds to wait after page navigation
        "click_delay": 0.3,        # Seconds between "See more" clicks
        "gamereview_delay": 2,     # Seconds to wait after loading gamereview page
        "element_wait_timeout": 5   # Max seconds to wait for elements
    },
    "NORMAL": {
        "page_load_delay": 3,
        "click_delay": 0.5,
        "gamereview_delay": 2.5,
        "element_wait_timeout": 8
    },
    "SAFE": {
        "page_load_delay": 5,      # Original conservative delays
        "click_delay": 1,
        "gamereview_delay": 3,
        "element_wait_timeout": 10
    }
}

# Get current speed settings
CURRENT_SPEED = SPEED_PROFILES.get(SPEED_PROFILE, SPEED_PROFILES["NORMAL"])

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

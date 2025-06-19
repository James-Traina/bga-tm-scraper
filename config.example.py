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

# Speed settings for scraping
# Choose one of the predefined speed profiles or create a custom one

# Speed profile options: "FAST", "NORMAL", "SLOW", "CUSTOM"
SPEED_PROFILE = "NORMAL"

# Predefined speed profiles
SPEED_PROFILES = {
    "FAST": {
        "page_load_delay": 2,
        "click_delay": 0.3,
        "gamereview_delay": 1.5,
        "element_wait_timeout": 5
    },
    "NORMAL": {
        "page_load_delay": 3,
        "click_delay": 0.5,
        "gamereview_delay": 2.5,
        "element_wait_timeout": 8
    },
    "SLOW": {
        "page_load_delay": 5,
        "click_delay": 1.0,
        "gamereview_delay": 4.0,
        "element_wait_timeout": 12
    },
    "CUSTOM": {
        "page_load_delay": 3,
        "click_delay": 0.5,
        "gamereview_delay": 2.5,
        "element_wait_timeout": 8
    }
}

# Current speed settings (automatically set based on SPEED_PROFILE)
CURRENT_SPEED = SPEED_PROFILES[SPEED_PROFILE]

# Speed setting descriptions:
# - page_load_delay: Time to wait after navigating to a page (seconds)
# - click_delay: Time to wait between clicks when auto-clicking "See more" (seconds)
# - gamereview_delay: Time to wait for gamereview page to load (seconds)
# - element_wait_timeout: Maximum time to wait for elements to appear (seconds)
#
# Recommendations:
# - Use FAST for reliable internet and powerful computers
# - Use NORMAL for typical setups (recommended for most users)
# - Use SLOW for slower internet or if you encounter timeout errors
# - Use CUSTOM and modify the values above if you need fine-tuned control

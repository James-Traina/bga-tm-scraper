# Terraforming Mars BGA Scraper

A Python CLI tool for scraping and parsing Terraforming Mars game replays from BoardGameArena.

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation & Setup](#installation--setup)
- [Quick Start](#quick-start)
- [CLI Commands](#cli-commands)
- [How It Works](#how-it-works)
- [Configuration](#configuration)
- [File Organization](#file-organization)
- [Usage Examples](#usage-examples)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Features

- **CLI Interface**: Clean command-based interface for all operations
- **Web Scraping**: Automated data collection from both replay and table pages
- **Player Game History**: Automatically scrape all table IDs from a player's game history
- **Arena Mode Detection**: Automatically identifies and filters Arena mode games
- **ELO Data Extraction**: Arena points, game rank, and rating changes for each player
- **Comprehensive Parsing**: Complete game state reconstruction with move-by-move parsing
- **Rich Data Extraction**: Players, corporations, cards, resources, terraforming parameters
- **Game State Tracking**: Full game progression from start to finish
- **Registry Management**: Tracks processed games to avoid duplicates
- **Smart Filtering**: Skip players with completed discovery automatically

## Requirements

### System Requirements
- **Python 3.7+**
- **Google Chrome browser** (latest version recommended)
- **ChromeDriver** (matching your Chrome version)
- **Windows/macOS/Linux** (tested on Windows 11)

### Python Dependencies
- `requests>=2.31.0` - HTTP requests
- `beautifulsoup4>=4.12.0` - HTML parsing
- `lxml>=4.9.0` - XML/HTML processing
- `selenium>=4.15.0` - Browser automation
- `psutil>=5.9.0` - System process management

## Installation & Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd bga-tm-scraper
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Setup ChromeDriver
1. Check your Chrome version: `chrome://version/`
2. Download matching ChromeDriver from https://chromedriver.chromium.org/
3. Extract to a folder (e.g., `C:\Code\chromedriver-win64\`)
4. Note the path to `chromedriver.exe`

### 4. Configure Settings
```bash
cp config.example.py config.py
```

Edit `config.py` and update:
- `CHROMEDRIVER_PATH`: Path to your ChromeDriver executable
- `CHROME_PATH`: Path to your Chrome browser (if not default)
- `BGA_EMAIL` and `BGA_PASSWORD`: Your BoardGameArena credentials
- Other settings as needed (see [Configuration](#configuration))

### 5. Verify Setup
```bash
# Check if everything is working
python main.py status
```

## Quick Start

### 1. Update Player Registry
```bash
# Get top 100 Arena players
python main.py update-players --count 100
```

### 2. Check Status
```bash
# See what's in the registry
python main.py status --detailed
```

### 3. Start Scraping
```bash
# Complete workflow for all players (tables + replays + parsing)
python main.py scrape-complete --all

# Or start with just table scraping to identify Arena games
python main.py scrape-tables --all
```

### 4. Parse Games
```bash
# Parse games that have been scraped
python main.py parse
```

## CLI Commands

The CLI provides six main commands for different operations:

### `scrape-tables` - Scrape table HTMLs only
Scrapes table pages to identify Arena mode games and extract basic information.

```bash
# Scrape tables for all players (updates player registry first)
python main.py scrape-tables --all --update-players

# Scrape tables for specific players
python main.py scrape-tables 12345678 87654321 11223344
```

**Options:**
- `--all, -a`: Process all players from the registry
- `--update-players`: Update player registry before processing
- `--retry-failed`: Include previously failed games

### `scrape-complete` - Full workflow (tables + replays + parsing)
Performs the complete workflow: scrapes tables, scrapes replays for Arena games, and parses them.

```bash
# Complete workflow for all players
python main.py scrape-complete --all --update-players

# Complete workflow for specific players
python main.py scrape-complete 12345678 87654321

# Retry failed games for specific players
python main.py scrape-complete 12345678 --retry-failed
```

**Options:**
- `--all, -a`: Process all players from the registry
- `--update-players`: Update player registry before processing
- `--retry-failed`: Include previously failed games

### `scrape-replays` - Scrape replays and parse (requires table HTMLs)
Scrapes replay pages and parses games that already have table HTML scraped.

```bash
# Process all games that need replay scraping
python main.py scrape-replays

# Process specific games (using composite keys)
python main.py scrape-replays 123456789:12345678 987654321:87654321
```

**Composite Key Format:** `table_id:player_perspective`
- Example: `123456789:12345678` means table ID 123456789 from player 12345678's perspective

### `parse` - Parse games only (requires both HTMLs)
Parses games that have both table and replay HTML files already scraped.

```bash
# Parse all games ready for parsing
python main.py parse

# Parse specific games
python main.py parse 123456789:12345678 987654321:87654321

# Reparse all games (including already parsed ones)
python main.py parse --reparse

# Reparse specific games
python main.py parse --reparse 123456789:12345678 987654321:87654321
```

**Options:**
- `--reparse`: Reparse already parsed games (overwrite existing JSON files)

### `update-players` - Update player registry
Updates the player registry with the latest Arena leaderboard data.

```bash
# Update with default number of players (from config)
python main.py update-players

# Update with specific number of top players
python main.py update-players --count 200
```

### `status` - Show registry status
Displays statistics about the current state of the games registry.

```bash
# Basic status
python main.py status

# Detailed status with breakdowns
python main.py status --detailed
```

## How It Works

### 1. Player Registry Management
- Fetches top Arena players from BoardGameArena leaderboards
- Maintains a registry of players to track (`data/registry/players.csv`)
- Updates player information periodically

### 2. Table Scraping
- Visits each player's game history page
- Automatically loads all games by clicking "See more"
- Extracts table IDs and basic game information
- Identifies Arena mode games using ELO data presence
- Stores raw HTML in `data/raw/{player_id}/table_{table_id}.html`

### 3. Replay Scraping
- For Arena mode games, scrapes detailed replay pages
- Uses browser automation to handle dynamic content
- Extracts complete game logs and player actions
- Stores replay HTML in `data/raw/{player_id}/replay_{table_id}.html`

### 4. Game Parsing
- Processes both table and replay HTML files
- Reconstructs complete game state move-by-move
- Extracts player data, cards, resources, terraforming parameters
- Combines ELO data from table pages with game data
- Exports structured JSON files to `data/parsed/{player_id}/game_{table_id}.json`

### 5. Registry Tracking
- Maintains `data/registry/games.csv` to track processing status
- Prevents duplicate processing
- Tracks scraping and parsing timestamps
- Handles version management for replay URLs

### 6. Smart Filtering
- Automatically skips players with completed discovery
- Checks for `complete_summary.json` files with `discovery_completed: true`
- Provides filtering statistics during processing

## Configuration

Key settings in `config.py`:

### Paths and Browser
```python
CHROMEDRIVER_PATH = r'C:\path\to\chromedriver.exe'
CHROME_PATH = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
```

### BGA Credentials
```python
BGA_EMAIL = "your_email@example.com"
BGA_PASSWORD = "your_password"
```

### Scraping Settings
```python
REQUEST_DELAY = 2  # Seconds between requests
TOP_N_PLAYERS = 1000  # Number of players to fetch
SEASON_21_FILTER = True  # Only Season 21 games
TWO_PLAYER_ONLY = True  # Only 2-player games
```

### Speed Profiles
Choose from predefined profiles or customize:
```python
SPEED_PROFILE = "NORMAL"  # Options: "FAST", "NORMAL", "SLOW", "CUSTOM"
```

## File Organization

```
bga-tm-scraper/
├── main.py                    # CLI entry point
├── config.py                  # Configuration settings
├── requirements.txt           # Python dependencies
├── bga_tm_scraper/           # Core modules
│   ├── scraper.py            # Web scraping logic
│   ├── parser.py             # Game parsing logic
│   ├── games_registry.py     # Registry management
│   ├── players_registry.py   # Player management
│   └── bga_session.py        # BGA session handling
├── data/
│   ├── raw/                  # Raw HTML files
│   │   └── {player_id}/
│   │       ├── table_{table_id}.html
│   │       └── replay_{table_id}.html
│   ├── parsed/               # Processed JSON files
│   │   └── {player_id}/
│   │       ├── game_{table_id}.json
│   │       └── complete_summary.json
│   └── registry/             # Registry files
│       ├── games.csv         # Games tracking
│       └── players.csv       # Players list
└── scraper.log              # Application logs
```

## Usage Examples

### Initial Setup Workflow
```bash
# 1. Update player registry with top 100 players
python main.py update-players --count 100

# 2. Check what's in the registry
python main.py status --detailed

# 3. Start with table scraping to identify Arena games
python main.py scrape-tables --all

# 4. Check progress
python main.py status

# 5. Run complete workflow for new data
python main.py scrape-complete --all
```

### Daily Maintenance
```bash
# Update players and run complete workflow
python main.py scrape-complete --all --update-players

# Or just parse games that are ready
python main.py parse

# Check progress
python main.py status --detailed
```

### Targeted Processing
```bash
# Process specific players
python main.py scrape-complete 12345678 87654321

# Process specific games that failed
python main.py scrape-replays 123456789:12345678 987654321:87654321

# Retry failed games for a player
python main.py scrape-complete 12345678 --retry-failed

# Reparse specific games
python main.py parse --reparse 123456789:12345678
```

### Sample Output Structure

The parser generates comprehensive JSON with:

```json
{
  "replay_id": "250604-1037",
  "game_date": "2025-06-16",
  "winner": "StrandedKnight",
  "players": {
    "86296239": {
      "player_name": "StrandedKnight",
      "corporation": "Cheung Shing Mars",
      "final_vp": 104,
      "cards_played": ["Great Aquifer", "Nuclear Power"],
      "milestones_claimed": ["Gardener", "Terraformer", "Builder"],
      "awards_funded": ["Landlord"],
      "elo_data": {
        "arena_points": 1754,
        "arena_points_change": 24,
        "game_rank": 453,
        "game_rank_change": -5
      }
    }
  },
  "moves": [
    {
      "move_number": 4,
      "player_name": "StrandedKnight",
      "action_type": "play_card",
      "card_played": "Great Aquifer",
      "resource_changes": {"TR": 1},
      "parameter_changes": {"oceans": 1},
      "game_state": {
        "generation": 1,
        "temperature": -30,
        "oxygen": 0,
        "oceans": 1
      }
    }
  ],
  "final_state": {
    "generation": 11,
    "temperature": -4,
    "oxygen": 14,
    "oceans": 6
  }
}
```

## Troubleshooting

### Common Issues

**ChromeDriver Issues**
- Ensure ChromeDriver version matches your Chrome browser
- Update `CHROMEDRIVER_PATH` in config.py
- Try downloading the latest ChromeDriver

**Login Problems**
- Verify BGA credentials in config.py
- Check if BGA requires 2FA (not currently supported)
- Try manual login in browser first

**Scraping Failures**
- Check internet connection
- Increase delays in speed profile settings
- Use `--retry-failed` flag to retry failed games
- Check `scraper.log` for detailed error messages

**Memory Issues**
- Process players in smaller batches
- Use specific player IDs instead of `--all`
- Restart the scraper periodically for large datasets

### Performance Tips

1. **Use `scrape-tables` first** to identify Arena games before full processing
2. **Process in batches** rather than all players at once
3. **Use `parse` command** to process games that are already scraped
4. **Check `status`** regularly to monitor progress
5. **Adjust speed profiles** based on your connection and BGA's response times

### Logging

- All operations are logged to `scraper.log`
- Use `--detailed` flag with status command for more information
- Check registry files for processing history

## License

This project is for educational and research purposes. Please respect BoardGameArena's terms of service and use responsibly.
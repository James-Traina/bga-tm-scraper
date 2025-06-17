# BGA Terraforming Mars Scraper

A comprehensive Python tool for scraping and parsing Terraforming Mars game replays from BoardGameArena with ELO tracking.

## Features

- **Enhanced Web scraping**: Automated data collection from both replay and table pages
- **Player Game History**: Automatically scrape all table IDs from a player's game history
- **ELO Data Extraction**: Arena points, game rank, and rating changes for each player
- **Comprehensive parsing**: Complete game state reconstruction with move-by-move analysis
- **Rich data extraction**: Players, corporations, cards, resources, terraforming parameters
- **Multiple output formats**: JSON export with structured game data including ELO information
- **Game state tracking**: Full game progression from start to finish

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Setup ChromeDriver

1. Download ChromeDriver from https://chromedriver.chromium.org/
2. Make sure the version matches your Chrome browser version
3. Extract to a folder (e.g., `C:\Code\chromedriver-win64\`)

### 3. Configure Settings

```bash
cp config.example.py config.py
```

Edit `config.py` and update:
- `CHROMEDRIVER_PATH`: Path to your ChromeDriver executable
- `TEST_TABLE_IDS`: List of table IDs to scrape (e.g., ["688769496"])

The scraper now works with table IDs instead of full replay URLs for enhanced functionality.

### 4. Run the Scraper

For individual games:
```bash
python main.py
```

For player game history:
```bash
python test_player_history.py
```

### 5. Parse Game Data

```bash
python test_parser.py
```

## Project Structure

```
bga-tm-scraper/
├── src/
│   ├── scraper.py          # Web scraping logic
│   ├── parser.py           # Comprehensive game parser
│   └── card_vp_database.py # Card VP calculations
├── data/
│   ├── raw/                # Raw HTML files
│   └── parsed/             # Processed game data
├── main.py                 # Scraper entry point
├── test_player_history.py  # Player game history scraper
├── test_parser.py          # Parser testing and demo
├── config.py               # Configuration settings
└── requirements.txt        # Python dependencies
```

## Player Game History Scraping

The scraper can now automatically collect all table IDs from a player's game history:

### How It Works
1. Navigate to a player's game history page
2. Automatically click "See more" until all games are loaded
3. Extract table IDs from the complete game list
4. Optionally scrape detailed data for all found games

### Usage
```bash
python test_player_history.py
```

The script will:
- Prompt for a player ID
- Open browser for manual login
- Automatically load all games by clicking "See more"
- Extract and save all table IDs
- Optionally scrape the first 5 games as a sample

### Features
- **Smart Detection**: Stops when "No more results" banner appears
- **Progress Tracking**: Shows how many games have been loaded
- **Safety Limits**: Maximum click limit to prevent infinite loops
- **Error Handling**: Robust error recovery and logging
- **Data Export**: Saves table IDs and scraping results to JSON files

## ELO Data Extraction

The enhanced scraper now extracts ELO information from game table pages:

### ELO Data Types
- **Arena Points**: Current season-specific ranking points
- **Arena Points Change**: Gain/loss from the specific game
- **Game Rank**: Overall ELO rating for the game
- **Game Rank Change**: ELO rating change from the game

### How It Works
1. Scraper fetches both table page (`/table?table=ID`) and replay page
2. Parser extracts ELO data from table page HTML structure
3. ELO information is merged with player data in the final JSON

## Parser Features

The new unified parser provides comprehensive game analysis:

### Data Extraction
- **Complete move log**: Every action with timestamps and details
- **Game state tracking**: Resources, production, and parameters after each move
- **Player data**: Corporations, cards played, milestones, awards
- **Terraforming progression**: Temperature, oxygen, and ocean changes
- **Victory point tracking**: Detailed VP breakdown and progression

### Action Classification
- `play_card`: Playing project cards with costs and effects
- `place_tile`: City, forest, and ocean tile placement
- `standard_project`: Standard project usage
- `claim_milestone`: Milestone achievements
- `fund_award`: Award funding
- `activate_card`: Card ability activations
- `convert_heat`: Heat to temperature conversion
- And more...

### Output Structure

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
      "cards_played": ["Great Aquifer", "Nuclear Power", ...],
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
        "oceans": 1,
        "player_resources": {...},
        "player_production": {...}
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

## Usage Examples

### Player Game History
```python
from src.scraper import TMScraper

scraper = TMScraper(chromedriver_path="path/to/chromedriver.exe")
scraper.start_browser()
scraper.login_to_bga()

# Get all table IDs for a player
table_ids = scraper.scrape_player_game_history("86296239")
print(f"Found {len(table_ids)} games")

# Scrape all games
results = scraper.scrape_multiple_tables_and_replays(table_ids)
```

### Basic Parsing
```python
from src.parser import Parser

parser = Parser()
game_data = parser.parse_complete_game(html_content, "game_id")
parser.export_to_json(game_data, "output.json")
```

### Analysis
```bash
# Run parser test
python test_parser.py

# Analyze parsed data
python test_parser.py analyze

# Scrape player history
python test_player_history.py
```

## Sample Output

From the test game (250604-1037):
- **Players**: 2 (petersenhauke vs StrandedKnight)
- **Winner**: StrandedKnight (104 VP vs 43 VP)
- **Duration**: 32 minutes, 11 generations
- **Total moves**: 288 moves parsed
- **Cards played**: 54 total
- **Final terraforming**: -4°C, 14% oxygen, 6 oceans

## Requirements

- Python 3.7+
- Chrome browser
- ChromeDriver
- Required Python packages (see requirements.txt)

## Authentication

The scraper uses manual login:
1. Browser opens to BoardGameArena
2. You log in manually in the browser
3. Press Enter in the terminal to continue
4. Scraper proceeds with authenticated session

## Notes

- You need to be logged into BoardGameArena for the scraper to access replay data
- The scraper uses Chrome in debug mode to maintain session state
- Large games may take several minutes to parse completely
- The parser achieves 99%+ accuracy in move classification and data extraction

## License

This project is for educational and research purposes. Please respect BoardGameArena's terms of service and use responsibly.

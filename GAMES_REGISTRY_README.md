# Master Games Registry System

The Master Games Registry is a centralized system that tracks all scraped games across all players to prevent duplicate scraping and maintain a comprehensive overview of all processed games.

## Overview

The registry system consists of:
- **Master Registry File**: `data/processed/master_games_registry.json` - Central database of all games
- **Games Registry Module**: `src/games_registry.py` - Python module for managing the registry
- **Registry Viewer**: `view_registry.py` - Utility script for viewing and managing registry data
- **Integrated Scraping**: Modified `test_player_history.py` with duplicate prevention

## Key Features

### 🚫 Duplicate Prevention
- Automatically checks if games have already been scraped before processing
- Skips duplicate games to save time and resources
- Shows clear statistics about new vs. already processed games

### 📊 Comprehensive Tracking
- Tracks game metadata: table_id, datetime information, players
- Records scraping success/failure status with error reasons
- Maintains audit trail of who scraped what and when

### 🔍 Easy Management
- View registry statistics and game lists
- Search for specific games by table ID
- Export registry data for analysis
- Failed game tracking for retry logic

## File Structure

```
data/processed/master_games_registry.json  # Main registry file
src/games_registry.py                      # Registry management module
view_registry.py                          # Registry viewer utility
test_player_history.py                    # Modified scraper with registry integration
```

## Registry Data Structure

The master registry file contains:

```json
{
  "metadata": {
    "created_at": "2025-06-18T15:02:51",
    "last_updated": "2025-06-18T15:02:51", 
    "total_games": 0,
    "description": "Master registry of all scraped games across all players"
  },
  "games": {
    "688771617": {
      "table_id": "688771617",
      "raw_datetime": "yesterday at 22:46",
      "parsed_datetime": "2025-06-16T22:46:00",
      "players": [
        {
          "player_id": "12345",
          "name": "PlayerName",
          "score": 85
        }
      ],
      "scraped_at": "2025-06-18T15:03:00",
      "scraped_successfully": true
    }
  }
}
```

## Usage

### Running the Scraper with Registry

The modified `test_player_history.py` now automatically:

1. **Loads the registry** at startup and shows current stats
2. **Filters duplicates** from the games found for a player
3. **Updates the registry** after each successful scrape/parse
4. **Saves the registry** at the end with updated stats

```bash
python test_player_history.py
```

Example output:
```
📋 Loading master games registry...

=== Master Games Registry Stats ===
Total games tracked: 45
Successfully scraped: 42
Failed scrapes: 3
Success rate: 93.3%

🔍 Checking for already scraped games...
⏭️  Found 12 games already in registry - skipping duplicates
📋 8 new games to process
```

### Viewing Registry Data

Use the `view_registry.py` utility to explore the registry:

```bash
# Show registry statistics
python view_registry.py stats

# List all successfully scraped games
python view_registry.py list

# Show failed games
python view_registry.py failed

# Search for a specific game
python view_registry.py search 688771617

# Export registry to JSON file
python view_registry.py export my_games.json
```

### Programmatic Access

You can also use the registry in your own scripts:

```python
from src.games_registry import GamesRegistry

# Initialize registry
registry = GamesRegistry()

# Check if a game is already scraped
if registry.is_game_scraped("688771617"):
    print("Game already processed")

# Filter new games from a list
new_games = registry.filter_new_games(games_list)

# Add a successfully scraped game
registry.add_game(
    table_id="688771617",
    raw_datetime="yesterday at 22:46", 
    parsed_datetime="2025-06-16T22:46:00",
    players=[{"name": "Player1", "score": 85}],
    scraped_by_player="96014413"
)

# Save changes
registry.save_registry()
```

## Benefits

### ⏱️ Time Savings
- No more re-scraping the same games
- Faster execution when running multiple scraping sessions
- Efficient resource utilization

### 📈 Better Organization  
- Single source of truth for all scraped games
- Easy to see what's been processed across all players
- Clear audit trail and statistics

### 🔧 Improved Reliability
- Failed games are tracked for potential retry
- Prevents data loss from interrupted scraping sessions
- Maintains data integrity across runs

### 📊 Analytics Ready
- Export functionality for data analysis
- Rich metadata for each game
- Player information preserved for cross-referencing

## Migration from Old System

The new system is backward compatible. Existing scraped games in `data/parsed/` are not automatically added to the registry, but:

1. **New scrapes** will be tracked in the registry going forward
2. **Duplicate detection** only applies to games in the registry
3. **Old games** can be manually added to the registry if needed

## Registry Maintenance

The registry is designed to be self-maintaining:
- **Automatic updates** during scraping
- **Metadata refresh** on each save
- **Statistics calculation** in real-time
- **Error handling** for corrupted registry files

## Troubleshooting

### Registry File Issues
If the registry file becomes corrupted, it will automatically recreate an empty registry and continue working.

### Performance
The registry is optimized for fast lookups and can handle thousands of games efficiently.

### Backup
Consider backing up `data/processed/master_games_registry.json` periodically to preserve your scraping history.

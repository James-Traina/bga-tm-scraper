# Players Registry System

This system maintains a CSV registry of Arena Leaderboard players for Terraforming Mars on BoardGameArena (BGA).

## Overview

The players registry tracks:
- Player ID (BGA unique identifier)
- Player Name
- Country
- Current Arena Rank
- Last Updated timestamp

## Files Structure

```
src/
├── bga_session.py          # BGA login and session management
├── leaderboard_scraper.py  # Fetch leaderboard data from BGA
└── players_registry.py     # CSV registry management

update_players.py           # Main script to update registry
test_players_registry.py    # Test script for validation
data/processed/players.csv  # CSV registry file (created automatically)
```

## Configuration

Add these settings to your `config.py` (copy from `config.example.py`):

```python
# BGA Login Credentials
BGA_EMAIL = "your_email@example.com"
BGA_PASSWORD = "your_password"

# Leaderboard Settings
TERRAFORMING_MARS_GAME_ID = 1924
DEFAULT_PLAYER_COUNT = 100
```

## Usage

### Update Players Registry

```bash
# Update with default settings (top 100 players)
python update_players.py

# Update with custom number of players
python update_players.py --players 50

# Update with custom output file
python update_players.py --output data/my_players.csv

# Show statistics only (no update)
python update_players.py --stats-only

# Verbose logging
python update_players.py --verbose
```

### Command Line Options

- `--players, -n`: Number of top players to fetch (default: 100)
- `--output, -o`: Output CSV file path (default: data/processed/players.csv)
- `--game-id`: BGA Game ID (default: 1924 for Terraforming Mars)
- `--verbose, -v`: Enable verbose logging
- `--stats-only`: Only show registry statistics, do not update

### Example Output

```
=== Update Complete ===
Total players in registry: 100
New players added: 15
Players updated: 8
Players unchanged: 77

Top 10 players:
  #1: PlayerName1 (Country1)
  #2: PlayerName2 (Country2)
  ...
```

## CSV Format

The `players.csv` file contains:

| Column | Type | Description |
|--------|------|-------------|
| PlayerId | int | BGA player unique identifier |
| PlayerName | string | Player display name |
| Country | string | Player's country |
| ArenaRank | int | Current Arena Leaderboard rank |
| LastUpdated | datetime | ISO format timestamp of last update |

Example:
```csv
PlayerId,PlayerName,Country,ArenaRank,LastUpdated
12345678,TopPlayer,Norway,1,2025-06-18T20:15:30.123456
87654321,SecondPlace,Germany,2,2025-06-18T20:15:30.123456
```

## Features

### Smart Updates
- Only updates players whose data has changed
- Preserves historical data for players not in current top N
- Tracks when each player was last updated

### Registry Management
- Automatic CSV creation with headers
- Sorted by Arena rank (ascending)
- UTF-8 encoding support for international names

### Statistics and Queries
- Get top N players
- Find players by country
- Registry statistics (total players, countries, rank ranges)
- Player lookup by ID

## API Usage

```python
from src.players_registry import PlayersRegistry

# Initialize registry
registry = PlayersRegistry('data/processed/players.csv')

# Get statistics
stats = registry.get_registry_stats()
print(f"Total players: {stats['total_players']}")

# Get top 10 players
top_players = registry.get_top_players(10)

# Find specific player
player = registry.find_player(12345678)

# Get players from specific country
norway_players = registry.get_players_by_country("Norway")
```

## Testing

Run the test suite to verify functionality:

```bash
python test_players_registry.py
```

This creates sample data, tests all registry operations, and cleans up automatically.

## Error Handling

The system includes comprehensive error handling for:
- Network connectivity issues
- BGA login failures
- Invalid response formats
- CSV file operations
- Missing configuration

## Security Notes

- Store your BGA credentials securely in `config.py`
- Never commit `config.py` to version control
- The system uses session-based authentication (no credentials stored in requests)
- Request tokens are automatically managed

## Integration

This system is designed to work alongside the existing game scraping system. Both use CSV-based storage for consistency and can be run independently or together.

## Troubleshooting

### Login Issues
- Verify BGA_EMAIL and BGA_PASSWORD in config.py
- Check if your BGA account has access to Arena Leaderboards
- Try logging in manually to BGA website first

### Data Issues
- Use `--verbose` flag for detailed logging
- Check `--stats-only` to verify current registry state
- Ensure sufficient disk space for CSV files

### Network Issues
- The system includes automatic retries for network requests
- Check your internet connection
- BGA may have rate limiting - try reducing update frequency

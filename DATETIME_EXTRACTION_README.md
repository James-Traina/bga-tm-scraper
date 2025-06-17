# Datetime Extraction Feature

This document describes the enhanced datetime extraction functionality added to the BGA Terraforming Mars scraper.

## Overview

The scraper now extracts and parses datetime information from player game history pages, converting relative dates like "yesterday" to actual dates based on the current date.

## Features

### Datetime Formats Supported

1. **Relative dates**: "yesterday at 00:08", "today at 14:30"
2. **Absolute dates**: "2025-06-15 at 00:29"
3. **Alternative absolute format**: "15/06/2025 at 23:45"
4. **Time only**: "12:34" (assumes today's date)

### Enhanced Return Data

The `scrape_player_game_history()` method now returns a list of dictionaries instead of just table IDs:

```python
[
    {
        'table_id': '688328967',
        'raw_datetime': 'yesterday at 00:08',
        'parsed_datetime': '2025-06-16T00:08:00',
        'date_type': 'relative'
    },
    {
        'table_id': '687877071',
        'raw_datetime': '2025-06-15 at 00:29',
        'parsed_datetime': '2025-06-15T00:29:00',
        'date_type': 'absolute'
    }
]
```

### Date Type Classifications

- **`relative`**: Dates like "yesterday" or "today"
- **`absolute`**: Full dates in YYYY-MM-DD or DD/MM/YYYY format
- **`time_only`**: Just time information (assumes current date)
- **`unknown`**: When no datetime could be extracted

## Usage

### Basic Usage

```python
from src.scraper import TMScraper

scraper = TMScraper(chromedriver_path="path/to/chromedriver.exe")
scraper.start_browser()
scraper.login_to_bga()

# Get games with datetime information
games_data = scraper.scrape_player_game_history(player_id="12345678")

for game in games_data:
    print(f"Game {game['table_id']} played on {game['raw_datetime']}")
    print(f"Parsed datetime: {game['parsed_datetime']}")
```

### Filtering by Date

```python
from datetime import datetime, timedelta

# Filter games from the last 7 days
week_ago = datetime.now() - timedelta(days=7)

recent_games = []
for game in games_data:
    if game['parsed_datetime']:
        game_date = datetime.fromisoformat(game['parsed_datetime'])
        if game_date >= week_ago:
            recent_games.append(game)

print(f"Found {len(recent_games)} games from the last week")
```

## Implementation Details

### New Methods Added

1. **`_extract_games_with_datetimes_from_history()`**: Main extraction method
2. **`_extract_datetime_from_row()`**: Extracts datetime from individual game rows
3. **`_parse_game_datetime()`**: Parses various datetime formats

### Timezone Handling

- All parsed datetimes are in the local timezone where the scraper is running
- Currently set for Europe/Oslo (UTC+2) based on your location
- Relative dates ("yesterday") are calculated based on the current local time

### Error Handling

- If no datetime is found for a game, it returns:
  ```python
  {
      'raw_datetime': 'unknown',
      'parsed_datetime': None,
      'date_type': 'unknown'
  }
  ```
- Parsing errors are logged but don't stop the scraping process

## Testing

Run the datetime parsing test to verify functionality:

```bash
python test_datetime_parsing.py
```

This will test various datetime formats and show the parsing results.

## Updated Test Script

The `test_player_history.py` script has been updated to:

1. Display datetime information for each game found
2. Save games data with datetime information to JSON files
3. Include datetime info in processing summaries

### Sample Output

```
✅ Successfully found 25 games with datetime information!
Games found (showing first 10):
  1. Table ID: 688328967
     Date: yesterday at 00:08 (relative)
     Parsed: 2025-06-16T00:08:00

  2. Table ID: 687877071
     Date: 2025-06-15 at 00:29 (absolute)
     Parsed: 2025-06-15T00:29:00
```

## Benefits

1. **Historical Analysis**: Track when games were played over time
2. **Filtering Capabilities**: Filter games by date ranges for analysis
3. **Data Completeness**: More comprehensive game history data
4. **Timezone Awareness**: Proper handling of local time vs relative dates

## Arena Season 21 Filtering

The scraper now includes built-in filtering for Arena season 21 games (2025-04-08 to 2025-07-08).

### Usage

```python
# Enable Arena season 21 filtering
games_data = scraper.scrape_player_game_history(
    player_id="12345678",
    filter_arena_season_21=True
)

# This will only return games played between 2025-04-08 and 2025-07-08
```

### Date Range Constants

```python
ARENA_SEASON_21_START = datetime(2025, 4, 8)
ARENA_SEASON_21_END = datetime(2025, 7, 8, 23, 59, 59)
```

### Filtering Logic

- Games are filtered based on their parsed datetime
- Only games with valid parsed datetimes within the season 21 range are included
- Games with unparseable dates are excluded for safety
- Filtering statistics are logged and displayed during scraping

### Test Script Integration

The `test_player_history.py` script now includes an option to enable Arena season 21 filtering:

```
Filter for Arena season 21 games only (2025-04-08 to 2025-07-08)? (y/n): y
🎯 Arena season 21 filtering enabled - only games from 2025-04-08 to 2025-07-08 will be included
```

## Future Enhancements

Potential improvements could include:

1. **Timezone Configuration**: Allow users to specify their timezone
2. **More Date Formats**: Support additional relative date formats ("2 days ago", etc.)
3. **Configurable Date Ranges**: Allow custom date range filtering
4. **Performance Optimization**: Caching of parsed dates
5. **Multiple Season Support**: Support filtering for different Arena seasons

# Dynamic Version Extraction for BGA Replay URLs

## Problem

BoardGameArena replay URLs contain a version number that changes depending on when the game was played. The original scraper used a hardcoded version number in the `REPLAY_URL_TEMPLATE`:

```
https://boardgamearena.com/archive/replay/250604-1037/?table={table_id}&player={player_id}&comments={player_id}
```

This caused issues when trying to scrape replays from games played at different times, as they would have different version numbers (e.g., `250505-1448`, `250604-1037`, etc.).

## Solution

The scraper now dynamically extracts the correct version number for each game by:

1. **Fetching the gamereview page**: For each table ID, the scraper first navigates to `https://boardgamearena.com/gamereview?table={table_id}`

2. **Extracting version from replay links**: The gamereview page contains links to the replay with the correct version number. The scraper parses these links using regex pattern `/archive/replay/(\d+-\d+)/`

3. **Constructing the correct replay URL**: Using the extracted version, the scraper builds the proper replay URL: `https://boardgamearena.com/archive/replay/{version}/?table={table_id}&player={player_id}&comments={player_id}`

4. **Fallback mechanism**: If version extraction fails, the scraper falls back to using the hardcoded version from `config.py`

## Implementation Details

### New Method: `extract_version_from_gamereview()`

```python
def extract_version_from_gamereview(self, table_id: str) -> Optional[str]:
    """
    Extract the version number from the gamereview page
    
    Args:
        table_id: BGA table ID
        
    Returns:
        str: Version number (e.g., "250604-1037") or None if not found
    """
```

This method:
- Navigates to the gamereview page
- Parses HTML to find replay links
- Extracts version using regex
- Handles authentication and error cases
- Returns the version string or None

### Updated Method: `scrape_replay_from_table()`

The existing method now:
1. First calls `extract_version_from_gamereview()` to get the correct version
2. Constructs the replay URL with the extracted version
3. Falls back to the config template if version extraction fails
4. Proceeds with normal replay scraping

## Usage

The dynamic version extraction is automatically used when calling:

```python
# This now automatically extracts the correct version
replay_data = scraper.scrape_replay_from_table(table_id, player_id)

# Or when using the full table and replay scraping
combined_data = scraper.scrape_table_and_replay(table_id)
```

## Testing

Use the provided test script to verify the functionality:

```bash
python test_version_extraction.py
```

This script will:
1. Start the browser and prompt for BGA login
2. Extract the version number from a test table's gamereview page
3. Construct a replay URL with the extracted version
4. Test if the constructed URL works by scraping the replay
5. Display the results

## Benefits

1. **Automatic compatibility**: Works with games from any time period
2. **No manual version updates**: No need to update hardcoded version numbers
3. **Robust fallback**: Still works if version extraction fails
4. **Minimal performance impact**: Only one additional page request per game
5. **Future-proof**: Will continue working as BGA releases new versions

## Error Handling

The implementation includes comprehensive error handling:
- Authentication errors (redirects to login)
- Network timeouts and connection issues
- Missing or malformed version numbers
- Inaccessible gamereview pages
- Fallback to hardcoded version when needed

## Logging

The scraper logs all version extraction activities:
- Successful version extraction: `INFO` level
- Fallback to hardcoded version: `WARNING` level
- Extraction failures: `ERROR` level
- Debug information: `DEBUG` level

This ensures you can monitor the version extraction process and troubleshoot any issues.

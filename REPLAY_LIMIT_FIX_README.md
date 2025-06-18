# Replay Limit Detection Fix

This document describes the fix implemented to properly detect and handle BGA's daily replay limits during scraping.

## Problem

The scraper was continuing to attempt replay access even after hitting BGA's daily replay limit, which:
- Wastes time making futile requests
- Shows disrespect for BGA's server resources
- Could potentially flag the account for excessive usage

## Solution Implemented

### 1. Replay Limit Detection (`_check_replay_limit_reached`)

Added a comprehensive method in `src/scraper.py` that detects replay limits by looking for:

**Text-based indicators:**
- "you have reached a limit (replay)"
- "you have reached a limit"
- "reached a limit (replay)"
- "reached a limit"
- "replay limit"
- "limit reached"
- "daily replay limit"

**HTML structure detection:**
- Notification elements (div.notification, div.alert, etc.)
- Elements with limit-related classes
- Warning/error message containers

### 2. Integration in Replay Scraping

The `scrape_replay()` method now:
1. **Checks for limit immediately** after loading a replay page
2. **Returns a special result** when limit is detected:
   ```python
   {
       'replay_id': replay_id,
       'url': url,
       'scraped_at': datetime.now().isoformat(),
       'error': 'replay_limit_reached',
       'limit_reached': True,
       'html_length': len(page_source)
   }
   ```
3. **Logs clear warnings** about the limit being reached
4. **Provides user-friendly messages** explaining the situation

### 3. Graceful Script Termination

Updated `test_player_history.py` to:
1. **Detect limit results** from scraping operations
2. **Stop processing immediately** when limit is reached
3. **Save progress** before terminating
4. **Display clear messages** to the user about what happened

## How It Works

### Detection Flow
```
1. Navigate to replay page
2. Check page content for limit indicators
3. If limit detected:
   - Log warning
   - Return limit_reached result
   - Display user message
4. If no limit, continue normal processing
```

### Script Response
```
1. Receive scraping result
2. Check for limit_reached flag
3. If limit reached:
   - Display "REPLAY LIMIT REACHED!" message
   - Save current progress
   - Exit scraping loop gracefully
4. If no limit, continue processing
```

## User Experience

### Before Fix
```
❌ Scraping game 123456789...
❌ Failed to scrape game 123456789
❌ Scraping game 987654321...
❌ Failed to scrape game 987654321
[Continues indefinitely with failures]
```

### After Fix
```
✅ Scraping game 123456789...
✅ Successfully scraped game 123456789
🚫 REPLAY LIMIT REACHED!
   Stopping scraping process to respect BGA's daily limits.
   Please try again tomorrow when the limit resets.

💾 Saving progress before stopping...
✅ Processing complete!
```

## Technical Details

### Limit Detection Patterns

The detection is case-insensitive and looks for multiple variations:
- **Exact match**: "You have reached a limit (replay)"
- **Partial matches**: "reached a limit", "replay limit"
- **Generic patterns**: "limit reached", "daily replay limit"

### Error Handling

- **Robust parsing**: Uses both text search and HTML parsing
- **Graceful degradation**: If HTML parsing fails, falls back to text search
- **Logging**: All detection events are logged for debugging

### Integration Points

1. **`scrape_replay()`** - Primary detection point
2. **`scrape_replay_from_table()`** - Inherits detection via `scrape_replay()`
3. **`scrape_table_and_replay()`** - Handles limit results appropriately
4. **`test_player_history.py`** - Responds to limit detection

## Benefits

### ✅ Respectful Usage
- Immediately stops when limits are reached
- Prevents unnecessary server load
- Shows respect for BGA's resource management

### ✅ Better User Experience
- Clear messages about what happened
- Explains when to try again
- Saves progress before stopping

### ✅ Efficient Processing
- No wasted time on futile requests
- Preserves completed work
- Allows resumption the next day

### ✅ Robust Detection
- Multiple detection methods
- Handles various limit message formats
- Comprehensive error handling

## Testing

To test the limit detection:
1. Run the scraper until you hit the actual replay limit
2. Verify the script detects the limit and stops gracefully
3. Check that progress is saved properly
4. Confirm clear user messages are displayed

## Future Enhancements

Potential improvements:
- **Proactive limit tracking**: Count replay requests and warn before hitting limits
- **Time-based reset detection**: Automatically retry after limit reset time
- **Limit status caching**: Remember limit status to avoid repeated checks
- **Multiple limit types**: Detect other BGA limits (not just replay limits)

---

**Note**: This fix ensures the scraper behaves responsibly and respects BGA's daily replay limits, providing a better experience for both users and BGA's servers.

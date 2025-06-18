# Automated BGA Login Implementation

This document describes the new automated login functionality that eliminates the need for manual login when scraping BoardGameArena (BGA) data.

## Overview

The automated login system combines session-based authentication with browser automation to provide seamless, hands-free scraping. No more manual login required!

## Key Components

### 1. BGAHybridSession (`src/bga_hybrid_session.py`)
- **Purpose**: Core hybrid session manager that handles automated authentication
- **Features**:
  - Performs programmatic login using email/password
  - Transfers authenticated session cookies to Selenium browser
  - Handles session refresh when cookies expire
  - Provides unified authentication for both API calls and browser automation

### 2. Updated TMScraper (`src/scraper.py`)
- **New Method**: `start_browser_and_login()` - Replaces manual login process
- **Enhanced Features**:
  - Automatic credential loading from config
  - Graceful fallback to manual login if automated login fails
  - Automatic session refresh on authentication errors
  - Improved error handling and recovery

### 3. Updated Scripts
- **test_player_history.py**: Now uses automated login by default
- **test_automated_login.py**: New test script to verify functionality

## Setup Instructions

### 1. Update Configuration
Ensure your `config.py` contains valid BGA credentials:

```python
# BGA Login Credentials
BGA_EMAIL = "your_actual_email@example.com"
BGA_PASSWORD = "your_actual_password"

# Chrome settings (existing)
CHROMEDRIVER_PATH = r'C:\path\to\your\chromedriver.exe'
```

### 2. Install Dependencies
No new dependencies required - uses existing packages.

## Usage Examples

### Basic Usage (TMScraper)
```python
from src.scraper import TMScraper

# Initialize scraper (credentials loaded automatically from config)
scraper = TMScraper(
    chromedriver_path=CHROMEDRIVER_PATH,
    request_delay=2,
    headless=False
)

# Start browser and login automatically
if scraper.start_browser_and_login():
    print("✅ Logged in successfully!")
    
    # Now you can scrape without manual intervention
    games = scraper.scrape_player_game_history("player_id")
    
    # Always close when done
    scraper.close_browser()
else:
    print("❌ Automated login failed")
```

### Direct Hybrid Session Usage
```python
from src.bga_hybrid_session import BGAHybridSession

# Use as context manager for automatic cleanup
with BGAHybridSession(
    email="your_email@example.com",
    password="your_password",
    chromedriver_path=CHROMEDRIVER_PATH
) as session:
    
    if session.login():
        # Get authenticated browser driver
        driver = session.get_driver()
        
        # Get authenticated requests session
        requests_session = session.get_session()
        
        # Use both for scraping...
```

### Fallback Behavior
The system automatically falls back to manual login if automated login fails:

```python
# This will try automated login first, then fallback to manual if needed
if not scraper.start_browser_and_login():
    print("Falling back to manual login...")
    scraper.start_browser()
    scraper.login_to_bga()  # Manual login as before
```

## Testing

### Run Automated Login Tests
```bash
python test_automated_login.py
```

This will test:
- Direct hybrid session functionality
- TMScraper integration
- Authentication verification
- Browser navigation

### Run Full Scraping Test
```bash
python test_player_history.py
```

This will:
- Use automated login by default
- Scrape a player's game history
- Parse and save game data
- Demonstrate the complete workflow

## How It Works

### Authentication Flow
1. **Session Login**: Uses `requests.Session` to authenticate with BGA servers
2. **Token Extraction**: Extracts request tokens from HTML responses
3. **Cookie Transfer**: Transfers authenticated cookies to Selenium browser
4. **Verification**: Verifies browser authentication by checking protected pages
5. **Ready to Scrape**: Both session and browser are now authenticated

### Session Management
- **Automatic Refresh**: Detects when sessions expire and refreshes automatically
- **Error Recovery**: Handles authentication errors gracefully
- **Cleanup**: Properly closes browsers and cleans up resources

### Security Features
- **Credential Protection**: Credentials are only stored in config file
- **Session Isolation**: Each scraping session is independent
- **Secure Headers**: Uses appropriate headers to avoid detection

## Migration Guide

### From Manual Login
If you were using the old manual login approach:

**Old Way:**
```python
scraper.start_browser()
scraper.login_to_bga()  # Manual login required
```

**New Way:**
```python
scraper.start_browser_and_login()  # Fully automated
```

### Backward Compatibility
- All existing methods still work
- Manual login is still available as fallback
- No breaking changes to existing scripts

## Troubleshooting

### Common Issues

**1. "Email and password are required"**
- Solution: Update `BGA_EMAIL` and `BGA_PASSWORD` in `config.py`

**2. "Automated login failed"**
- Check credentials are correct
- Verify internet connection
- Try manual login to test BGA accessibility
- Check ChromeDriver compatibility

**3. "Session expired" during scraping**
- The system should auto-refresh, but if it doesn't:
- Check if BGA changed their authentication system
- Try restarting the scraping process

**4. Browser doesn't start**
- Verify `CHROMEDRIVER_PATH` in config
- Ensure ChromeDriver version matches your Chrome browser
- Check file permissions

### Debug Mode
Enable debug logging for detailed information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Benefits

### ✅ Advantages
- **No Manual Intervention**: Fully automated login process
- **Robust Error Handling**: Automatic session refresh and fallback
- **Unified Authentication**: Works for both API calls and browser automation
- **Backward Compatible**: Existing scripts continue to work
- **Easy Setup**: Just update credentials in config

### 🔄 Improved Workflow
- **Before**: Start script → Wait for browser → Manually login → Continue scraping
- **After**: Start script → Automatic login → Immediate scraping

## Future Enhancements

Potential improvements for future versions:
- Support for 2FA authentication
- Session persistence across script runs
- Multiple account support
- Headless mode optimization
- Rate limiting integration

## Support

If you encounter issues:
1. Run `test_automated_login.py` to verify setup
2. Check the troubleshooting section above
3. Enable debug logging for detailed error information
4. Ensure all dependencies are up to date

---

**Note**: This implementation respects BGA's terms of service and implements appropriate delays and error handling to avoid overwhelming their servers.

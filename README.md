# BGA Terraforming Mars Scraper

A web scraper for collecting Terraforming Mars game replay data from BoardGameArena (BGA).

## Overview

This scraper extracts detailed game logs from BGA Terraforming Mars replays for analysis. It uses web automation with manual login to handle BGA's authentication requirements.

## Features

- **Web automation**: Uses browser automation for reliable data extraction
- **Manual authentication**: Handles BGA login through browser interaction
- **Raw data preservation**: Saves complete HTML for iterative parser development
- **Batch processing**: Scrapes multiple replays with configurable delays
- **Error handling**: Robust error handling and logging

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
- `TEST_URLS`: Add BGA replay URLs you want to scrape

### 4. Run the Scraper

```bash
python main.py
```

The scraper will:
1. Open a Chrome browser window
2. Navigate to BoardGameArena
3. Wait for you to log in manually
4. Scrape the configured replay URLs
5. Save raw HTML and summary data

## Project Structure

```
bga-tm-scraper/
├── src/
│   ├── scraper.py             # Main scraper class
│   └── __init__.py
├── data/
│   ├── raw/                   # Raw HTML files
│   └── processed/             # Processed JSON summaries
├── main.py                    # Entry point
├── config.py                  # Configuration (update this)
├── config.example.py          # Configuration template
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Configuration

Key settings in `config.py`:

- `TEST_URLS`: List of BGA replay URLs to scrape
- `CHROMEDRIVER_PATH`: Path to ChromeDriver executable
- `REQUEST_DELAY`: Delay between requests (default: 2 seconds)
- `RAW_DATA_DIR`: Directory for raw HTML files
- `PROCESSED_DATA_DIR`: Directory for processed data

## Output

The scraper generates:

1. **Raw HTML files**: Complete replay pages saved to `data/raw/`
2. **Summary JSON**: Metadata and basic info saved to `data/processed/`

Example summary data:
```json
{
  "replay_id": "250604-1037",
  "url": "https://boardgamearena.com/archive/replay/250604-1037/...",
  "scraped_at": "2025-06-16T19:30:36.123456",
  "title": "Terraforming Mars - Replay",
  "players": ["Player1", "Player2"],
  "game_logs_found": true,
  "num_moves": 245
}
```

## Authentication

The scraper uses manual login:
1. Browser opens to BoardGameArena
2. You log in manually in the browser
3. Press Enter in the terminal to continue
4. Scraper proceeds with authenticated session

## Rate Limiting

The scraper includes respectful rate limiting:
- 2-second delay between requests (configurable)
- Single-threaded operation
- Error handling for failed requests

## Troubleshooting

### ChromeDriver Issues
- Make sure ChromeDriver version matches your Chrome browser
- Update `CHROMEDRIVER_PATH` in config.py
- Check Chrome version: Help > About Google Chrome
- Download matching ChromeDriver from https://chromedriver.chromium.org/

### Authentication Issues
- Make sure you're fully logged into BGA before pressing Enter
- Check that the browser window stays open during scraping
- Look for "must be logged" errors in the output

### No Game Logs Found
- Verify the replay URL is accessible when logged in
- Check that the replay isn't private or restricted
- Look at the raw HTML file to debug parsing issues

## Future Development

Planned features:
- [ ] Game log parser to extract structured move data
- [ ] URL discovery from Arena leaderboards
- [ ] Season 21 filtering for consistent game settings
- [ ] Statistical analysis of card win rates
- [ ] Integration with existing Steam data format

## License

This project is for educational and research purposes. Please respect BoardGameArena's terms of service and use responsibly.

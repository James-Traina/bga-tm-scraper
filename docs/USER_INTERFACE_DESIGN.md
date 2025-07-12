# BGA TM Scraper User Interface Design (Living Document)

## Current Status: ONE WEEK MVP

Building the simplest possible web UI that lets a non-technical user scrape ONE game at a time.

### What We're Building (5 Days)
- Single-file Flask app (`web_ui.py`)
- User enters one game URL at a time
- User provides BGA credentials (used only for scraping, not stored)
- Downloads results as ZIP file
- Manual upload to GitHub

### Implementation Plan
1. **Day 1**: Flask shell with basic form
2. **Day 2**: Scraper integration
3. **Day 3**: Duplicate check against games.csv
4. **Day 4**: ZIP file export
5. **Day 5**: Test & document

### Key Decisions Made
- **No GitHub automation** - Manual ZIP upload is 10x simpler
- **No database** - In-memory duplicate checking only
- **No batch processing** - One game at a time for simplicity
- **No JavaScript frameworks** - Plain HTML form
- **No user accounts** - Anonymous usage

### Why These Choices
- **Minimal complexity** allows shipping in 1 week vs 1 month
- **Manual upload** removes OAuth complexity while providing 90% value
- **Single game** simplifies error handling and UI
- **No persistence** means no data migration headaches

### Dead Ends We Avoided
1. **GitHub OAuth integration** - Adds weeks of complexity for marginal benefit
2. **SQLite persistence** - Unnecessary for MVP, adds deployment complexity
3. **OS keyring** - Platform-specific issues, not needed for one-time credentials
4. **Player history browsing** - Feature creep that delays core functionality
5. **Pretty UI** - Function over form for MVP

### Success Criteria
- Works for 1 game
- Prevents duplicate scraping
- Returns valid data
- Total code < 200 lines

### Next Steps After MVP Ships
Only if MVP proves successful:
1. Multiple game URLs
2. Better UI/styling
3. Standalone packaging
4. GitHub automation (if users request it)

## Code Structure
```
web_ui.py              # Entire app in one file
games.csv              # Downloaded on startup for duplicate check
output/                # Temporary directory for scraped files
```

## UI Elements
- Game URL input field
- BGA username field  
- BGA password field (masked)
- "Scrape Game" button
- Status messages (success/duplicate/error)
- Download ZIP button (appears after successful scrape)

## Previous Design Iterations (Archived Summary)

### V1: Comprehensive Design (Too Complex)
- Included GitHub OAuth, SQLite, keyring integration
- 4-phase implementation over months
- Rejected for: Over-engineering before validating need

### V2: Streamlined MVP (Still Too Much)
- 2-week timeline with Flask/Electron choice
- ZIP export with manual upload
- Rejected for: Still too many features for initial validation

### Current: One Week MVP (Just Right)
- Single game at a time
- Bare minimum UI
- Ship fast, iterate based on feedback
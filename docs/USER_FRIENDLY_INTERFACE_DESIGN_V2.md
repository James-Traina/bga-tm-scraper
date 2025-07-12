# User-Friendly BGA TM Scraper Interface Design (Streamlined)

## Core Problem
Non-technical Terraforming Mars players can't contribute their games to the community dataset because the current scraper requires Python/CLI knowledge.

## Minimal Solution: Web Scraper with Export

### What We're Building (MVP)
A single web application where users can:
1. Paste BGA game URLs
2. Enter their BGA credentials
3. Click "Scrape Games"
4. Download results as a ZIP file
5. Manually submit to GitHub (with clear instructions)

### What We're NOT Building (Yet)
- GitHub integration (OAuth, PRs, automated uploads)
- Player history browsing
- Date range filters
- Persistent storage (SQLite)
- OS keyring integration
- Stats/leaderboards
- Auto-updates

## Technical Stack (Simplified)

**Option A: Flask + Browser**
- Simple Flask app (one file if possible)
- In-memory duplicate checking
- Basic session storage
- Manual download button

**Option B: Electron/Tauri Wrapper** (Recommended)
- Desktop app wrapping the Python scraper
- No localhost/firewall issues
- Easier distribution
- Built-in file save dialogs

## User Flow (3 Steps)

1. **Input Games**
   ```
   ┌─────────────────────────────────────────────┐
   │ BGA Terraforming Mars Scraper               │
   ├─────────────────────────────────────────────┤
   │ Paste game URLs (one per line):             │
   │ ┌─────────────────────────────────────┐     │
   │ │ https://boardgamearena.com/table...  │     │
   │ │ https://boardgamearena.com/table...  │     │
   │ │                                      │     │
   │ └─────────────────────────────────────┘     │
   │                                             │
   │ BGA Username: [___________]                 │
   │ BGA Password: [___________]                 │
   │                                             │
   │ [Check Games]                               │
   └─────────────────────────────────────────────┘
   ```

2. **Review & Scrape**
   ```
   ┌─────────────────────────────────────────────┐
   │ Ready to Scrape:                            │
   ├─────────────────────────────────────────────┤
   │ ✅ Game #123456789 - New                    │
   │ ❌ Game #123456790 - Already scraped        │
   │ ✅ Game #123456791 - New                    │
   │                                             │
   │ Will scrape: 2 new games                    │
   │                                             │
   │ [Start Scraping]                            │
   └─────────────────────────────────────────────┘
   ```

3. **Download Results**
   ```
   ┌─────────────────────────────────────────────┐
   │ Scraping Complete!                          │
   ├─────────────────────────────────────────────┤
   │ ✅ Successfully scraped 2 games             │
   │                                             │
   │ [Download Results (ZIP)]                    │
   │                                             │
   │ To submit your games:                       │
   │ 1. Click download above                     │
   │ 2. Go to: github.com/[repo]/upload         │
   │ 3. Upload the ZIP file                      │
   │ 4. Add message: "Add 2 games"              │
   └─────────────────────────────────────────────┘
   ```

## Implementation Plan (2 Weeks Total)

### Week 1: Core Functionality
- Day 1-2: Basic Flask/Electron setup
- Day 3-4: BGA login and URL parsing
- Day 5: Duplicate checking (download games.csv)
- Day 6-7: Scraping integration

### Week 2: Polish & Release
- Day 8-9: ZIP export functionality
- Day 10: Error handling and messages
- Day 11: Simple deployment/packaging
- Day 12-13: Documentation and release
- Day 14: Buffer/fixes

## Data Format

**Input**: List of BGA game URLs (newline separated)
```
https://boardgamearena.com/table?table=520549261
https://boardgamearena.com/table?table=520549262
```

**Output**: ZIP containing:
```
scraped_games_2024-01-15/
├── games.csv (append these rows to registry)
├── raw/
│   ├── table_520549261.html
│   ├── replay_520549261.html
│   └── ...
└── README.txt (submission instructions)
```

## Duplicate Checking (Simplified)

1. On startup: Fetch latest `games.csv` from GitHub
2. Build set of already-scraped table IDs
3. When user pastes URLs: Mark duplicates
4. Only scrape new games

## Error Handling

Three states only:
- **New**: Ready to scrape
- **Already Scraped**: Skip (show who scraped it)
- **Error**: Invalid URL or scraping failed

## Future Enhancements (Post-MVP)

Only after validating the core works:
1. GitHub OAuth integration
2. Player history browser
3. Persistent storage
4. Auto-updates
5. Batch operations

## Success Metrics

1. User can go from zero to submitted games in <10 minutes
2. Zero Python/Git knowledge required
3. Clear feedback at every step
4. Works on Windows/Mac/Linux

## Immediate Next Steps

1. **Verify BGA ToS** allows automated scraping
2. **Choose Electron vs Flask** based on packaging ease
3. **Build simplest possible prototype** (accept 1 URL, scrape it)
4. **Test with 2-3 friendly users**
5. **Ship public beta within 2 weeks**

## What This Achieves

- **Immediate value**: Non-technical users can contribute TODAY
- **Minimal complexity**: No databases, no OAuth, no Git
- **Fast iteration**: Get real feedback in 2 weeks
- **Clear upgrade path**: Can add features based on actual usage

The key insight: **Export + manual upload** is 10x simpler than automated GitHub integration, and still provides 90% of the value. Ship this first, automate later.
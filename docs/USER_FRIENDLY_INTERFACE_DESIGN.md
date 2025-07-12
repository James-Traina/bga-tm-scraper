# User-Friendly BGA TM Scraper Interface Design

## Problem Statement

Currently, the BGA TM scraper requires technical knowledge (Python, CLI, Git) to operate. We need a user-friendly interface that allows non-technical Terraforming Mars enthusiasts to contribute game data to the community dataset.

## User Personas

**Primary User**: Terraforming Mars player who:
- Plays on BoardGameArena regularly
- Wants to contribute their games to community analysis
- Has no programming experience
- May not understand Git/GitHub
- Uses Windows/Mac/Linux with a web browser

## Core Requirements

1. **Simple Game List Creation**: Users can easily specify which games to scrape
2. **One-Click Scraping**: Automated scraping without technical setup
3. **Automatic Upload**: Seamless contribution to the GitHub repository
4. **Duplication Prevention**: Only scrape games not already in the dataset
5. **Progress Visibility**: Users can see what they've contributed

## Technical Constraints

1. BGA authentication required for scraping
2. GitHub API rate limits and authentication
3. Cross-platform compatibility needed
4. Must integrate with existing scraper codebase
5. Respect BGA's daily replay limits
6. **Must comply with BGA Terms of Service** (critical - needs verification)

## Proposed Solution: Web-Based Interface

### Phase 1: Minimal Local Web App (MVP)

A lightweight local web application that:
- Runs on user's machine (no cloud hosting needed)
- Provides a simple web UI (localhost)
- Reuses existing Python scraper code
- Handles GitHub commits via API

**Technology Stack**:
- Backend: Flask (minimal Python web framework)
- Frontend: Simple HTML + vanilla JavaScript
- Data: Local SQLite for user session data
- Packaging: PyInstaller for standalone executable

### User Flow

1. **Download & Launch**
   - User downloads a single executable
   - Double-clicks to start local web server
   - Browser opens to `http://localhost:5000`

2. **Initial Setup** (one-time)
   - Enter BGA username/password (stored securely via OS keyring)
   - Simple "Connect to GitHub" button (OAuth only, no PAT)
   - Automatic fork creation (hidden from user)

3. **Add Games to Scrape**
   - Option A: Paste BGA game URLs
   - Option B: Enter player name to see their recent games
   - Option C: Enter date range for their games
   - Shows checklist of games with duplicate detection

4. **Scrape & Upload**
   - Click "Start Scraping"
   - Progress bar shows games being processed
   - Automatic commits to GitHub after each batch
   - Clear success/error messages

### Data Flow

```
User Input → Local Web App → Existing Scraper → Local Storage → GitHub API
                   ↓
            Duplicate Check ← Games Registry (from GitHub)
```

### Duplication Handling Strategy

1. **On Startup**: Download latest `games.csv` from GitHub
2. **Before Scraping**: Check each game against registry
3. **Visual Indicators**: 
   - ✅ Already scraped (by anyone)
   - 🆕 New game to scrape
   - ⏳ In progress
   - ❌ Failed (with retry option)

### GitHub Integration Approach

**Option 1: Fork & Pull Request** (Recommended)
- User forks repository once
- App commits to user's fork
- App creates pull request to main repo
- Maintainers review and merge

**Option 2: Direct Branch** (Simpler)
- App creates branch on main repo
- Commits directly to branch
- Creates pull request automatically

### Interface Mockup

```
┌─────────────────────────────────────────────┐
│ BGA Terraforming Mars Scraper               │
├─────────────────────────────────────────────┤
│ Status: Connected to BGA ✓ | GitHub ✓       │
├─────────────────────────────────────────────┤
│ Add Games:                                  │
│ ┌─────────────────────────────────────┐     │
│ │ Paste game URLs or player name...   │     │
│ └─────────────────────────────────────┘     │
│ [Add Games] [My Recent Games]               │
├─────────────────────────────────────────────┤
│ Games to Scrape (3 new, 2 duplicates):     │
│                                             │
│ ☐ Game #520549261 - 2024-01-15 ✅          │
│ ☑ Game #520549262 - 2024-01-15 🆕          │
│ ☑ Game #520549263 - 2024-01-15 🆕          │
│ ☑ Game #520549264 - 2024-01-15 🆕          │
│ ☐ Game #520549265 - 2024-01-15 ✅          │
│                                             │
│ [Select All New] [Deselect All]            │
│                                             │
│ [Start Scraping]                            │
├─────────────────────────────────────────────┤
│ Progress: ████████░░ 2/3 games             │
│ Currently: Scraping replay #520549263...    │
└─────────────────────────────────────────────┘
```

## Implementation Phases

### Phase 0: Command-Line Prototype (3-5 days)
- Simple Python script with friendly prompts
- Uses `input()` for BGA credentials and game URLs
- Tests core scraping logic end-to-end
- Validates approach with 1-2 friendly users

### Phase 1: MVP (2-3 weeks)
- Basic Flask app with game URL input
- Integration with existing scraper
- Local duplicate checking
- Manual GitHub upload instructions
- SQLite for progress persistence (track game states)

### Phase 2: GitHub Integration (1-2 weeks)
- GitHub OAuth/PAT authentication
- Automatic commits and pull requests
- Download registry for duplicate checking

### Phase 3: Enhanced UX (1-2 weeks)
- Player game history browser
- Batch operations
- Better error handling and retry
- Progress persistence

### Phase 4: Advanced Features (Future)
- Game filtering (Arena only, date ranges)
- Contribution statistics
- Dataset preview
- Multi-user coordination

## Security Considerations

1. **Credentials**: Use OS native keyring (macOS Keychain, Windows Credential Manager) via `keyring` library
2. **GitHub Access**: OAuth only with minimal scopes (public_repo, workflow)
3. **Rate Limiting**: Respect both BGA and GitHub limits
4. **Validation**: Sanitize all user inputs
5. **BGA ToS Compliance**: Verify scraping is permitted before release
6. **No Git Terminology**: Hide all Git concepts (fork, branch, PR) from users

## Success Metrics

1. Non-technical users can contribute games
2. Zero duplicate scraping
3. Successful GitHub integration
4. Growing community dataset

## Minimal First Step

Create a simple Flask app that:
1. Accepts a list of game URLs
2. Checks for duplicates against local registry
3. Scrapes new games only
4. Saves results locally
5. Shows instructions for manual GitHub upload

This provides immediate value while we build the full solution incrementally.

## Additional Considerations (from Review)

1. **Update Mechanism**: Include "Check for Updates" feature in Phase 2
2. **State Management**: SQLite should track game states from the start:
   - `pending`, `scraped`, `uploaded`, `failed`
   - Allows resume after crashes/restarts
3. **GitHub Workflow**: 
   - Pull latest `games.csv` before each PR
   - Minimize merge conflict window
   - Automate fork creation completely
4. **User Communication**:
   - Never expose Git terminology
   - "Submit my games" instead of "Create pull request"
   - Clear, non-technical error messages
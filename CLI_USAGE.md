# Terraforming Mars BGA Scraper - CLI Usage Guide

## Overview

The new CLI provides a clean, command-based interface for all scraping and parsing operations. Each command has a specific purpose and uses intuitive arguments.

## Commands

### 1. `scrape-tables` - Scrape table HTMLs only

Scrapes table pages to identify Arena mode games and extract basic information.

```bash
# Scrape tables for all players (updates player registry first)
python main.py scrape-tables --all --update-players

# Scrape tables for specific players
python main.py scrape-tables 12345678 87654321 11223344
```

**Options:**
- `--all, -a`: Process all players from the registry
- `--update-players`: Update player registry before processing
- `--retry-failed`: Include previously failed games

### 2. `scrape-complete` - Full workflow (tables + replays + parsing)

Performs the complete workflow: scrapes tables, scrapes replays for Arena games, and parses them.

```bash
# Complete workflow for all players
python main.py scrape-complete --all --update-players

# Complete workflow for specific players
python main.py scrape-complete 12345678 87654321

# Retry failed games for specific players
python main.py scrape-complete 12345678 --retry-failed
```

**Options:**
- `--all, -a`: Process all players from the registry
- `--update-players`: Update player registry before processing
- `--retry-failed`: Include previously failed games

### 3. `scrape-replays` - Scrape replays and parse (requires table HTMLs)

Scrapes replay pages and parses games that already have table HTML scraped.

```bash
# Process all games that need replay scraping
python main.py scrape-replays

# Process specific games (using composite keys)
python main.py scrape-replays 123456789:12345678 987654321:87654321
```

**Composite Key Format:** `table_id:player_perspective`
- Example: `123456789:12345678` means table ID 123456789 from player 12345678's perspective

### 4. `parse` - Parse games only (requires both HTMLs)

Parses games that have both table and replay HTML files already scraped.

```bash
# Parse all games ready for parsing
python main.py parse

# Parse specific games
python main.py parse 123456789:12345678 987654321:87654321

# Reparse all games (including already parsed ones)
python main.py parse --reparse

# Reparse specific games
python main.py parse --reparse 123456789:12345678 987654321:87654321
```

**Options:**
- `--reparse`: Reparse already parsed games (overwrite existing JSON files)

### 5. `update-players` - Update player registry

Updates the player registry with the latest Arena leaderboard data.

```bash
# Update with default number of players (from config)
python main.py update-players

# Update with specific number of top players
python main.py update-players --count 200
```

### 6. `status` - Show registry status

Displays statistics about the current state of the games registry.

```bash
# Basic status
python main.py status

# Detailed status with breakdowns
python main.py status --detailed
```

## Global Options

These options work with most commands:

- `--retry-failed`: Include previously failed games in processing

## Common Usage Patterns

### Initial Setup
```bash
# 1. Update player registry
python main.py update-players --count 100

# 2. Check status
python main.py status

# 3. Start with table scraping for all players
python main.py scrape-tables --all
```

### Daily Workflow
```bash
# Update players and run complete workflow for new data
python main.py scrape-complete --all --update-players

# Or just parse games that are ready
python main.py parse

# Check progress
python main.py status --detailed
```

### Targeted Processing
```bash
# Process specific players
python main.py scrape-complete 12345678 87654321

# Process specific games that failed
python main.py scrape-replays 123456789:12345678 987654321:87654321

# Retry failed games for a player
python main.py scrape-complete 12345678 --retry-failed
```

### Debugging and Testing
```bash
# Check detailed status
python main.py status --detailed

# Process just a few players for testing
python main.py scrape-tables 12345678 87654321
```

## File Organization

The scraper organizes files as follows:

```
data/
├── raw/
│   └── {player_id}/
│       ├── table_{table_id}.html
│       └── replay_{table_id}.html
├── parsed/
│   └── {player_id}/
│       └── game_{table_id}.json
└── registry/
    ├── games.csv
    └── players.csv
```

## Registry Management

The games registry (`data/registry/games.csv`) tracks:
- **TableId**: BGA table ID
- **PlayerPerspective**: Which player's perspective the data was scraped from
- **IsArenaMode**: Whether the game is Arena mode
- **ScrapedAt**: When table and replay HTML were scraped
- **ParsedAt**: When the game was parsed to JSON
- **Version**: BGA version number for replay URLs

## Error Handling

- Failed operations are logged to `scraper.log`
- The registry tracks which games have been processed to avoid duplicates
- Use `--retry-failed` to reprocess games that previously failed

## Performance Tips

1. **Use `scrape-tables` first** to identify Arena games before full processing
2. **Process in batches** rather than all players at once to manage memory
3. **Use `parse` command** to process games that are already scraped
4. **Check `status`** regularly to monitor progress

## Configuration

Key configuration options in `config.py`:
- `REQUEST_DELAY`: Delay between requests (respect BGA's servers)
- `FILTER_ARENA_SEASON_21`: Whether to filter for specific Arena season
- `TOP_N_PLAYERS`: Default number of players for updates
- `RAW_DATA_DIR`, `PARSED_DATA_DIR`, `REGISTRY_DATA_DIR`: Data directories

## Migration from Old CLI

The new CLI replaces the old argument-based interface:

**Old:**
```bash
python main.py --loop-players --no-scrape
```

**New:**
```bash
python main.py scrape-tables --all
```

**Old:**
```bash
python main.py --loop-players
```

**New:**
```bash
python main.py scrape-complete --all
```

The new interface is more explicit about what each command does and provides better control over the workflow.

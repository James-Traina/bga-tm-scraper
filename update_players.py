#!/usr/bin/env python3
"""
Update Players Registry
Main script to fetch Arena Leaderboard data and update the players CSV registry
"""

import argparse
import logging
import sys
import os
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from bga_session import BGASession
from leaderboard_scraper import LeaderboardScraper
from players_registry import PlayersRegistry

# Import config
try:
    import config
except ImportError:
    print("Error: config.py not found. Please copy config.example.py to config.py and update with your credentials.")
    sys.exit(1)


def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def main():
    # Get config values with fallbacks
    default_player_count = getattr(config, 'DEFAULT_PLAYER_COUNT', 100)
    default_game_id = getattr(config, 'TERRAFORMING_MARS_GAME_ID', 1924)
    
    parser = argparse.ArgumentParser(description='Update Arena Leaderboard players registry')
    parser.add_argument('--players', '-n', type=int, default=default_player_count,
                       help=f'Number of top players to fetch (default: {default_player_count})')
    parser.add_argument('--output', '-o', default='data/processed/players.csv',
                       help='Output CSV file path (default: data/processed/players.csv)')
    parser.add_argument('--game-id', type=int, default=default_game_id,
                       help=f'BGA Game ID (default: {default_game_id} for Terraforming Mars)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--stats-only', action='store_true',
                       help='Only show registry statistics, do not update')
    
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    # Initialize registry
    registry = PlayersRegistry(args.output)
    
    if args.stats_only:
        # Show statistics only
        stats = registry.get_registry_stats()
        print("\n=== Players Registry Statistics ===")
        print(f"Total players: {stats['total_players']}")
        if stats['total_players'] > 0:
            print(f"Countries represented: {stats['countries_count']}")
            print(f"Rank range: {stats['rank_range'][0]} - {stats['rank_range'][1]}")
            print(f"Last update: {stats['last_update']}")
            print(f"\nTop countries:")
            for country, count in stats['top_countries']:
                print(f"  {country}: {count} players")
            
            print(f"\nTop 10 players:")
            top_players = registry.get_top_players(10)
            for player in top_players:
                print(f"  #{player['ArenaRank']}: {player['PlayerName']} ({player['Country']})")
        return
    
    # Validate credentials
    if not hasattr(config, 'BGA_EMAIL') or not hasattr(config, 'BGA_PASSWORD'):
        logger.error("BGA_EMAIL and BGA_PASSWORD must be set in config.py")
        sys.exit(1)
    
    if config.BGA_EMAIL == "your_email@example.com":
        logger.error("Please update BGA_EMAIL in config.py with your actual credentials")
        sys.exit(1)
    
    try:
        # Initialize BGA session
        logger.info("Initializing BGA session...")
        session = BGASession(config.BGA_EMAIL, config.BGA_PASSWORD)
        
        # Login
        if not session.login():
            logger.error("Failed to login to BGA")
            sys.exit(1)
        
        # Initialize scraper
        scraper = LeaderboardScraper(session)
        
        # Fetch players data
        logger.info(f"Fetching top {args.players} players for game ID {args.game_id}...")
        players_data = scraper.get_players_by_rank(args.game_id, args.players)
        
        if not players_data:
            logger.warning("No players data retrieved")
            return
        
        # Update registry
        logger.info(f"Updating players registry: {args.output}")
        update_stats = registry.update_players(players_data)
        
        # Print results
        print(f"\n=== Update Complete ===")
        print(f"Total players in registry: {update_stats['total_players']}")
        print(f"New players added: {update_stats['new_players']}")
        print(f"Players updated: {update_stats['updated_players']}")
        print(f"Players unchanged: {update_stats['unchanged_players']}")
        
        # Show top 10
        print(f"\nTop 10 players:")
        top_players = registry.get_top_players(10)
        for player in top_players:
            print(f"  #{player['ArenaRank']}: {player['PlayerName']} ({player['Country']})")
        
        logger.info("Players registry update completed successfully")
        
    except KeyboardInterrupt:
        logger.info("Update cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during update: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

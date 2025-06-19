"""
Script for scraping player game history
"""
import argparse
import logging
import json
import os
import csv
from datetime import datetime

from src.bga_session import BGASession

# Setup logging with UTF-8 encoding to handle Unicode characters (emojis)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('player_history_scraper.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def load_players_by_rank():
    """Load players from players.csv ordered by ArenaRank"""
    players = []
    try:
        with open('data/processed/players.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                players.append({
                    'player_id': row['PlayerId'],
                    'player_name': row['PlayerName'],
                    'country': row['Country'],
                    'arena_rank': int(row['ArenaRank'])
                })
        
        # Sort by arena rank (should already be sorted, but ensure it)
        players.sort(key=lambda x: x['arena_rank'])
        return players
    except FileNotFoundError:
        print("❌ players.csv not found in data/processed/")
        return []
    except Exception as e:
        print(f"❌ Error loading players.csv: {e}")
        return []

def get_player_summary_status(player_id):
    """Get player processing status from their summary file"""
    summary_file = f"data/processed/{player_id}/complete_summary.json"
    
    if not os.path.exists(summary_file):
        return None
    
    try:
        with open(summary_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error reading summary for player {player_id}: {e}")
        return None

def check_arena_games_parsed_in_registry(player_id, games_registry):
    """Check if all Arena games for this player perspective are parsed in the registry"""
    all_games = games_registry.get_all_games()
    
    for table_id, game_data in all_games.items():
        # Check if this game has the player's perspective and is Arena mode
        if (game_data.get('player_perspective') == player_id and 
            game_data.get('is_arena_mode', False) and 
            not game_data.get('parsed_at')):
            return False  # Found an unparsed Arena game
    
    return True  # All Arena games are parsed

def is_player_processed(player_id, mode, games_registry):
    """Check if a player has been fully processed based on the mode"""
    summary = get_player_summary_status(player_id)
    
    if not summary:
        return False  # No summary file means not processed
    
    # Check if discovery is complete
    discovery_completed = summary.get('discovery_completed', False)
    
    if mode == 'no_scrape':
        # In no-scrape mode, player is processed if discovery is complete
        # When discovery is complete, ALL discovered games have been table-only checked
        # (some may have been skipped as non-Arena, but they were still checked)
        return discovery_completed
    
    elif mode == 'normal':
        # In normal mode, player is processed if:
        # 1. Discovery is complete AND
        # 2. All discovered games are scraped AND
        # 3. All Arena games in registry with this player's perspective are parsed
        if not discovery_completed:
            return False
        
        total_discovered = summary.get('total_games_discovered', 0)
        successful_scrapes = summary.get('successful_scrapes', 0)
        all_scraped = total_discovered == successful_scrapes
        arena_games_parsed = check_arena_games_parsed_in_registry(player_id, games_registry)
        return all_scraped and arena_games_parsed
    
    return False

def save_player_summary(player_id, summary_data):
    """Save player summary to their folder with discovery status tracking"""
    player_dir = f"data/processed/{player_id}"
    os.makedirs(player_dir, exist_ok=True)
    
    summary_file = os.path.join(player_dir, "complete_summary.json")
    
    # Add discovery status fields if not present
    if 'discovery_completed' not in summary_data:
        # Determine if discovery is complete based on whether we have games_data
        games_data = summary_data.get('games_data', [])
        total_games_found = summary_data.get('total_games_found', 0)
        
        # Discovery is complete if we have game data and it matches total_games_found
        discovery_completed = len(games_data) > 0 and len(games_data) == total_games_found
        
        summary_data['discovery_completed'] = discovery_completed
        if discovery_completed:
            summary_data['discovery_completed_at'] = summary_data.get('scraped_at', datetime.now().isoformat())
        summary_data['total_games_discovered'] = len(games_data)
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)
    
    return summary_file

def process_all_missing_arena_replays(games_registry, raw_data_dir):
    """Process all missing Arena replays regardless of player (retry-checked-games mode)"""
    print("🔍 Retry-checked-games mode: Processing all missing Arena replays...")
    
    # Get all Arena games from registry that haven't been scraped yet
    all_registry_games = games_registry.get_all_games()
    unscraped_arena_games = []
    
    for table_id, game_data in all_registry_games.items():
        if (game_data.get('is_arena_mode', False) and 
            not game_data.get('scraped_at')):
            unscraped_arena_games.append(table_id)
    
    if not unscraped_arena_games:
        print("✅ No unscraped Arena games found in registry")
        return
    
    print(f"Found {len(unscraped_arena_games)} unscraped Arena games")
    
    # Use session-only approach for these games
    scraping_results, parsing_results = scrape_with_session_only(
        unscraped_arena_games, games_registry, raw_data_dir
    )
    
    # Display results
    successful_scrapes = len([r for r in scraping_results if r.get('success', False)])
    successful_parses = len([r for r in parsing_results if r.get('success', False)])
    
    print(f"\n✅ Retry processing complete!")
    print(f"   ✅ Successfully scraped: {successful_scrapes}")
    print(f"   ✅ Successfully parsed: {successful_parses}")

def scrape_with_session_only(table_ids_to_scrape, games_registry, raw_data_dir):
    """
    Scrape replays using session-only approach (no browser) for retry scenarios
    
    Args:
        table_ids_to_scrape: List of table IDs to process
        games_registry: Games registry instance
        raw_data_dir: Directory for raw HTML files
        
    Returns:
        tuple: (scraping_results, parsing_results)
    """
    try:
        # Import credentials
        from config import BGA_EMAIL, BGA_PASSWORD, REQUEST_DELAY
        
        # Initialize session
        print("🔐 Initializing session-only mode (no browser)...")
        session = BGASession(BGA_EMAIL, BGA_PASSWORD)
        
        if not session.login():
            print("❌ Session login failed")
            return [], []
        
        print("✅ Session login successful!")
        
        # Initialize parser
        from src.parser import Parser
        parser = Parser()
        
        scraping_results = []
        parsing_results = []
        
        for i, table_id in enumerate(table_ids_to_scrape, 1):
            print(f"\n--- Processing game {i}/{len(table_ids_to_scrape)} (table ID: {table_id}) ---")
            
            try:
                # Check if we can use direct fetch
                table_html_path = os.path.join(raw_data_dir, f"table_{table_id}.html")
                if not os.path.exists(table_html_path):
                    print(f"❌ Table HTML not found for {table_id}")
                    parsing_results.append({
                        'table_id': table_id,
                        'success': False,
                        'error': 'Table HTML not found'
                    })
                    continue
                
                # Get version and player ID from registry
                game_info = games_registry.get_game_info(table_id)
                if not game_info or not game_info.get('version'):
                    print(f"❌ Version not found for {table_id}")
                    parsing_results.append({
                        'table_id': table_id,
                        'success': False,
                        'error': 'Version not found'
                    })
                    continue
                
                version = game_info['version']
                
                # Read table HTML to get player ID
                with open(table_html_path, 'r', encoding='utf-8') as f:
                    table_html = f.read()
                
                # Extract player IDs from table HTML
                from src.scraper import TMScraper
                temp_scraper = TMScraper("", 0)  # Dummy scraper for ID extraction
                player_ids = temp_scraper.extract_player_ids_from_table(table_html)
                
                if not player_ids:
                    print(f"❌ No player IDs found for {table_id}")
                    parsing_results.append({
                        'table_id': table_id,
                        'success': False,
                        'error': 'No player IDs found'
                    })
                    continue
                
                player_id = player_ids[0]
                
                # Construct replay URL
                replay_url = f"https://boardgamearena.com/archive/replay/{version}/?table={table_id}&player={player_id}&comments={player_id}"
                print(f"🌐 Fetching replay via session: {replay_url}")
                
                # Fetch replay HTML directly
                response = session.get(replay_url, timeout=30)
                response.raise_for_status()
                
                replay_html = response.text
                print(f"✅ Fetched replay HTML ({len(replay_html)} chars)")
                
                # Check for replay limit
                if 'you have reached a limit' in replay_html.lower():
                    print("🚫 Replay limit reached!")
                    parsing_results.append({
                        'table_id': table_id,
                        'success': False,
                        'limit_reached': True,
                        'error': 'replay_limit_reached'
                    })
                    break
                
                # Save replay HTML to player perspective folder
                # Use the first player ID from the extracted player IDs as perspective
                player_perspective_dir = os.path.join(raw_data_dir, player_id)
                os.makedirs(player_perspective_dir, exist_ok=True)
                replay_html_path = os.path.join(player_perspective_dir, f"replay_{table_id}.html")
                with open(replay_html_path, 'w', encoding='utf-8') as f:
                    f.write(replay_html)
                
                # Create scraping result
                scraping_result = {
                    'table_id': table_id,
                    'scraped_at': datetime.now().isoformat(),
                    'success': True,
                    'session_only': True,
                    'table_data': {'from_file': True},
                    'replay_data': {
                        'url': replay_url,
                        'html_length': len(replay_html),
                        'direct_fetch': True
                    }
                }
                scraping_results.append(scraping_result)
                
                # Mark as scraped
                games_registry.mark_game_scraped(table_id)
                
                # Parse the game
                print(f"Parsing game {table_id}...")
                game_data = parser.parse_complete_game_with_elo(
                    replay_html=replay_html,
                    table_html=table_html,
                    table_id=table_id
                )
                
                # Export to JSON with player perspective
                output_path = f"data/parsed/game_{table_id}.json"
                parser.export_to_json(game_data, output_path, player_perspective=player_id)
                
                parsing_results.append({
                    'table_id': table_id,
                    'success': True,
                    'output_file': output_path,
                    'players_count': len(game_data.players),
                    'moves_count': len(game_data.moves),
                    'elo_data_included': game_data.metadata.get('elo_data_included', False),
                    'elo_players_found': game_data.metadata.get('elo_players_found', 0),
                    'session_only': True
                })
                
                print(f"✅ Successfully processed game {table_id} (session-only)")
                print(f"   Players: {len(game_data.players)}, Moves: {len(game_data.moves)}")
                
                # Mark as parsed
                games_registry.mark_game_parsed(table_id)
                
                # Update player info in registry
                if game_info:
                    player_ids_from_data = []
                    if hasattr(game_data, 'players') and isinstance(game_data.players, dict):
                        for pid, player_obj in game_data.players.items():
                            player_ids_from_data.append(str(player_obj.player_id))
                    game_info['players'] = player_ids_from_data
                
                # Save registry
                games_registry.save_registry()
                
                # Add delay between requests
                if i < len(table_ids_to_scrape):
                    print(f"Waiting {REQUEST_DELAY} seconds...")
                    import time
                    time.sleep(REQUEST_DELAY)
                
            except Exception as e:
                print(f"❌ Error processing {table_id}: {e}")
                parsing_results.append({
                    'table_id': table_id,
                    'success': False,
                    'error': str(e)
                })
        
        return scraping_results, parsing_results
        
    except Exception as e:
        print(f"❌ Error in session-only mode: {e}")
        return [], []

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Scrape BGA Terraforming Mars game history')
    parser.add_argument('--retry-checked-games', action='store_true',
                       help='Retry games that have been previously checked but not successfully scraped (default: skip all previously checked games)')
    parser.add_argument('--no-scrape', action='store_true',
                       help='Only scrape table page and add entry to games.csv (skip replay scraping)')
    parser.add_argument('--loop-players', action='store_true',
                       help='Loop through players in players.csv ordered by ArenaRank')
    args = parser.parse_args()
    
    retry_checked_games = args.retry_checked_games
    no_scrape = args.no_scrape
    
    # Try to import config
    try:
        from config import REQUEST_DELAY, RAW_DATA_DIR, CHROMEDRIVER_PATH
        logger.info("Configuration loaded successfully")
    except ImportError:
        logger.error("Could not import config.py. Please update config.py with ChromeDriver path.")
        print("\nTo get started:")
        print("1. Download ChromeDriver from https://chromedriver.chromium.org/")
        print("2. Update CHROMEDRIVER_PATH in config.py")
        print("3. Run this script again")
        return
    
    # Check if ChromeDriver path is configured
    if 'C:\\path\\to\\chromedriver.exe' in CHROMEDRIVER_PATH:
        print("\n❌ ChromeDriver path not configured!")
        print("Please:")
        print("1. Download ChromeDriver from https://chromedriver.chromium.org/")
        print("2. Update CHROMEDRIVER_PATH in config.py")
        return
    
    # Import scraper module
    from src.scraper import TMScraper
    from src.games_registry import GamesRegistry
    
    # Initialize games registry
    print("\n📋 Loading master games registry...")
    games_registry = GamesRegistry()
    games_registry.print_stats()
    
    # Create data directories
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    os.makedirs('data/processed', exist_ok=True)
    
    filter_arena_season_21 = True
    
    if filter_arena_season_21:
        print("🎯 Arena season 21 filtering enabled - only games from 2025-04-08 to 2025-07-08 will be included")
    else:
        print("📅 No date filtering - all games will be included")
    
    # Handle different modes
    if args.loop_players:
        if retry_checked_games:
            # Special case: retry mode processes all missing Arena replays regardless of player
            process_all_missing_arena_replays(games_registry, RAW_DATA_DIR)
            return
        
        # Load players and process them in order
        print("\n👥 Loading players from players.csv...")
        players = load_players_by_rank()
        
        if not players:
            print("❌ No players found or error loading players.csv")
            return
        
        print(f"Found {len(players)} players to process")
        
        # Determine processing mode for status checking
        mode = 'no_scrape' if no_scrape else 'normal'
        
        processed_count = 0
        for i, player in enumerate(players, 1):
            player_id = player['player_id']
            player_name = player['player_name']
            arena_rank = player['arena_rank']
            
            print(f"\n--- Player {i}/{len(players)}: {player_name} (ID: {player_id}, Rank: {arena_rank}) ---")
            
            # Check if player is already processed
            if is_player_processed(player_id, mode, games_registry):
                continue  # Skip silently as requested
            
            print(f"🎯 Processing player {player_name} (Rank {arena_rank})...")
            
            try:
                # Process this player using the existing single-player logic
                success = process_single_player(player_id, retry_checked_games, no_scrape, 
                                              filter_arena_season_21, games_registry, 
                                              RAW_DATA_DIR, CHROMEDRIVER_PATH, REQUEST_DELAY)
                
                if success:
                    processed_count += 1
                    print(f"✅ Successfully processed player {player_name}")
                else:
                    # Check if we hit replay limit
                    if success is False:  # Explicit False means replay limit hit
                        print(f"🚫 Replay limit reached while processing {player_name}")
                        print("Stopping player loop to respect BGA's daily limits.")
                        break
                    else:
                        print(f"⚠️ Failed to process player {player_name}")
                
            except Exception as e:
                print(f"❌ Error processing player {player_name}: {e}")
                continue
        
        print(f"\n✅ Player loop complete! Processed {processed_count} players.")
        return
    
    else:
        # Original single-player mode
        player_id = input("Enter the BGA player ID to scrape game history for: ").strip()
        if not player_id:
            print("❌ No player ID provided!")
            return
        
        # Process single player
        process_single_player(player_id, retry_checked_games, no_scrape, 
                            filter_arena_season_21, games_registry, 
                            RAW_DATA_DIR, CHROMEDRIVER_PATH, REQUEST_DELAY)

def process_single_player(player_id, retry_checked_games, no_scrape, filter_arena_season_21, 
                         games_registry, raw_data_dir, chromedriver_path, request_delay):
    """Process a single player's game history. Returns True on success, False on replay limit, None on other errors."""
    
    # Import scraper here to avoid circular imports
    from src.scraper import TMScraper
    
    # Check if we can use session-only mode for retry scenarios (before starting browser)
    use_session_only = False
    if retry_checked_games and not no_scrape:
        print("\n🔍 Checking if session-only mode is possible...")
        
        # Get all games from registry that haven't been scraped yet
        all_registry_games = games_registry.get_all_games()
        unscraped_games = []
        
        for table_id, game_data in all_registry_games.items():
            # Only include games that haven't been scraped yet (for retry mode)
            if not game_data.get('scraped_at'):
                unscraped_games.append({
                    'table_id': table_id,
                    'raw_datetime': game_data.get('raw_datetime', ''),
                    'parsed_datetime': game_data.get('parsed_datetime', ''),
                    'date_type': 'registry'
                })
        
        if unscraped_games:
            print(f"Found {len(unscraped_games)} unscraped games in registry")
            
            # Check if all unscraped games can use session-only approach
            can_use_session_only = True
            for game in unscraped_games:
                table_id = game['table_id']
                table_html_path = os.path.join(RAW_DATA_DIR, f"table_{table_id}.html")
                game_info = games_registry.get_game_info(table_id)
                
                if not os.path.exists(table_html_path) or not game_info or not game_info.get('version'):
                    can_use_session_only = False
                    break
            
            if can_use_session_only and unscraped_games:
                print("✅ All unscraped games have table HTML and version numbers!")
                print("🚀 Using session-only mode (no browser needed)...")
                
                # Extract table IDs for session-only processing
                table_ids_to_scrape = [game['table_id'] for game in unscraped_games]
                
                # Use session-only approach
                scraping_results, parsing_results = scrape_with_session_only(
                    table_ids_to_scrape, games_registry, RAW_DATA_DIR
                )
                
                use_session_only = True
                print(f"\n✅ Session-only processing complete!")
                
                # Calculate and display statistics
                successful_scrapes = len([r for r in scraping_results if r.get('success', False)])
                successful_parses = len([r for r in parsing_results if r.get('success', False)])
                
                print(f"   ✅ Successfully scraped: {successful_scrapes}")
                print(f"   ✅ Successfully parsed: {successful_parses}")
                
                # Save the updated registry
                print(f"\n💾 Saving updated master games registry...")
                games_registry.save_registry()
                games_registry.print_stats()
                
                return True  # Success
            else:
                print("❌ Some games missing table HTML or version numbers")
                print("🌐 Will use browser mode for missing data...")
        else:
            print("No unscraped games found in registry")
    
    # Initialize scraper (only if we're not using session-only mode)
    if not use_session_only:
        scraper = TMScraper(
            chromedriver_path=chromedriver_path,
            request_delay=request_delay,
            headless=False  # Keep browser visible for manual login
        )
        
        try:
            # Start browser and perform automated login
            if not scraper.start_browser_and_login():
                print("❌ Failed to start browser and login automatically")
                print("Falling back to manual login...")
                
                # Fallback to manual login if automated login fails
                scraper.start_browser()
                scraper.login_to_bga()
            
            # Scrape player game history with datetime information
            print(f"\n🎯 Starting to scrape game history for player {player_id}...")
            print("Note: Extracting table IDs and datetimes. Only Arena mode games will be processed during scraping.")
            games_data = scraper.scrape_player_game_history(
                player_id=player_id,
                max_clicks=50,  # Reasonable limit
                click_delay=1,  # 1 second between clicks
                filter_arena_season_21=filter_arena_season_21
            )
            
            if games_data:
                print(f"\n✅ Successfully found {len(games_data)} games with datetime information!")
                print("Games found (showing first 10):")
                for i, game in enumerate(games_data, 1):
                    print(f"  {i}. Table ID: {game['table_id']}")
                    print(f"     Date: {game['raw_datetime']} ({game['date_type']})")
                    if game['parsed_datetime']:
                        print(f"     Parsed: {game['parsed_datetime']}")
                    print()
            
            if len(games_data) > 10:
                print(f"  ... and {len(games_data) - 10} more games")
            
            # Save results to file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Note: We'll add games to registry only when we actually visit each table page
            print(f"\n📝 Games will be added to registry when visited (retry mode: {'ON' if retry_checked_games else 'OFF'})...")
            
            # Filter games based on retry setting
            if retry_checked_games:
                print(f"\n🔍 Retry mode: Checking for already scraped games...")
                new_games = games_registry.filter_new_games(games_data)  # Only skip scraped
                filter_type = "scraped"
            else:
                print(f"\n🔍 Standard mode: Checking for already checked games...")
                new_games = games_registry.filter_unchecked_games(games_data)  # Skip all checked
                filter_type = "checked"
            
            already_processed = len(games_data) - len(new_games)
            
            if already_processed > 0:
                print(f"⏭️  Found {already_processed} games already {filter_type} - skipping")
                print(f"📋 {len(new_games)} new games to process")
            else:
                print(f"📋 All {len(games_data)} games are new - proceeding with full processing")
            
            if not new_games:
                print(f"✅ No new games to process - all games already {filter_type}!")
                games_registry.print_stats()
                return True  # Success - no work needed
           
            table_ids_to_scrape = [game['table_id'] for game in new_games]
            
            # Check if we can use session-only mode for retry scenarios
            if retry_checked_games and not no_scrape:
                # Check if all games can use session-only approach
                can_use_session_only = True
                for table_id in table_ids_to_scrape:
                    table_html_path = os.path.join(RAW_DATA_DIR, f"table_{table_id}.html")
                    game_info = games_registry.get_game_info(table_id)
                    
                    if not os.path.exists(table_html_path) or not game_info or not game_info.get('version'):
                        can_use_session_only = False
                        break
                
                if can_use_session_only:
                    print("\n🚀 Using session-only mode (no browser needed)...")
                    print("All games have table HTML and version numbers - skipping browser entirely!")
                    
                    # Close browser since we don't need it
                    scraper.close_browser()
                    
                    # Use session-only approach
                    scraping_results, parsing_results = scrape_with_session_only(
                        table_ids_to_scrape, games_registry, RAW_DATA_DIR
                    )
                    
                    # Skip the normal processing loop
                    print(f"\n✅ Session-only processing complete!")
                else:
                    print("\n🚀 Some games need browser mode - using hybrid approach...")
                    # Fall through to normal processing
            
            # Normal processing (browser-based or hybrid)
            if not (retry_checked_games and not no_scrape and 'scraping_results' in locals()):
                if no_scrape:
                    print("\n🚀 Starting table-only scraping (--no-scrape mode)...")
                else:
                    print("\n🚀 Starting to scrape and parse games...")
                
                # Initialize parser
                from src.parser import Parser
                parser = Parser()
                
                scraping_results = []
                parsing_results = []
                
                for i, table_id in enumerate(table_ids_to_scrape, 1):
                    print(f"\n--- Processing game {i}/{len(table_ids_to_scrape)} (table ID: {table_id}) ---")
                    
                    # Add game to registry now that we're actually visiting it
                    game_info = next((game for game in new_games if game['table_id'] == table_id), None)
                    if game_info:
                        games_registry.add_game_check(
                            table_id=table_id,
                            raw_datetime=game_info['raw_datetime'],
                            parsed_datetime=game_info['parsed_datetime'],
                            players=[],  # Will be populated after processing
                            is_arena_mode=True,  # Assume arena mode since we're filtering for it
                            player_perspective=player_id  # Add player perspective
                        )
                        games_registry.save_registry()  # Save immediately
                        print(f"📋 Added game {table_id} to registry")
                    
                    # Choose scraping method based on --no-scrape flag
                    if no_scrape:
                        print(f"Scraping table only for game {table_id}...")
                        scraping_result = scraper.scrape_table_only(
                            table_id=table_id,
                            player_perspective=player_id,  # Use the player ID as perspective
                            save_raw=True,
                            raw_data_dir=raw_data_dir
                        )
                    else:
                        print(f"Scraping game {table_id}...")
                        # Use smart mode that automatically chooses between direct fetch and browser scraping
                        scraping_result = scraper.scrape_table_and_replay(
                            table_id=table_id,
                            player_perspective=player_id,  # Use the player ID as perspective
                            save_raw=True,
                            raw_data_dir=raw_data_dir
                        )
                    
                    if scraping_result:
                        scraping_results.append(scraping_result)
                        
                        # Check for replay limit reached
                        replay_data = scraping_result.get('replay_data', {})
                        if replay_data and replay_data.get('limit_reached', False):
                            print("🚫 REPLAY LIMIT REACHED!")
                            print("   Stopping scraping process to respect BGA's daily limits.")
                            print("   Please try again tomorrow when the limit resets.")
                            
                            # Mark this in parsing results
                            parsing_results.append({
                                'table_id': table_id,
                                'success': False,
                                'limit_reached': True,
                                'error': 'replay_limit_reached'
                            })
                            
                            # Save progress and exit gracefully
                            print(f"\n💾 Saving progress before stopping...")
                            games_registry.save_registry()
                            return False  # Return False to indicate replay limit hit
                        
                        # Handle different scraping results
                        if scraping_result.get('success', False):
                            print(f"✅ Successfully scraped game {table_id}")
                            
                            # Handle table-only scraping (--no-scrape mode)
                            if no_scrape and scraping_result.get('table_only', False):
                                # Extract player info and add to CSV directly
                                player_ids = scraping_result.get('player_ids', [])
                                is_arena_mode = scraping_result.get('arena_mode', False)
                                version = scraping_result.get('version')
                                
                                # Update registry with player info, arena mode status, and version
                                if games_registry.is_game_checked(table_id, player_perspective=player_id):
                                    game_info = games_registry.get_game_info(table_id, player_perspective=player_id)
                                    if game_info:
                                        game_info['players'] = player_ids
                                        game_info['is_arena_mode'] = is_arena_mode
                                        game_info['version'] = version
                                
                                # Add to CSV (games.csv will be updated by the registry)
                                version_text = f"Version: {version}" if version else "No version"
                                print(f"📊 Added game {table_id} to CSV - Arena mode: {'✅' if is_arena_mode else '❌'}, Players: {len(player_ids)}, {version_text}")
                                
                                # Add to parsing results as table-only success
                                parsing_results.append({
                                    'table_id': table_id,
                                    'success': True,
                                    'table_only': True,
                                    'arena_mode': is_arena_mode,
                                    'players_count': len(player_ids),
                                    'version': version,
                                    'elo_data_included': len(scraping_result.get('elo_data', {})) > 0
                                })
                                
                                # Save registry immediately
                                games_registry.save_registry()
                                print(f"💾 Registry saved with {games_registry.get_stats()['total_games']} total games")
                                continue  # Skip to next game (no replay parsing needed)
                            else:
                                # Normal scraping mode - mark as scraped and continue to parsing
                                games_registry.mark_game_scraped(table_id)
                                print(f"Parsing game {table_id}...")
                        elif scraping_result.get('skipped', False):
                            skip_reason = scraping_result.get('skip_reason', 'unknown')
                            if skip_reason == 'not_arena_mode':
                                print(f"⏭️  Skipped game {table_id} - Not Arena mode")
                                # Update arena mode status in registry
                                if games_registry.is_game_checked(table_id):
                                    game_info = games_registry.get_game_info(table_id)
                                    if game_info:
                                        game_info['is_arena_mode'] = False
                            elif skip_reason == 'not_arena_season_21':
                                print(f"⏭️  Skipped game {table_id} - Outside Arena season 21 date range")
                            else:
                                print(f"⏭️  Skipped game {table_id} - {skip_reason}")
                            
                            # Add to parsing results as skipped
                            parsing_results.append({
                                'table_id': table_id,
                                'success': False,
                                'skipped': True,
                                'skip_reason': skip_reason
                            })
                            continue  # Skip to next game
                        else:
                            print(f"✅ Successfully scraped game {table_id}")
                            
                            # Mark game as scraped in registry
                            games_registry.mark_game_scraped(table_id)
                            
                            # Parse immediately after scraping
                            print(f"Parsing game {table_id}...")
                        try:
                            # Read the HTML files
                            table_html_path = os.path.join(RAW_DATA_DIR, f"table_{table_id}.html")
                            replay_html_path = os.path.join(RAW_DATA_DIR, f"replay_{table_id}.html")
                            
                            if os.path.exists(table_html_path) and os.path.exists(replay_html_path):
                                with open(table_html_path, 'r', encoding='utf-8') as f:
                                    table_html = f.read()
                                
                                with open(replay_html_path, 'r', encoding='utf-8') as f:
                                    replay_html = f.read()
                                
                                # Parse with ELO data
                                game_data = parser.parse_complete_game_with_elo(
                                    replay_html=replay_html,
                                    table_html=table_html,
                                    table_id=table_id
                                )
                                
                                # Export to JSON with player perspective
                                output_path = f"data/parsed/game_{table_id}.json"
                                parser.export_to_json(game_data, output_path, player_perspective=player_id)
                                
                                parsing_results.append({
                                    'table_id': table_id,
                                    'success': True,
                                    'output_file': output_path,
                                    'players_count': len(game_data.players),
                                    'moves_count': len(game_data.moves),
                                    'elo_data_included': game_data.metadata.get('elo_data_included', False),
                                    'elo_players_found': game_data.metadata.get('elo_players_found', 0)
                                })
                                
                                print(f"✅ Successfully parsed and saved game {table_id}")
                                print(f"   Players: {len(game_data.players)}, Moves: {len(game_data.moves)}, ELO: {'✅' if game_data.metadata.get('elo_data_included', False) else '❌'}")
                                
                                # Mark game as parsed in registry
                                games_registry.mark_game_parsed(table_id)
                                
                                # Update player information in registry
                                if games_registry.is_game_checked(table_id):
                                    game_info = games_registry.get_game_info(table_id)
                                    if game_info:
                                        # Extract player IDs from parsed data
                                        player_ids = []
                                        if hasattr(game_data, 'players') and isinstance(game_data.players, dict):
                                            for pid, player_obj in game_data.players.items():
                                                player_ids.append(str(player_obj.player_id))
                                        else:
                                            # Fallback for different data structure
                                            for player in game_data.players:
                                                pid = getattr(player, 'player_id', None)
                                                if pid:
                                                    player_ids.append(str(pid))
                                        
                                        # Update players in registry
                                        game_info['players'] = player_ids
                                
                                print(f"📋 Updated game {table_id} in master registry")
                                
                                # Save registry immediately after each game
                                games_registry.save_registry()
                                print(f"💾 Registry saved with {games_registry.get_stats()['total_games']} total games")
                                
                            else:
                                print(f"❌ Missing HTML files for game {table_id}")
                                parsing_results.append({
                                    'table_id': table_id,
                                    'success': False,
                                    'error': 'Missing HTML files'
                                })
                                
                        except Exception as e:
                            print(f"❌ Error parsing game {table_id}: {e}")
                            parsing_results.append({
                                'table_id': table_id,
                                'success': False,
                                'error': str(e)
                            })
                    else:
                        print(f"❌ Failed to scrape game {table_id}")
                        parsing_results.append({
                            'table_id': table_id,
                            'success': False,
                            'error': 'Scraping failed'
                        })
                    
                    # Add delay between games (except for the last one)
                    if i < len(table_ids_to_scrape):
                        print(f"Waiting {REQUEST_DELAY} seconds before next game...")
                        import time
                        time.sleep(REQUEST_DELAY)
            
            print(f"\n✅ Processing complete!")
            
            # Calculate statistics
            successful_scrapes = len([r for r in scraping_results if r.get('success', False)])
            skipped_games = len([r for r in scraping_results if r.get('skipped', False)])
            failed_scrapes = len([r for r in scraping_results if not r.get('success', False) and not r.get('skipped', False)])
            successful_parses = len([r for r in parsing_results if r.get('success', False)])
            skipped_parses = len([r for r in parsing_results if r.get('skipped', False)])
            failed_parses = len([r for r in parsing_results if not r.get('success', False) and not r.get('skipped', False)])
            
            print(f"   ✅ Successfully scraped: {successful_scrapes}")
            print(f"   ⏭️  Skipped: {skipped_games}")
            print(f"   ❌ Failed: {failed_scrapes}")
            print(f"   ✅ Successfully parsed: {successful_parses}")
            
            clean_scraping_results = []
            for result in scraping_results:
                clean_result = {
                    'table_id': result['table_id'],
                    'scraped_at': result['scraped_at'],
                    'success': result['success']
                }
                
                if result.get('skipped', False):
                    clean_result['skipped'] = True
                    clean_result['skip_reason'] = result.get('skip_reason', 'unknown')
                
                if 'table_data' in result and result['table_data']:
                    clean_result['table_data'] = {
                        'url': result['table_data'].get('url'),
                        'players_found': result['table_data'].get('players_found', []),
                        'elo_data_found': result['table_data'].get('elo_data_found', False),
                        'html_length': result['table_data'].get('html_length', 0)
                    }
                
                if 'replay_data' in result and result['replay_data']:
                    clean_result['replay_data'] = {
                        'url': result['replay_data'].get('url'),
                        'title': result['replay_data'].get('title'),
                        'players': result['replay_data'].get('players', []),
                        'game_logs_found': result['replay_data'].get('game_logs_found', False),
                        'num_moves': result['replay_data'].get('num_moves', 0),
                        'html_length': result['replay_data'].get('html_length', 0)
                    }
                
                clean_scraping_results.append(clean_result)
            
            # Save comprehensive summary to player folder
            scraping_summary = {
                'player_id': player_id,
                'scraped_at': datetime.now().isoformat(),
                'total_games_found': len(games_data),
                'games_scraped': len(table_ids_to_scrape),
                'successful_scrapes': successful_scrapes,
                'skipped_games': skipped_games,
                'failed_scrapes': failed_scrapes,
                'successful_parses': successful_parses,
                'games_data': games_data,  # Include datetime info for processed games
                'scraping_results': clean_scraping_results,
                'parsing_results': parsing_results
            }
            
            scraping_summary_file = save_player_summary(player_id, scraping_summary)
            print(f"💾 Complete summary saved to: {scraping_summary_file}")
            
            # Print detailed summary
            print(f"\n=== Complete Processing Summary ===")
            print(f"Total games found: {len(games_data)}")
            print(f"✅ Successfully scraped: {successful_scrapes}")
            print(f"⏭️  Skipped: {skipped_games}")
            print(f"❌ Failed: {failed_scrapes}")
            print(f"✅ Successfully parsed: {successful_parses}")
            print(f"Games with ELO data: {len([r for r in parsing_results if r.get('elo_data_included', False)])}")
            
            for result in parsing_results:
                if result.get('success', False):
                    if result.get('table_only', False):
                        # Table-only result (--no-scrape mode)
                        print(f"\nGame {result['table_id']} (table-only):")
                        print(f"  Arena mode: {'✅' if result.get('arena_mode', False) else '❌'}")
                        print(f"  Players: {result['players_count']}")
                        print(f"  ELO data: {'✅' if result['elo_data_included'] else '❌'}")
                        print(f"  Added to CSV: ✅")
                    else:
                        # Full parsing result
                        print(f"\nGame {result['table_id']}:")
                        print(f"  Players: {result['players_count']}")
                        print(f"  Moves: {result['moves_count']}")
                        print(f"  ELO data: {'✅' if result['elo_data_included'] else '❌'}")
                        if result['elo_data_included']:
                            print(f"  ELO players: {result['elo_players_found']}")
                        print(f"  Output: {result['output_file']}")
                elif result.get('skipped', False):
                    skip_reason = result.get('skip_reason', 'unknown')
                    print(f"\nGame {result['table_id']}: ⏭️  Skipped - {skip_reason}")
                else:
                    print(f"\nGame {result['table_id']}: ❌ Failed - {result.get('error', 'Unknown error')}")
            
            # Save the updated registry
            print(f"\n💾 Saving updated master games registry...")
            games_registry.save_registry()
            games_registry.print_stats()
            
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            print(f"❌ Error during scraping: {e}")
        
        finally:
            # Always close browser
            print("\nClosing browser...")
            scraper.close_browser()
    
    return True  # Default success return

if __name__ == "__main__":
    main()

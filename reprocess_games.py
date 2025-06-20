#!/usr/bin/env python3
"""
Game Reprocessor Script
Fetch missing replay HTML for games that only have table HTML and complete the processing
"""

import argparse
import os
import sys
import logging
from typing import List, Optional, Tuple
from datetime import datetime
import time

import config


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def setup_directories():
    """Ensure required directories exist"""
    directories = [config.RAW_DATA_DIR, config.PARSED_DATA_DIR]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def parse_composite_key(composite_key: str) -> Tuple[str, str]:
    """Parse composite key into game_id and player_perspective"""
    if ':' in composite_key:
        parts = composite_key.split(':', 1)
        return parts[0], parts[1]
    else:
        raise ValueError(f"Invalid composite key format: {composite_key}. Expected format: game_id:player_perspective")

def check_game_status(game_id: str, player_perspective: str) -> dict:
    """Check the current status of a game's files"""
    table_path = os.path.join(config.RAW_DATA_DIR, player_perspective, f"table_{game_id}.html")
    replay_path = os.path.join(config.RAW_DATA_DIR, player_perspective, f"replay_{game_id}.html")
    
    status = {
        'table_exists': os.path.exists(table_path),
        'replay_exists': os.path.exists(replay_path),
        'table_path': table_path,
        'replay_path': replay_path,
        'needs_reprocessing': False
    }
    
    # Game needs reprocessing if table exists but replay doesn't
    status['needs_reprocessing'] = status['table_exists'] and not status['replay_exists']
    
    return status

def extract_version_from_gamereview_session(table_id: str, session):
    """
    Extract version number from gamereview page using session
    
    Args:
        table_id: BGA table ID
        session: BGASession instance
        
    Returns:
        str: Version number (e.g., "250505-1448") or None if not found
    """
    import re
    
    gamereview_url = f"https://boardgamearena.com/gamereview?table={table_id}"
    logger.info(f"Extracting version from gamereview page: {gamereview_url}")
    
    try:
        print(f"🌐 Fetching gamereview page: {gamereview_url}")
        
        # Get the underlying requests session from BGASession
        requests_session = session.get_session()
        
        # Fetch the gamereview page
        response = requests_session.get(gamereview_url, timeout=30)
        response.raise_for_status()
        
        html_content = response.text
        print(f"✅ Fetched gamereview HTML ({len(html_content)} chars)")
        
        # Check for authentication errors
        if 'must be logged' in html_content.lower():
            print("❌ Authentication error - session may have expired")
            return None
        
        if 'fatal error' in html_content.lower():
            print("❌ Fatal error on page - gamereview might not be accessible")
            return None
        
        # Try multiple extraction patterns in order of reliability
        version = extract_version_with_multiple_patterns(html_content, table_id)
        
        if version:
            logger.info(f"Successfully extracted version: {version}")
            print(f"✅ Found version number: {version}")
            return version
        else:
            logger.warning(f"No version number found in gamereview page for table {table_id}")
            print("⚠️  No version number found in gamereview page")
            return None
        
    except Exception as e:
        logger.error(f"Error extracting version from gamereview for {table_id}: {e}")
        print(f"❌ Error extracting version: {e}")
        return None

def extract_version_with_multiple_patterns(html_content: str, table_id: str) -> Optional[str]:
    """
    Extract version number using multiple patterns in order of reliability
    
    Args:
        html_content: HTML content of the gamereview page
        table_id: Table ID for logging purposes
        
    Returns:
        str: Version number if found, None otherwise
    """
    import re
    
    logger.debug(f"Trying multiple version extraction patterns for table {table_id}")
    
    # Pattern definitions in order of reliability (most reliable first)
    patterns = [
        # Pattern 1: Direct replay links (most reliable)
        (r'/archive/replay/(\d{6}-\d{4})/', "Direct replay links"),
        
        # Pattern 2: JavaScript variables
        (r'version["\']?\s*:\s*["\'](\d{6}-\d{4})["\']', "JavaScript variables"),
        
        # Pattern 3: JSON data
        (r'"version"\s*:\s*"(\d{6}-\d{4})"', "JSON data"),
        
        # Pattern 4: URL parameters
        (r'[?&]version=(\d{6}-\d{4})', "URL parameters"),
        
        # Pattern 5: Data attributes
        (r'data-version=["\'](\d{6}-\d{4})["\']', "Data attributes"),
        
        # Pattern 6: Hidden form fields
        (r'<input[^>]*name=["\']version["\'][^>]*value=["\'](\d{6}-\d{4})["\']', "Hidden form fields"),
        
        # Pattern 7: Meta tags
        (r'<meta[^>]*content=["\'](\d{6}-\d{4})["\']', "Meta tags"),
        
        # Pattern 8: Game data objects
        (r'gamedata[^}]*version["\']?\s*:\s*["\'](\d{6}-\d{4})["\']', "Game data objects"),
    ]
    
    # Try each pattern
    for pattern, description in patterns:
        try:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            if matches:
                # Remove duplicates and get the first unique match
                unique_matches = list(dict.fromkeys(matches))  # Preserves order
                version = unique_matches[0]
                
                logger.info(f"Version found using {description}: {version}")
                logger.debug(f"Pattern '{description}' found {len(matches)} total matches, using first unique: {version}")
                
                # Validate the version format (6 digits, dash, 4 digits)
                if re.match(r'^\d{6}-\d{4}$', version):
                    return version
                else:
                    logger.warning(f"Invalid version format from {description}: {version}")
                    continue
                    
        except Exception as e:
            logger.debug(f"Error with pattern '{description}': {e}")
            continue
    
    # If no specific patterns worked, try a broader search as last resort
    logger.debug("Trying broader version pattern search as fallback")
    try:
        # Look for any 6-digit-4-digit pattern
        broad_matches = re.findall(r'(\d{6}-\d{4})', html_content)
        if broad_matches:
            # Remove duplicates and get the first one
            unique_broad_matches = list(dict.fromkeys(broad_matches))
            version = unique_broad_matches[0]
            
            logger.info(f"Version found using broad pattern search: {version}")
            logger.debug(f"Broad search found {len(broad_matches)} total matches, using first unique: {version}")
            return version
            
    except Exception as e:
        logger.debug(f"Error with broad pattern search: {e}")
    
    logger.debug(f"No version number found using any pattern for table {table_id}")
    return None

def get_current_site_version_browser(driver):
    """
    Get the current site version from BGA main page using browser
    
    Args:
        driver: Selenium WebDriver instance
        
    Returns:
        str: Current site version or None if not found
    """
    try:
        print("🔍 Getting current site version from BGA using browser...")
        
        # Try to get version from main page
        driver.get("https://boardgamearena.com")
        time.sleep(2)
        
        html_content = driver.page_source
        
        # Look for version in the main page using the same patterns
        version = extract_version_with_multiple_patterns(html_content, "main_page")
        
        if version:
            print(f"✅ Found current site version: {version}")
            return version
        
        # Alternative: try to get version from any game page
        print("🔍 Trying to get version from a game page...")
        driver.get("https://boardgamearena.com/gamepanel?game=terraformingmars")
        time.sleep(2)
        
        html_content = driver.page_source
        version = extract_version_with_multiple_patterns(html_content, "game_page")
        
        if version:
            print(f"✅ Found current site version from game page: {version}")
            return version
        
        print("⚠️  Could not find current site version")
        return None
        
    except Exception as e:
        print(f"❌ Error getting current site version: {e}")
        return None

def fetch_replay_html(game_id: str, player_perspective: str, version: str, session) -> Optional[str]:
    """
    Fetch replay HTML using BGASession
    
    Args:
        game_id: BGA table ID
        player_perspective: Player ID for perspective
        version: Site version for replay URL
        session: BGASession instance
        
    Returns:
        str: Replay HTML content or None if failed
    """
    try:
        # Construct replay URL
        replay_url = f"https://boardgamearena.com/archive/replay/{version}/?table={game_id}&player={player_perspective}&comments={player_perspective}"
        print(f"🌐 Fetching replay via browser: {replay_url}")
        
        # Get the browser driver from BGASession
        driver = session.get_driver()
        
        # Navigate to replay page using browser
        driver.get(replay_url)
        time.sleep(3)  # Wait for page to load
        
        # Get the fully rendered HTML
        replay_html = driver.page_source
        print(f"✅ Fetched replay HTML via browser ({len(replay_html)} chars)")
        
        # Check for replay limit
        if 'you have reached a limit' in replay_html.lower():
            print("🚫 Replay limit reached!")
            return None
        
        # Check for authentication errors
        if 'must be logged' in replay_html.lower():
            print("❌ Authentication error - session may have expired")
            return None
        
        # Check for "Wrong siteversion" error
        if 'wrong siteversion' in replay_html.lower() or 'fatalerror' in replay_html.lower():
            print(f"⚠️  Wrong siteversion error with version {version}, trying to get current version...")
            
            # Try to get the current version from the main site using browser
            current_version = get_current_site_version_browser(driver)
            if current_version and current_version != version:
                print(f"🔄 Retrying with current site version: {current_version}")
                
                # Retry with current version using browser
                retry_url = f"https://boardgamearena.com/archive/replay/{current_version}/?table={game_id}&player={player_perspective}&comments={player_perspective}"
                print(f"🌐 Retrying with browser: {retry_url}")
                
                driver.get(retry_url)
                time.sleep(3)
                
                replay_html = driver.page_source
                print(f"✅ Retry successful ({len(replay_html)} chars)")
                
                return replay_html
            else:
                print(f"❌ Could not get current site version or it's the same as extracted version")
                return None
        
        return replay_html
        
    except Exception as e:
        logger.error(f"Error fetching replay HTML for {game_id}: {e}")
        print(f"❌ Error fetching replay HTML: {e}")
        return None

def reprocess_single_game(composite_key: str, games_registry, session) -> dict:
    """
    Reprocess a single game by fetching missing replay HTML and parsing
    
    Args:
        composite_key: Game ID and player perspective (game_id:player_perspective)
        games_registry: Games registry instance
        session: BGASession instance
        
    Returns:
        dict: Processing result
    """
    try:
        # Parse composite key
        game_id, player_perspective = parse_composite_key(composite_key)
        
        result = {
            'game_id': composite_key,
            'success': False,
            'error': None,
            'output_file': None,
            'players_count': 0,
            'moves_count': 0,
            'elo_data_included': False,
            'fetched_replay': False,
            'version_extracted': False
        }
        
        print(f"🔄 Reprocessing game {game_id} (perspective: {player_perspective})")
        
        # Check game status
        status = check_game_status(game_id, player_perspective)
        
        if not status['table_exists']:
            result['error'] = f"Table HTML not found: {status['table_path']}"
            return result
        
        if status['replay_exists']:
            result['error'] = f"Replay HTML already exists: {status['replay_path']}. Use reparse_games.py instead."
            return result
        
        if not status['needs_reprocessing']:
            result['error'] = "Game does not need reprocessing"
            return result
        
        print(f"📁 Table HTML found: {status['table_path']}")
        print(f"❌ Replay HTML missing: {status['replay_path']}")
        
        # Get version from registry or extract it
        game_info = games_registry.get_game_info(game_id, player_perspective)
        version = None
        
        if game_info and game_info.get('version'):
            version = game_info['version']
            print(f"✅ Using version from registry: {version}")
        else:
            print(f"⚠️  Version not found in registry, extracting from gamereview...")
            version = extract_version_from_gamereview_session(game_id, session)
            
            if version:
                # Update registry with extracted version
                if game_info:
                    game_info['version'] = version
                else:
                    # Create minimal entry if game doesn't exist in registry
                    games_registry.add_game_check(
                        table_id=game_id,
                        raw_datetime='',
                        parsed_datetime='',
                        players=[],
                        is_arena_mode=True,
                        version=version,
                        player_perspective=player_perspective
                    )
                
                games_registry.save_registry()
                result['version_extracted'] = True
                print(f"✅ Updated registry with version {version}")
            else:
                result['error'] = f"Could not extract version for game {game_id}"
                return result
        
        # Fetch replay HTML
        replay_html = fetch_replay_html(game_id, player_perspective, version, session)
        
        if not replay_html:
            result['error'] = "Failed to fetch replay HTML"
            return result
        
        result['fetched_replay'] = True
        
        # Save replay HTML
        os.makedirs(os.path.dirname(status['replay_path']), exist_ok=True)
        with open(status['replay_path'], 'w', encoding='utf-8') as f:
            f.write(replay_html)
        
        print(f"💾 Saved replay HTML: {status['replay_path']}")
        
        # Mark as scraped in registry
        games_registry.mark_game_scraped(game_id, player_perspective=player_perspective)
        
        # Read table HTML
        with open(status['table_path'], 'r', encoding='utf-8') as f:
            table_html = f.read()
        
        # Parse the complete game
        from bga_tm_scraper.parser import Parser
        parser = Parser()
        
        print(f"🔄 Parsing complete game {game_id}...")
        game_data = parser.parse_complete_game_with_elo(
            replay_html=replay_html,
            table_html=table_html,
            table_id=game_id,
            player_perspective=player_perspective
        )
        
        # Export to JSON
        output_path = os.path.join(config.PARSED_DATA_DIR, player_perspective, f"game_{game_id}.json")
        print(f"💾 Saving to {output_path}...")
        parser.export_to_json(game_data, output_path)
        
        # Mark as parsed in registry
        games_registry.mark_game_parsed(game_id, player_perspective=player_perspective)
        
        # Update player info in registry
        if game_info:
            player_ids_from_data = []
            if hasattr(game_data, 'players') and isinstance(game_data.players, dict):
                for pid, player_obj in game_data.players.items():
                    player_ids_from_data.append(str(player_obj.player_id))
            game_info['players'] = player_ids_from_data
        
        # Save registry
        games_registry.save_registry()
        
        # Update result
        result['success'] = True
        result['output_file'] = output_path
        result['players_count'] = len(game_data.players)
        result['moves_count'] = len(game_data.moves)
        result['elo_data_included'] = game_data.metadata.get('elo_data_included', False)
        
        print(f"✅ Successfully reprocessed game {game_id}")
        print(f"   Players: {result['players_count']}, Moves: {result['moves_count']}, ELO: {'✅' if result['elo_data_included'] else '❌'}")
        
        return result
        
    except Exception as e:
        result['error'] = str(e)
        print(f"❌ Error reprocessing game {composite_key}: {e}")
        logger.error(f"Error reprocessing game {composite_key}: {e}")
        return result

def find_games_needing_reprocessing(games_registry) -> List[str]:
    """
    Find all games that have table HTML but missing replay HTML
    
    Args:
        games_registry: Games registry instance
        
    Returns:
        List of composite keys for games needing reprocessing
    """
    print("🔍 Scanning for games needing reprocessing...")
    
    games_needing_reprocessing = []
    all_games = games_registry.get_all_games()
    
    for composite_key, game_data in all_games.items():
        table_id = game_data.get('table_id')
        player_perspective = game_data.get('player_perspective')
        
        if not table_id or not player_perspective:
            continue
        
        # Check if this game needs reprocessing
        status = check_game_status(table_id, player_perspective)
        
        if status['needs_reprocessing']:
            composite_key_str = f"{table_id}:{player_perspective}"
            games_needing_reprocessing.append(composite_key_str)
    
    print(f"📊 Found {len(games_needing_reprocessing)} games needing reprocessing")
    return games_needing_reprocessing

def get_game_ids_from_args(args) -> List[str]:
    """Get game IDs from command line arguments"""
    game_ids = []
    
    # If --find-missing argument provided, scan registry
    if args.find_missing:
        from bga_tm_scraper.games_registry import GamesRegistry
        games_registry = GamesRegistry()
        return find_games_needing_reprocessing(games_registry)
    
    # If --file argument provided, read from file
    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                for line in f:
                    game_id = line.strip()
                    if game_id and ':' in game_id:
                        game_ids.append(game_id)
            print(f"📁 Loaded {len(game_ids)} composite keys from {args.file}")
        except FileNotFoundError:
            print(f"❌ File not found: {args.file}")
            return []
        except Exception as e:
            print(f"❌ Error reading file {args.file}: {e}")
            return []
    
    # Add game IDs from positional arguments
    if args.game_ids:
        for game_id in args.game_ids:
            if ':' in game_id:
                game_ids.append(game_id)
            else:
                print(f"⚠️  Skipping invalid composite key: {game_id} (expected format: game_id:player_perspective)")
    
    return game_ids

def get_game_ids_interactive() -> List[str]:
    """Get game IDs through interactive input"""
    print("\n🎮 Interactive Game Reprocessor")
    print("=" * 40)
    print("Enter composite keys to reprocess (format: game_id:player_perspective)")
    print("Press Enter on empty line to start processing")
    print("Type 'quit' to exit")
    print()
    
    game_ids = []
    while True:
        try:
            game_id = input("Composite key: ").strip()
            
            if not game_id:
                break
            
            if game_id.lower() == 'quit':
                print("👋 Goodbye!")
                sys.exit(0)
            
            if ':' in game_id:
                game_ids.append(game_id)
                print(f"✅ Added composite key: {game_id}")
            else:
                print(f"❌ Invalid format: {game_id} (expected: game_id:player_perspective)")
        
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            sys.exit(0)
    
    return game_ids

def print_summary(results: List[dict]):
    """Print summary of reprocessing results"""
    if not results:
        print("\n📋 No games processed")
        return
    
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    print(f"\n📋 Reprocessing Summary")
    print("=" * 40)
    print(f"Total games processed: {len(results)}")
    print(f"✅ Successful: {len(successful)}")
    print(f"❌ Failed: {len(failed)}")
    
    if successful:
        total_players = sum(r['players_count'] for r in successful)
        total_moves = sum(r['moves_count'] for r in successful)
        elo_games = len([r for r in successful if r['elo_data_included']])
        fetched_replays = len([r for r in successful if r['fetched_replay']])
        extracted_versions = len([r for r in successful if r['version_extracted']])
        
        print(f"\n📊 Statistics:")
        print(f"   Total players: {total_players}")
        print(f"   Total moves: {total_moves}")
        print(f"   Games with ELO data: {elo_games}/{len(successful)}")
        print(f"   Replays fetched: {fetched_replays}")
        print(f"   Versions extracted: {extracted_versions}")
    
    if failed:
        print(f"\n❌ Failed Games:")
        for result in failed:
            print(f"   {result['game_id']}: {result['error']}")
    
    if successful:
        print(f"\n✅ Successfully Reprocessed:")
        for result in successful:
            print(f"   {result['game_id']}: {result['players_count']} players, {result['moves_count']} moves")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Reprocess Terraforming Mars games by fetching missing replay HTML',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s 661311860:96014413                    # Reprocess single game
  %(prog)s 661311860:96014413 674028385:85074169 # Reprocess multiple games
  %(prog)s --file incomplete_games.txt           # Reprocess games from file
  %(prog)s --find-missing                        # Auto-discover and reprocess
  %(prog)s                                       # Interactive mode
        """
    )
    
    parser.add_argument(
        'game_ids',
        nargs='*',
        help='Composite keys to reprocess (format: game_id:player_perspective)'
    )
    
    parser.add_argument(
        '--file', '-f',
        help='File containing composite keys (one per line)'
    )
    
    parser.add_argument(
        '--find-missing',
        action='store_true',
        help='Automatically find and reprocess games with missing replay HTML'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Setup logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Setup directories
    setup_directories()
    
    # Check configuration
    try:
        from config import BGA_EMAIL, BGA_PASSWORD, REQUEST_DELAY, CHROMEDRIVER_PATH
        logger.info("Configuration loaded successfully")
    except ImportError:
        logger.error("Could not import config.py. Please update config.py with credentials and ChromeDriver path.")
        print("\nTo get started:")
        print("1. Download ChromeDriver from https://chromedriver.chromium.org/")
        print("2. Update config.py with your BGA credentials and ChromeDriver path")
        print("3. Run this script again")
        return
    
    # Check if ChromeDriver path is configured
    if 'C:\\path\\to\\chromedriver.exe' in CHROMEDRIVER_PATH:
        print("\n❌ ChromeDriver path not configured!")
        print("Please:")
        print("1. Download ChromeDriver from https://chromedriver.chromium.org/")
        print("2. Update CHROMEDRIVER_PATH in config.py")
        return
    
    # Initialize games registry
    from bga_tm_scraper.games_registry import GamesRegistry
    games_registry = GamesRegistry()
    print(f"📋 Loaded games registry with {len(games_registry.get_all_games())} games")
    
    # Get game IDs
    game_ids = get_game_ids_from_args(args)
    
    # If no game IDs provided, use interactive mode
    if not game_ids:
        game_ids = get_game_ids_interactive()
    
    if not game_ids:
        print("❌ No composite keys provided")
        return
    
    # Remove duplicates while preserving order
    unique_game_ids = []
    seen = set()
    for game_id in game_ids:
        if game_id not in seen:
            unique_game_ids.append(game_id)
            seen.add(game_id)
    
    print(f"\n🚀 Starting to reprocess {len(unique_game_ids)} games...")
    print("=" * 50)
    
    # Initialize BGASession
    from bga_tm_scraper.bga_session import BGASession
    
    print("🔐 Initializing session (headless Chrome)...")
    session = BGASession(
        email=BGA_EMAIL,
        password=BGA_PASSWORD,
        chromedriver_path=CHROMEDRIVER_PATH,
        headless=True
    )
    
    if not session.login():
        print("❌ Session login failed")
        return
    
    print("✅ Session login successful!")
    
    # Process each game
    results = []
    for i, game_id in enumerate(unique_game_ids, 1):
        print(f"\n--- Processing game {i}/{len(unique_game_ids)} (ID: {game_id}) ---")
        
        result = reprocess_single_game(game_id, games_registry, session)
        results.append(result)
        
        # Check for replay limit
        if not result['success'] and 'limit' in result.get('error', '').lower():
            print("🚫 Replay limit reached! Stopping processing.")
            break
        
        # Add delay between games (except for the last one)
        if i < len(unique_game_ids):
            print(f"⏱️  Waiting {REQUEST_DELAY} seconds...")
            time.sleep(REQUEST_DELAY)
    
    # Close session
    try:
        session.close()
    except AttributeError:
        # BGASession might not have close method, try cleanup
        if hasattr(session, 'cleanup'):
            session.cleanup()
        elif hasattr(session, 'driver') and session.driver:
            session.driver.quit()
    
    # Print summary
    print_summary(results)
    
    print(f"\n🎉 Reprocessing complete!")

if __name__ == "__main__":
    main()

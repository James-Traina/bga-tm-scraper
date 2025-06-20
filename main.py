"""
Script for scraping player game history
"""
import argparse
import logging
import json
import os
import csv
import re
import time
from datetime import datetime

from bga_tm_scraper.bga_hybrid_session import BGAHybridSession

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
            summary_data['discovery_completed_at'] = summary_data.get('scraped_at', datetime.now(datetime.timezone.utc).isoformat())
        summary_data['total_games_discovered'] = len(games_data)
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)
    
    return summary_file

def process_all_missing_arena_replays(games_registry, raw_data_dir):
    """Process all Arena games that need retry processing (missing replays)"""
    print("\n🔍 Finding all Arena games that need processing...")
    
    # Get all games from registry
    all_games = games_registry.get_all_games()
    
    # Find games that need processing (Arena mode, not parsed, or not scraped)
    games_to_retry = []
    
    for composite_key, game_data in all_games.items():
        table_id = game_data.get('table_id')
        if not table_id:
            continue
            
        # Only process Arena mode games
        if not game_data.get('is_arena_mode', False):
            continue
        
        # Check if game needs processing
        scraped = game_data.get('scraped_at') is not None
        parsed = game_data.get('parsed_at') is not None
        
        if not scraped or not parsed:
            games_to_retry.append({
                'table_id': table_id,
                'scraped': scraped,
                'parsed': parsed,
                'player_perspective': game_data.get('player_perspective')
            })
    
    # Separate into categories for better reporting
    unscraped_games = [g for g in games_to_retry if not g['scraped']]
    unparsed_games = [g for g in games_to_retry if g['scraped'] and not g['parsed']]
    
    print(f"Found {len(games_to_retry)} Arena games that need processing:")
    print(f"  - {len(unscraped_games)} unscraped games")
    print(f"  - {len(unparsed_games)} scraped but unparsed games")
    
    # Extract table IDs for processing
    table_ids_to_process = [game['table_id'] for game in games_to_retry]
    
    scraping_results, parsing_results = scrape_with_browser_retry(
        table_ids_to_process, games_registry, raw_data_dir
    )
    
    # Display results
    successful_scrapes = len([r for r in scraping_results if r.get('success', False)])
    successful_parses = len([r for r in parsing_results if r.get('success', False)])
    
    print(f"\n✅ Retry processing complete!")
    print(f"   ✅ Successfully scraped: {successful_scrapes}")
    print(f"   ✅ Successfully parsed: {successful_parses}")
    
    # Show breakdown of what was processed
    if unparsed_games:
        successfully_parsed_from_unparsed = len([
            r for r in parsing_results 
            if r.get('success', False) and r.get('table_id') in [g['table_id'] for g in unparsed_games]
        ])
        print(f"📊 Previously scraped games now parsed: {successfully_parsed_from_unparsed}")

def extract_version_from_gamereview_session(table_id, session):
    """
    Extract version number from gamereview page using session
    
    Args:
        table_id: BGA table ID
        session: BGAHybridSession instance
        
    Returns:
        str: Version number (e.g., "250505-1448") or None if not found
    """
    gamereview_url = f"https://boardgamearena.com/gamereview?table={table_id}"
    logger.info(f"Extracting version from gamereview page: {gamereview_url}")
    
    try:
        print(f"🌐 Fetching gamereview page: {gamereview_url}")
        
        # Get the underlying requests session from BGAHybridSession
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

def get_current_site_version(session):
    """
    Get the current site version from BGA main page
    
    Args:
        session: BGASession instance
        
    Returns:
        str: Current site version or None if not found
    """
    try:
        print("🔍 Getting current site version from BGA...")
        
        # Try to get version from main page
        response = session.get("https://boardgamearena.com", timeout=30)
        response.raise_for_status()
        
        html_content = response.text
        
        # Look for version in the main page using the same patterns
        version = extract_version_with_multiple_patterns(html_content, "main_page")
        
        if version:
            print(f"✅ Found current site version: {version}")
            return version
        
        # Alternative: try to get version from any game page
        print("🔍 Trying to get version from a game page...")
        response = session.get("https://boardgamearena.com/gamepanel?game=terraformingmars", timeout=30)
        response.raise_for_status()
        
        html_content = response.text
        version = extract_version_with_multiple_patterns(html_content, "game_page")
        
        if version:
            print(f"✅ Found current site version from game page: {version}")
            return version
        
        print("⚠️  Could not find current site version")
        return None
        
    except Exception as e:
        print(f"❌ Error getting current site version: {e}")
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
        import time
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

def extract_version_with_multiple_patterns(html_content, table_id):
    """
    Extract version number using multiple patterns in order of reliability
    
    Args:
        html_content: HTML content of the gamereview page
        table_id: Table ID for logging purposes
        
    Returns:
        str: Version number if found, None otherwise
    """
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

def scrape_with_browser_retry(table_ids_to_scrape, games_registry, raw_data_dir):
    """
    Scrape replays using browser-based approach for retry scenarios
    
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
        
        # Initialize hybrid session with headless Chrome
        print("🔐 Initializing hybrid session (headless Chrome)...")
        session = BGAHybridSession(
            email=BGA_EMAIL,
            password=BGA_PASSWORD,
            chromedriver_path=None,  # Will be set from config
            headless=True
        )
        
        # Import chromedriver path from config
        from config import CHROMEDRIVER_PATH
        session.chromedriver_path = CHROMEDRIVER_PATH
        
        if not session.login():
            print("❌ Hybrid session login failed")
            return [], []
        
        print("✅ Hybrid session login successful!")
        
        # Initialize parser
        from bga_tm_scraper.parser import Parser
        parser = Parser()
        
        scraping_results = []
        parsing_results = []
        
        for i, table_id in enumerate(table_ids_to_scrape, 1):
            print(f"\n--- Processing game {i}/{len(table_ids_to_scrape)} (table ID: {table_id}) ---")
            
            try:
                # Get version and player perspective from registry first
                # Try to find the game with any player perspective first
                game_info = None
                version = None
                player_perspective = None
                
                # Look for any entry with this table_id
                for composite_key, data in games_registry.get_all_games().items():
                    if data.get('table_id') == table_id:
                        game_info = data
                        version = game_info.get('version')
                        player_perspective = game_info.get('player_perspective')
                        break
                
                if not game_info:
                    # Fallback: try direct lookup
                    game_info = games_registry.get_game_info(table_id)
                    if game_info:
                        version = game_info.get('version')
                        player_perspective = game_info.get('player_perspective')
                
                # If version is missing, extract it from gamereview page
                if not version:
                    print(f"⚠️  Version not found in registry for {table_id}, extracting from gamereview...")
                    version = extract_version_from_gamereview_session(table_id, session)
                    
                    if version:
                        # Update the registry with the extracted version
                        if game_info:
                            game_info['version'] = version
                        else:
                            # Create minimal entry if game doesn't exist in registry
                            games_registry.add_game_check(
                                table_id=table_id,
                                raw_datetime='',
                                parsed_datetime='',
                                players=[],
                                is_arena_mode=True,
                                version=version,
                                player_perspective=player_perspective
                            )
                        
                        # Save registry with updated version
                        games_registry.save_registry()
                        print(f"✅ Updated registry with version {version} for game {table_id}")
                    else:
                        print(f"❌ Could not extract version for {table_id}")
                        parsing_results.append({
                            'table_id': table_id,
                            'success': False,
                            'error': 'Version extraction failed'
                        })
                        continue
                else:
                    print(f"✅ Using version from registry: {version}")
                
                if not version:
                    print(f"❌ Version not found for {table_id}")
                    parsing_results.append({
                        'table_id': table_id,
                        'success': False,
                        'error': 'Version not found'
                    })
                    continue
                
                # Try to find table HTML file - check multiple possible locations
                table_html_path = None
                
                # First: player perspective directory
                if player_perspective:
                    potential_path = os.path.join(raw_data_dir, player_perspective, f"table_{table_id}.html")
                    if os.path.exists(potential_path):
                        table_html_path = potential_path
                
                # Second try: root raw data directory
                if not table_html_path:
                    potential_path = os.path.join(raw_data_dir, f"table_{table_id}.html")
                    if os.path.exists(potential_path):
                        table_html_path = potential_path
                
                # Third try: search in all player directories
                if not table_html_path:
                    for item in os.listdir(raw_data_dir):
                        item_path = os.path.join(raw_data_dir, item)
                        if os.path.isdir(item_path):
                            potential_path = os.path.join(item_path, f"table_{table_id}.html")
                            if os.path.exists(potential_path):
                                table_html_path = potential_path
                                break
                
                if not table_html_path:
                    print(f"❌ Table HTML not found for {table_id}")
                    parsing_results.append({
                        'table_id': table_id,
                        'success': False,
                        'error': 'Table HTML not found'
                    })
                    continue
                
                # Read table HTML to get player ID
                with open(table_html_path, 'r', encoding='utf-8') as f:
                    table_html = f.read()
                
                # Use the player_perspective from registry if available, otherwise extract from HTML
                if player_perspective:
                    player_id = player_perspective
                    print(f"✅ Using PlayerPerspective from registry: {player_id}")
                else:
                    # Fallback: Extract player IDs from table HTML
                    from bga_tm_scraper.scraper import TMScraper
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
                    print(f"⚠️  No PlayerPerspective in registry, using first player ID from HTML: {player_id}")
                
                print(f"📁 Found table HTML at: {table_html_path}")
                
                # Check if replay HTML already exists (for games that were scraped but not parsed)
                player_perspective_dir = os.path.join(raw_data_dir, player_id)
                replay_html_path = os.path.join(player_perspective_dir, f"replay_{table_id}.html")
                
                replay_html = None
                need_to_fetch = True
                
                if os.path.exists(replay_html_path):
                    print(f"📁 Found existing replay HTML for {table_id}")
                    try:
                        with open(replay_html_path, 'r', encoding='utf-8') as f:
                            replay_html = f.read()
                        if replay_html and len(replay_html) > 1000:  # Basic validation
                            need_to_fetch = False
                            print(f"✅ Using existing replay HTML ({len(replay_html)} chars)")
                    except Exception as e:
                        print(f"⚠️ Error reading existing replay HTML: {e}")
                        need_to_fetch = True
                
                if need_to_fetch:
                    # Construct replay URL
                    replay_url = f"https://boardgamearena.com/archive/replay/{version}/?table={table_id}&player={player_id}&comments={player_id}"
                    print(f"🌐 Fetching replay via browser: {replay_url}")
                    
                    # Get the browser driver from BGAHybridSession
                    driver = session.get_driver()
                    
                    # Navigate to replay page using browser
                    driver.get(replay_url)
                    import time
                    time.sleep(3)  # Wait for page to load
                    
                    # Get the fully rendered HTML
                    replay_html = driver.page_source
                    print(f"✅ Fetched replay HTML via browser ({len(replay_html)} chars)")
                    
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
                    
                    # Check for authentication errors
                    if 'must be logged' in replay_html.lower():
                        print("❌ Authentication error - session may have expired")
                        parsing_results.append({
                            'table_id': table_id,
                            'success': False,
                            'error': 'Authentication error'
                        })
                        continue
                    
                    # Check for "Wrong siteversion" error
                    if 'wrong siteversion' in replay_html.lower() or 'fatalerror' in replay_html.lower():
                        print(f"⚠️  Wrong siteversion error with version {version}, trying to get current version...")
                        
                        # Try to get the current version from the main site using browser
                        current_version = get_current_site_version_browser(driver)
                        if current_version and current_version != version:
                            print(f"🔄 Retrying with current site version: {current_version}")
                            
                            # Update registry with new version
                            if game_info:
                                game_info['version'] = current_version
                                games_registry.save_registry()
                            
                            # Retry with current version using browser
                            retry_url = f"https://boardgamearena.com/archive/replay/{current_version}/?table={table_id}&player={player_id}&comments={player_id}"
                            print(f"🌐 Retrying with browser: {retry_url}")
                            
                            driver.get(retry_url)
                            time.sleep(3)
                            
                            replay_html = driver.page_source
                            print(f"✅ Retry successful ({len(replay_html)} chars)")
                            
                            # Update the replay URL for logging
                            replay_url = retry_url
                            version = current_version
                        else:
                            print(f"❌ Could not get current site version or it's the same as extracted version")
                            parsing_results.append({
                                'table_id': table_id,
                                'success': False,
                                'error': 'Wrong siteversion and could not get current version'
                            })
                            continue
                    
                    # Save replay HTML to player perspective folder
                    os.makedirs(player_perspective_dir, exist_ok=True)
                    with open(replay_html_path, 'w', encoding='utf-8') as f:
                        f.write(replay_html)
                    
                    # Create scraping result
                    scraping_result = {
                        'table_id': table_id,
                        'scraped_at': datetime.now().isoformat(),
                        'success': True,
                    'browser_based': True,
                        'table_data': {'from_file': True},
                        'replay_data': {
                            'url': replay_url,
                            'html_length': len(replay_html),
                            'direct_fetch': True
                        }
                    }
                    scraping_results.append(scraping_result)
                    
                    # Mark as scraped
                    games_registry.mark_game_scraped(table_id, player_perspective=player_id)
                else:
                    # Game was already scraped, just add a result for tracking
                    scraping_result = {
                        'table_id': table_id,
                        'scraped_at': game_info.get('scraped_at', datetime.now().isoformat()) if game_info else datetime.now().isoformat(),
                        'success': True,
                        'browser_based': True,
                        'table_data': {'from_file': True},
                        'replay_data': {
                            'html_length': len(replay_html),
                            'from_existing_file': True
                        }
                    }
                    scraping_results.append(scraping_result)
                
                # Parse the game
                print(f"Parsing game {table_id}...")
                game_data = parser.parse_complete_game_with_elo(
                    replay_html=replay_html,
                    table_html=table_html,
                    table_id=table_id,
                    player_perspective=player_id
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
                    'browser_based': True
                })
                
                print(f"✅ Successfully processed game {table_id}")
                print(f"   Players: {len(game_data.players)}, Moves: {len(game_data.moves)}")
                
                # Mark as parsed
                games_registry.mark_game_parsed(table_id, player_perspective=player_id)
                
                # Update player info in registry
                if game_info:
                    player_ids_from_data = []
                    if hasattr(game_data, 'players') and isinstance(game_data.players, dict):
                        for pid, player_obj in game_data.players.items():
                            player_ids_from_data.append(str(player_obj.player_id))
                    game_info['players'] = player_ids_from_data
                
                # Save registry
                games_registry.save_registry()
                
                # Add delay between requests (only if we fetched new data)
                if need_to_fetch and i < len(table_ids_to_scrape):
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
    from bga_tm_scraper.scraper import TMScraper
    from bga_tm_scraper.games_registry import GamesRegistry
    
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
    from bga_tm_scraper.scraper import TMScraper
    
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
            missing_version_games = []
            
            for game in unscraped_games:
                table_id = game['table_id']
                table_html_path = os.path.join(raw_data_dir, f"table_{table_id}.html")
                game_info = games_registry.get_game_info(table_id)
                
                if not os.path.exists(table_html_path):
                    can_use_session_only = False
                    break
                
                # Check if version is missing - we can extract it during retry
                if not game_info or not game_info.get('version'):
                    missing_version_games.append(table_id)
            
            if can_use_session_only and unscraped_games:
                if missing_version_games:
                    print(f"✅ All unscraped games have table HTML!")
                    print(f"⚠️  {len(missing_version_games)} games missing version numbers - will extract during processing")
                else:
                    print("✅ All unscraped games have table HTML and version numbers!")
                
                print("🚀 Using session-only mode (no browser needed)...")
                
                # Extract table IDs for session-only processing
                table_ids_to_scrape = [game['table_id'] for game in unscraped_games]
                
                # Use session-only approach
                scraping_results, parsing_results = scrape_with_session_only(
                    table_ids_to_scrape, games_registry, raw_data_dir
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
                print("❌ Some games missing table HTML")
                print("🌐 Will use browser mode for missing data...")
        else:
            print("No unscraped games found in registry")
    
    # If we used session-only mode, we're done
    if use_session_only:
        return True
    
    # Initialize scraper for browser mode
    scraper = TMScraper(
        chromedriver_path=chromedriver_path,
        request_delay=request_delay,
        headless=True  # Keep browser visible for manual login
    )
    
    try:
        # Start browser and perform automated login
        if not scraper.start_browser_and_login():
            print("❌ Failed to start browser and login automatically")
            print("Falling back to manual login...")
            
            # Fallback to manual login if automated login fails
            scraper.start_browser()
            scraper.login_to_bga()
        
        # Continue with normal browser-based processing...
        print(f"\n🎯 Starting to scrape game history for player {player_id}...")
        
        # Scrape player's game history to discover all games
        games_data = scraper.scrape_player_game_history(
            player_id=player_id,
            max_clicks=100,
            filter_arena_season_21=filter_arena_season_21
        )
        
        if not games_data:
            print(f"❌ No games found for player {player_id}")
            return None
        
        print(f"✅ Discovered {len(games_data)} games for player {player_id}")
        
        # Process discovered games and add to registry
        arena_games_found = 0
        games_added_to_registry = 0
        
        for i, game_info in enumerate(games_data, 1):
            table_id = game_info['table_id']
            raw_datetime = game_info['raw_datetime']
            parsed_datetime = game_info['parsed_datetime']
            
            print(f"Processing game {i}/{len(games_data)}: {table_id}")
            
            try:
                if no_scrape:
                    # In no-scrape mode, just scrape table page to check Arena mode
                    result = scraper.scrape_table_only(table_id, player_id, save_raw=True, raw_data_dir=raw_data_dir)
                    
                    if result and result.get('success'):
                        is_arena_mode = result.get('arena_mode', False)
                        player_ids = result.get('player_ids', [])
                        version = result.get('version')
                        
                        if is_arena_mode:
                            arena_games_found += 1
                            print(f"✅ Game {table_id} is Arena mode")
                        else:
                            print(f"⏭️  Game {table_id} is not Arena mode - skipping")
                        
                        # Add to registry regardless of Arena mode (for tracking)
                        games_registry.add_game_check(
                            table_id=table_id,
                            raw_datetime=raw_datetime,
                            parsed_datetime=parsed_datetime,
                            players=player_ids,
                            is_arena_mode=is_arena_mode,
                            version=version,
                            player_perspective=player_id
                        )
                        games_added_to_registry += 1
                        
                        # Save registry after each game to ensure data persistence
                        games_registry.save_registry()
                        
                    else:
                        print(f"❌ Failed to process game {table_id}")
                        
                else:
                    # In normal mode, scrape both table and replay
                    result = scraper.scrape_table_and_replay(table_id, player_id, save_raw=True, raw_data_dir=raw_data_dir)
                    
                    if result and result.get('success'):
                        is_arena_mode = result.get('arena_mode', False)
                        version = result.get('version')
                        
                        if is_arena_mode:
                            arena_games_found += 1
                            print(f"✅ Game {table_id} is Arena mode - scraped successfully")
                            
                            # Extract player IDs from scraped data
                            player_ids = []
                            if result.get('table_data') and result['table_data'].get('html_content'):
                                player_ids = scraper.extract_player_ids_from_table(result['table_data']['html_content'])
                            
                            # Add to registry
                            games_registry.add_game_check(
                                table_id=table_id,
                                raw_datetime=raw_datetime,
                                parsed_datetime=parsed_datetime,
                                players=player_ids,
                                is_arena_mode=True,
                                version=version,
                                player_perspective=player_id
                            )
                            
                            # Mark as scraped
                            games_registry.mark_game_scraped(table_id, player_perspective=player_id)
                            games_added_to_registry += 1
                            
                        else:
                            print(f"⏭️  Game {table_id} is not Arena mode - skipped")
                    
                    elif result and result.get('skipped'):
                        print(f"⏭️  Game {table_id} was skipped: {result.get('skip_reason', 'unknown')}")
                    else:
                        print(f"❌ Failed to scrape game {table_id}")
                
                # Add delay between games
                if i < len(games_data):
                    time.sleep(request_delay)
                    
            except Exception as e:
                print(f"❌ Error processing game {table_id}: {e}")
                continue
        
        # Save updated registry
        games_registry.save_registry()
        
        # Create player summary
        summary_data = {
            'player_id': player_id,
            'scraped_at': datetime.now().isoformat(),
            'total_games_found': len(games_data),
            'total_games_discovered': len(games_data),
            'arena_games_found': arena_games_found,
            'games_added_to_registry': games_added_to_registry,
            'discovery_completed': True,
            'discovery_completed_at': datetime.now().isoformat(),
            'successful_scrapes': arena_games_found if not no_scrape else 0,
            'mode': 'no_scrape' if no_scrape else 'normal',
            'games_data': games_data
        }
        
        # Save player summary
        save_player_summary(player_id, summary_data)
        
        print(f"\n✅ Player {player_id} processing complete:")
        print(f"   📊 Total games discovered: {len(games_data)}")
        print(f"   🎯 Arena games found: {arena_games_found}")
        print(f"   📝 Games added to registry: {games_added_to_registry}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error during scraping: {e}")
        print(f"❌ Error during scraping: {e}")
        return None
    
    finally:
        # Always close browser
        print("\nClosing browser...")
        scraper.close_browser()

if __name__ == "__main__":
    main()

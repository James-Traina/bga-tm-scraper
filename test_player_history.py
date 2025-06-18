"""
Test script for scraping player game history
"""
import logging
import json
import os
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('player_history_scraper.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Test the player game history scraping functionality"""
    
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
    
    # Get player ID from user
    player_id = input("Enter the BGA player ID to scrape game history for: ").strip()
    if not player_id:
        print("❌ No player ID provided!")
        return
    
    filter_arena_season_21 = True
    
    if filter_arena_season_21:
        print("🎯 Arena season 21 filtering enabled - only games from 2025-04-08 to 2025-07-08 will be included")
    else:
        print("📅 No date filtering - all games will be included")
    
    # Initialize games registry
    print("\n📋 Loading master games registry...")
    games_registry = GamesRegistry()
    games_registry.print_stats()
    
    # Initialize scraper
    scraper = TMScraper(
        chromedriver_path=CHROMEDRIVER_PATH,
        request_delay=REQUEST_DELAY,
        headless=False  # Keep browser visible for manual login
    )
    
    # Create data directories
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    os.makedirs('data/processed', exist_ok=True)
    
    try:
        # Start browser
        scraper.start_browser()
        
        # Manual login
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
            
            # Filter out already scraped games
            print(f"\n🔍 Checking for already scraped games...")
            new_games = games_registry.filter_new_games(games_data)
            already_scraped = len(games_data) - len(new_games)
            
            if already_scraped > 0:
                print(f"⏭️  Found {already_scraped} games already in registry - skipping duplicates")
                print(f"📋 {len(new_games)} new games to process")
            else:
                print(f"📋 All {len(games_data)} games are new - proceeding with full scraping")
            
            if not new_games:
                print("✅ No new games to scrape - all games already processed!")
                games_registry.print_stats()
                return
           
            print("\n🚀 Starting to scrape and parse games...")
            table_ids_to_scrape = [game['table_id'] for game in new_games]
            
            # Initialize parser
            from src.parser import Parser
            parser = Parser()
            
            scraping_results = []
            parsing_results = []
            
            for i, table_id in enumerate(table_ids_to_scrape, 1):
                print(f"\n--- Processing game {i}/{len(table_ids_to_scrape)} (table ID: {table_id}) ---")
                
                # Scrape the game
                print(f"Scraping game {table_id}...")
                scraping_result = scraper.scrape_table_and_replay(
                    table_id=table_id,
                    save_raw=True,
                    raw_data_dir=RAW_DATA_DIR
                )
                
                if scraping_result:
                    scraping_results.append(scraping_result)
                    
                    # Check if this was a successful scrape or a skip
                    if scraping_result.get('success', False):
                        print(f"✅ Successfully scraped game {table_id}")
                        
                        # Parse immediately after scraping
                        print(f"Parsing game {table_id}...")
                    elif scraping_result.get('skipped', False):
                        skip_reason = scraping_result.get('skip_reason', 'unknown')
                        if skip_reason == 'not_arena_mode':
                            print(f"⏭️  Skipped game {table_id} - Not Arena mode")
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
                            
                            # Export to JSON
                            output_path = f"data/parsed/game_{table_id}.json"
                            parser.export_to_json(game_data, output_path)
                            
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
                            
                            # Find the original game data for this table_id
                            original_game = next((g for g in new_games if g['table_id'] == table_id), None)
                            if original_game:
                                # Extract player information from parsed data
                                players_info = []
                                # game_data.players is a dictionary with player_id as keys and Player objects as values
                                if hasattr(game_data, 'players') and isinstance(game_data.players, dict):
                                    for player_id, player_obj in game_data.players.items():
                                        players_info.append({
                                            'player_id': player_obj.player_id,
                                            'name': player_obj.player_name,
                                            'score': player_obj.final_vp
                                        })
                                else:
                                    # Fallback for different data structure
                                    for player in game_data.players:
                                        players_info.append({
                                            'player_id': getattr(player, 'player_id', None),
                                            'name': getattr(player, 'player_name', getattr(player, 'name', None)),
                                            'score': getattr(player, 'final_vp', getattr(player, 'score', None))
                                        })
                                
                                # Add to registry
                                games_registry.add_game(
                                    table_id=table_id,
                                    raw_datetime=original_game['raw_datetime'],
                                    parsed_datetime=original_game['parsed_datetime'],
                                    players=players_info
                                )
                                print(f"📋 Added game {table_id} to master registry")
                                
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
            
            # Save comprehensive summary
            scraping_summary_file = f"data/processed/player_{player_id}_complete_summary_{timestamp}.json"
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
            
            with open(scraping_summary_file, 'w', encoding='utf-8') as f:
                json.dump(scraping_summary, f, indent=2, ensure_ascii=False)
            
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
            
        else:
            print("❌ No table IDs found. This could be due to:")
            print("  - Incorrect player ID")
            print("  - Player has no game history")
            print("  - Page structure has changed")
            print("  - Authentication issues")
    
    except Exception as e:
        logger.error(f"Error during scraping: {e}")
        print(f"❌ Error during scraping: {e}")
    
    finally:
        # Always close browser
        print("\nClosing browser...")
        scraper.close_browser()

if __name__ == "__main__":
    main()

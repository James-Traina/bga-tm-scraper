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
    
    # Get player ID from user
    player_id = input("Enter the BGA player ID to scrape game history for: ").strip()
    if not player_id:
        print("❌ No player ID provided!")
        return
    
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
        
        # Scrape player game history (Arena mode filtering happens during individual game scraping)
        print(f"\n🎯 Starting to scrape game history for player {player_id}...")
        print("Note: Only Arena mode games will be processed during scraping.")
        table_ids = scraper.scrape_player_game_history(
            player_id=player_id,
            max_clicks=50,  # Reasonable limit
            click_delay=1   # 1 second between clicks
        )
        
        if table_ids:
            print(f"\n✅ Successfully found {len(table_ids)} games!")
            print("Table IDs found:")
            for i, table_id in enumerate(table_ids[:10], 1):  # Show first 10
                print(f"  {i}. {table_id}")
            
            if len(table_ids) > 10:
                print(f"  ... and {len(table_ids) - 10} more")
            
            # Save results to file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            results_file = f"data/processed/player_{player_id}_table_ids_{timestamp}.json"
            
            results_data = {
                'player_id': player_id,
                'scraped_at': datetime.now().isoformat(),
                'total_games_found': len(table_ids),
                'table_ids': table_ids
            }
            
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results_data, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Results saved to: {results_file}")
            
            # Ask if user wants to scrape some of these games
            scrape_games = input(f"\nWould you like to scrape the first 10 games? (y/n): ").strip().lower()
            
            if scrape_games == 'y':
                print("\n🚀 Starting to scrape and parse first 10 games...")
                sample_table_ids = table_ids[:10]
                
                # Initialize parser
                from src.parser import Parser
                parser = Parser()
                
                scraping_results = []
                parsing_results = []
                
                for i, table_id in enumerate(sample_table_ids, 1):
                    print(f"\n--- Processing game {i}/{len(sample_table_ids)} (table ID: {table_id}) ---")
                    
                    # Scrape the game
                    print(f"Scraping game {table_id}...")
                    scraping_result = scraper.scrape_table_and_replay(
                        table_id=table_id,
                        save_raw=True,
                        raw_data_dir=RAW_DATA_DIR
                    )
                    
                    if scraping_result:
                        scraping_results.append(scraping_result)
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
                    if i < len(sample_table_ids):
                        print(f"Waiting {REQUEST_DELAY} seconds before next game...")
                        import time
                        time.sleep(REQUEST_DELAY)
                
                print(f"\n✅ Processing complete!")
                print(f"   Games scraped: {len(scraping_results)}/{len(sample_table_ids)}")
                print(f"   Games parsed: {len([r for r in parsing_results if r['success']])}/{len(sample_table_ids)}")
                
                # Create clean scraping summary (without large HTML content)
                clean_scraping_results = []
                for result in scraping_results:
                    clean_result = {
                        'table_id': result['table_id'],
                        'scraped_at': result['scraped_at'],
                        'success': result['success']
                    }
                    
                    # Add table data summary without HTML content
                    if 'table_data' in result and result['table_data']:
                        clean_result['table_data'] = {
                            'url': result['table_data'].get('url'),
                            'players_found': result['table_data'].get('players_found', []),
                            'elo_data_found': result['table_data'].get('elo_data_found', False),
                            'html_length': result['table_data'].get('html_length', 0)
                        }
                    
                    # Add replay data summary without HTML content
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
                    'total_table_ids_found': len(table_ids),
                    'games_scraped': len(sample_table_ids),
                    'successful_scrapes': len(scraping_results),
                    'successful_parses': len([r for r in parsing_results if r['success']]),
                    'scraping_results': clean_scraping_results,
                    'parsing_results': parsing_results
                }
                
                with open(scraping_summary_file, 'w', encoding='utf-8') as f:
                    json.dump(scraping_summary, f, indent=2, ensure_ascii=False)
                
                print(f"💾 Complete summary saved to: {scraping_summary_file}")
                
                # Print detailed summary
                print(f"\n=== Complete Processing Summary ===")
                print(f"Total table IDs found: {len(table_ids)}")
                print(f"Games scraped: {len(scraping_results)}")
                print(f"Games parsed: {len([r for r in parsing_results if r['success']])}")
                print(f"Games with ELO data: {len([r for r in parsing_results if r.get('elo_data_included', False)])}")
                
                for result in parsing_results:
                    if result['success']:
                        print(f"\nGame {result['table_id']}:")
                        print(f"  Players: {result['players_count']}")
                        print(f"  Moves: {result['moves_count']}")
                        print(f"  ELO data: {'✅' if result['elo_data_included'] else '❌'}")
                        if result['elo_data_included']:
                            print(f"  ELO players: {result['elo_players_found']}")
                        print(f"  Output: {result['output_file']}")
                    else:
                        print(f"\nGame {result['table_id']}: ❌ Failed - {result.get('error', 'Unknown error')}")
            
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

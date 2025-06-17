"""
Main entry point for BGA Terraforming Mars scraper
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
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main function to run the enhanced scraper with ELO data"""
    
    # Try to import config
    try:
        from config import TEST_TABLE_IDS, REQUEST_DELAY, RAW_DATA_DIR, CHROMEDRIVER_PATH
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
    
    # Import scraper and parser modules
    from src.scraper import TMScraper
    from src.parser import Parser
    
    # Initialize scraper and parser
    scraper = TMScraper(
        chromedriver_path=CHROMEDRIVER_PATH,
        request_delay=REQUEST_DELAY,
        headless=False  # Keep browser visible for manual login
    )
    
    parser = Parser()
    
    # Create data directories
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    os.makedirs('data/processed', exist_ok=True)
    os.makedirs('data/parsed', exist_ok=True)
    
    try:
        # Start browser
        scraper.start_browser()
        
        # Manual login
        scraper.login_to_bga()
        
        # Scrape table IDs with both table and replay data
        logger.info(f"Starting to scrape {len(TEST_TABLE_IDS)} games (table + replay + ELO)...")
        scraping_results = scraper.scrape_multiple_tables_and_replays(
            table_ids=TEST_TABLE_IDS,
            save_raw=True,
            raw_data_dir=RAW_DATA_DIR
        )
        
        # Parse each game with ELO data
        parsing_results = []
        for scraping_result in scraping_results:
            table_id = scraping_result['table_id']
            logger.info(f"Parsing game {table_id} with ELO data...")
            
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
                    
                    logger.info(f"Successfully parsed and saved game {table_id}")
                    
                else:
                    logger.error(f"Missing HTML files for game {table_id}")
                    parsing_results.append({
                        'table_id': table_id,
                        'success': False,
                        'error': 'Missing HTML files'
                    })
                    
            except Exception as e:
                logger.error(f"Error parsing game {table_id}: {e}")
                parsing_results.append({
                    'table_id': table_id,
                    'success': False,
                    'error': str(e)
                })
        
        # Save results summary
        if scraping_results:
            summary_file = f"data/processed/enhanced_scraping_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            summary_data = {
                'scraping_results': scraping_results,
                'parsing_results': parsing_results,
                'summary': {
                    'total_games_attempted': len(TEST_TABLE_IDS),
                    'games_scraped': len(scraping_results),
                    'games_parsed': len([r for r in parsing_results if r['success']]),
                    'games_with_elo': len([r for r in parsing_results if r.get('elo_data_included', False)])
                }
            }
            
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Enhanced scraping completed! Summary saved to {summary_file}")
            
            # Print summary
            print(f"\n=== Enhanced Scraping Summary ===")
            print(f"Total games attempted: {len(TEST_TABLE_IDS)}")
            print(f"Successfully scraped: {len(scraping_results)}")
            print(f"Successfully parsed: {len([r for r in parsing_results if r['success']])}")
            print(f"Games with ELO data: {len([r for r in parsing_results if r.get('elo_data_included', False)])}")
            print(f"Raw HTML files saved to: {RAW_DATA_DIR}")
            print(f"Parsed JSON files saved to: data/parsed/")
            print(f"Summary saved to: {summary_file}")
            
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
            logger.error("No games were successfully scraped")
            print("\nNo games were successfully scraped. Check the logs for errors.")
            print("Make sure you're logged into BGA in the browser window.")
    
    finally:
        # Always close browser
        print("\nClosing browser...")
        scraper.close_browser()

if __name__ == "__main__":
    main()

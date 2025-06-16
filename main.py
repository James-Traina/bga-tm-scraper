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
    """Main function to run the scraper"""
    
    # Try to import config
    try:
        from config import TEST_URLS, REQUEST_DELAY, RAW_DATA_DIR, CHROMEDRIVER_PATH
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
    
    # Import scraper modules
    from src.scraper import TMScraper
    
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
        
        # Scrape test URLs
        logger.info(f"Starting to scrape {len(TEST_URLS)} test URLs...")
        results = scraper.scrape_multiple_replays(
            urls=TEST_URLS,
            save_raw=True,
            raw_data_dir=RAW_DATA_DIR
        )
        
        # Save results summary
        if results:
            summary_file = f"data/processed/scraping_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Scraping completed! Summary saved to {summary_file}")
            
            # Print summary
            print(f"\n=== Scraping Summary ===")
            print(f"Total URLs processed: {len(TEST_URLS)}")
            print(f"Successfully scraped: {len(results)}")
            print(f"Raw HTML files saved to: {RAW_DATA_DIR}")
            print(f"Summary saved to: {summary_file}")
            
            for result in results:
                print(f"\nReplay {result['replay_id']}:")
                print(f"  Title: {result.get('title', 'N/A')}")
                print(f"  Players: {', '.join(result.get('players', []))}")
                print(f"  Game logs found: {result.get('game_logs_found', False)}")
                if result.get('num_moves'):
                    print(f"  Number of moves: {result['num_moves']}")
        else:
            logger.error("No replays were successfully scraped")
            print("\nNo replays were successfully scraped. Check the logs for errors.")
            print("Make sure you're logged into BGA in the browser window.")
    
    finally:
        # Always close browser
        print("\nClosing browser...")
        scraper.close_browser()

if __name__ == "__main__":
    main()

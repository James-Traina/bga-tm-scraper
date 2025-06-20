"""
Backfill version numbers for existing games in games.csv

This script processes all games in the games registry and extracts version numbers
for games that don't already have them.
"""
import logging
import time
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backfill_versions.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    print("🔧 Version Number Backfill Tool")
    print("This script will extract version numbers for existing games in your registry.")
    print()
    
    # Try to import config
    try:
        from config import REQUEST_DELAY, CHROMEDRIVER_PATH
        logger.info("Configuration loaded successfully")
    except ImportError:
        logger.error("Could not import config.py. Please update config.py with ChromeDriver path.")
        print("❌ Could not import config.py. Please ensure config.py is properly configured.")
        return
    
    # Check if ChromeDriver path is configured
    if 'C:\\path\\to\\chromedriver.exe' in CHROMEDRIVER_PATH:
        print("❌ ChromeDriver path not configured!")
        print("Please update CHROMEDRIVER_PATH in config.py")
        return
    
    # Import required modules
    from bga_tm_scraper.scraper import TMScraper
    from bga_tm_scraper.games_registry import GamesRegistry
    
    # Initialize games registry
    print("📋 Loading master games registry...")
    games_registry = GamesRegistry()
    games_registry.print_stats()
    
    # Get all games from registry
    all_games = games_registry.get_all_games()
    
    # Filter games that don't have version numbers
    games_without_version = []
    games_with_version = 0
    
    for table_id, game_data in all_games.items():
        if not game_data.get('version'):
            games_without_version.append(table_id)
        else:
            games_with_version += 1
    
    print(f"\n📊 Version Status:")
    print(f"   Games with version: {games_with_version}")
    print(f"   Games without version: {len(games_without_version)}")
    
    if not games_without_version:
        print("✅ All games already have version numbers!")
        return
    
    print(f"\n🎯 Will process {len(games_without_version)} games to extract version numbers")
    
    # Ask for confirmation
    response = input("\nDo you want to proceed? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("❌ Operation cancelled.")
        return
    
    # Initialize scraper
    print("\n🚀 Initializing scraper...")
    scraper = TMScraper(
        chromedriver_path=CHROMEDRIVER_PATH,
        request_delay=REQUEST_DELAY,
        headless=True  # Keep browser visible for login
    )
    
    try:
        # Start browser and login
        if not scraper.start_browser_and_login():
            print("❌ Failed to start browser and login automatically")
            print("Falling back to manual login...")
            
            # Fallback to manual login if automated login fails
            scraper.start_browser()
            scraper.login_to_bga()
        
        print(f"\n🔧 Starting version extraction for {len(games_without_version)} games...")
        
        successful_extractions = 0
        failed_extractions = 0
        
        for i, table_id in enumerate(games_without_version, 1):
            print(f"\n--- Processing game {i}/{len(games_without_version)} (table ID: {table_id}) ---")
            
            try:
                # Extract version number
                print(f"Extracting version for game {table_id}...")
                version = scraper.extract_version_from_gamereview(table_id)
                
                if version:
                    # Update the registry with the version
                    games_registry.update_game_version(table_id, version)
                    print(f"✅ Successfully extracted version: {version}")
                    successful_extractions += 1
                else:
                    print(f"⚠️  Could not extract version for game {table_id}")
                    failed_extractions += 1
                
                # Save registry after each update
                games_registry.save_registry()
                
                # Add delay between requests (except for the last one)
                if i < len(games_without_version):
                    print(f"Waiting {REQUEST_DELAY} seconds before next game...")
                    time.sleep(REQUEST_DELAY)
                
            except Exception as e:
                logger.error(f"Error processing game {table_id}: {e}")
                print(f"❌ Error processing game {table_id}: {e}")
                failed_extractions += 1
                continue
        
        print(f"\n✅ Version extraction complete!")
        print(f"   ✅ Successful extractions: {successful_extractions}")
        print(f"   ❌ Failed extractions: {failed_extractions}")
        
        # Save final registry
        print(f"\n💾 Saving updated registry...")
        games_registry.save_registry()
        games_registry.print_stats()
        
        # Show updated statistics
        all_games_updated = games_registry.get_all_games()
        games_with_version_final = sum(1 for game_data in all_games_updated.values() if game_data.get('version'))
        games_without_version_final = len(all_games_updated) - games_with_version_final
        
        print(f"\n📊 Final Version Status:")
        print(f"   Games with version: {games_with_version_final}")
        print(f"   Games without version: {games_without_version_final}")
        
        if games_without_version_final == 0:
            print("🎉 All games now have version numbers!")
        
    except Exception as e:
        logger.error(f"Error during version extraction: {e}")
        print(f"❌ Error during version extraction: {e}")
    
    finally:
        # Always close browser
        print("\nClosing browser...")
        scraper.close_browser()

if __name__ == "__main__":
    main()

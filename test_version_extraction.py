"""
Test script for dynamic version extraction from gamereview pages
"""
import logging
from src.scraper import TMScraper
from config import CHROMEDRIVER_PATH, TEST_TABLE_IDS

# Setup logging
logging.basicConfig(level=logging.INFO)

def test_version_extraction():
    """Test the version extraction functionality"""
    
    # Initialize scraper
    scraper = TMScraper(
        chromedriver_path=CHROMEDRIVER_PATH,
        request_delay=1,
        headless=False
    )
    
    print(f"🚀 Speed optimizations enabled!")
    print(f"   Speed profile: {scraper.speed_profile}")
    print(f"   Page load delay: {scraper.speed_settings.get('page_load_delay')}s")
    print(f"   Gamereview delay: {scraper.speed_settings.get('gamereview_delay')}s")
    print(f"   Click delay: {scraper.speed_settings.get('click_delay')}s")
    
    try:
        # Start browser
        print("Starting browser...")
        scraper.start_browser()
        
        # Manual login
        print("Please log in to BGA...")
        scraper.login_to_bga()
        
        # Test version extraction with the first test table ID
        test_table_id = TEST_TABLE_IDS[0] if TEST_TABLE_IDS else "688771617"
        
        print(f"\nTesting version extraction for table ID: {test_table_id}")
        version = scraper.extract_version_from_gamereview(test_table_id)
        
        if version:
            print(f"✅ Successfully extracted version: {version}")
            
            # Test constructing the replay URL with the extracted version
            player_id = "96014413"  # Default player ID
            replay_url = f"https://boardgamearena.com/archive/replay/{version}/?table={test_table_id}&player={player_id}&comments={player_id}"
            print(f"📝 Constructed replay URL: {replay_url}")
            
            # Test if the replay URL works
            print("\nTesting if the constructed replay URL works...")
            replay_data = scraper.scrape_replay(replay_url, save_raw=False)
            
            if replay_data:
                print("✅ Replay URL works! Dynamic version extraction is successful.")
                print(f"   - Replay ID: {replay_data.get('replay_id')}")
                print(f"   - Game logs found: {replay_data.get('game_logs_found')}")
                print(f"   - Players: {replay_data.get('players', [])}")
            else:
                print("❌ Replay URL failed - there might be an issue with the constructed URL")
        else:
            print("❌ Failed to extract version number")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        
    finally:
        # Close browser
        print("\nClosing browser...")
        scraper.close_browser()

if __name__ == "__main__":
    test_version_extraction()

#!/usr/bin/env python3
"""
Test script for automated BGA login functionality
Demonstrates the new hybrid session manager that eliminates manual login
"""

import logging
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_hybrid_session():
    """Test the hybrid session manager directly"""
    print("🧪 Testing BGAHybridSession directly...")
    
    try:
        from config import BGA_EMAIL, BGA_PASSWORD, CHROMEDRIVER_PATH
    except ImportError:
        print("❌ Could not import config. Please ensure config.py exists with credentials.")
        return False
    
    if BGA_EMAIL == "your_email@example.com":
        print("❌ Please update BGA_EMAIL and BGA_PASSWORD in config.py")
        return False
    
    try:
        from bga_hybrid_session import BGAHybridSession
        
        # Test hybrid session
        with BGAHybridSession(
            email=BGA_EMAIL,
            password=BGA_PASSWORD,
            chromedriver_path=CHROMEDRIVER_PATH,
            headless=False
        ) as session:
            
            print("🔐 Attempting automated login...")
            if session.login():
                print("✅ Hybrid session login successful!")
                
                # Test authentication status
                status = session.check_authentication_status()
                print(f"📊 Authentication status: {status}")
                
                # Test getting authenticated driver
                driver = session.get_driver()
                print(f"🌐 Browser driver obtained: {type(driver).__name__}")
                
                # Navigate to a test page
                print("🔍 Testing navigation to BGA account page...")
                driver.get("https://boardgamearena.com/account")
                
                # Check if we're logged in
                page_source = driver.page_source.lower()
                if 'must be logged' in page_source:
                    print("❌ Not properly authenticated")
                    return False
                else:
                    print("✅ Successfully authenticated and navigated!")
                    return True
            else:
                print("❌ Hybrid session login failed")
                return False
                
    except Exception as e:
        print(f"❌ Error testing hybrid session: {e}")
        return False

def test_scraper_integration():
    """Test the TMScraper with automated login"""
    print("\n🧪 Testing TMScraper with automated login...")
    
    try:
        from config import CHROMEDRIVER_PATH, REQUEST_DELAY
        from scraper import TMScraper
        
        # Initialize scraper
        scraper = TMScraper(
            chromedriver_path=CHROMEDRIVER_PATH,
            request_delay=REQUEST_DELAY,
            headless=False
        )
        
        print("🔐 Testing automated login via TMScraper...")
        if scraper.start_browser_and_login():
            print("✅ TMScraper automated login successful!")
            
            # Test a simple navigation
            print("🔍 Testing navigation to BGA main page...")
            scraper.driver.get("https://boardgamearena.com")
            
            # Check authentication
            page_source = scraper.driver.page_source.lower()
            if 'logout' in page_source or 'my account' in page_source:
                print("✅ TMScraper authentication verified!")
                return True
            else:
                print("❌ TMScraper authentication verification failed")
                return False
        else:
            print("❌ TMScraper automated login failed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing TMScraper: {e}")
        return False
    finally:
        try:
            scraper.close_browser()
        except:
            pass

def main():
    """Run all tests"""
    print("🚀 Testing Automated BGA Login Implementation")
    print("=" * 50)
    
    # Test 1: Direct hybrid session test
    hybrid_success = test_hybrid_session()
    
    # Test 2: Scraper integration test
    scraper_success = test_scraper_integration()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Test Results Summary:")
    print(f"  Hybrid Session: {'✅ PASS' if hybrid_success else '❌ FAIL'}")
    print(f"  Scraper Integration: {'✅ PASS' if scraper_success else '❌ FAIL'}")
    
    if hybrid_success and scraper_success:
        print("\n🎉 All tests passed! Automated login is working correctly.")
        print("\n📝 Next steps:")
        print("  1. Run test_player_history.py to test full scraping workflow")
        print("  2. The script will now login automatically without manual intervention")
        print("  3. If automated login fails, it will fallback to manual login")
    else:
        print("\n⚠️  Some tests failed. Please check:")
        print("  1. BGA credentials in config.py are correct")
        print("  2. ChromeDriver path is valid")
        print("  3. Internet connection is stable")
        print("  4. BGA website is accessible")

if __name__ == "__main__":
    main()

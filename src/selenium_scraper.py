"""
Selenium-based scraper for Terraforming Mars replay data from BoardGameArena
Uses regular Selenium WebDriver without debug mode
"""
import time
import os
import logging
from typing import List, Optional, Dict
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import datetime

logger = logging.getLogger(__name__)

class SeleniumTMScraper:
    """Scraper using regular Selenium WebDriver for Terraforming Mars replays"""
    
    def __init__(self, chromedriver_path: str, request_delay: int = 2, headless: bool = False):
        """
        Initialize the Selenium scraper
        
        Args:
            chromedriver_path: Path to ChromeDriver executable
            request_delay: Delay between requests in seconds
            headless: Whether to run Chrome in headless mode
        """
        self.chromedriver_path = chromedriver_path
        self.request_delay = request_delay
        self.headless = headless
        self.driver = None
    
    def start_browser(self):
        """Start the Chrome browser"""
        print("Starting Chrome browser...")
        
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless')
        
        # Add useful Chrome options
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # Set user agent to avoid detection
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        service = Service(self.chromedriver_path)
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        print("✅ Chrome browser started successfully!")
        return self.driver
    
    def login_to_bga(self):
        """Navigate to BGA and wait for user to log in manually"""
        if not self.driver:
            raise RuntimeError("Browser not started. Call start_browser() first.")
        
        print("Navigating to BoardGameArena...")
        self.driver.get("https://boardgamearena.com")
        
        print("\n" + "="*60)
        print("🔐 MANUAL LOGIN REQUIRED")
        print("Please log into BoardGameArena in the browser window that opened.")
        print("After logging in, come back here and press Enter to continue...")
        print("="*60)
        
        input("Press Enter when you're logged in and ready to continue...")
        
        # Verify login by checking for logout link or user menu
        try:
            # Look for common elements that indicate login
            WebDriverWait(self.driver, 10).until(
                lambda driver: 'logout' in driver.page_source.lower() or 
                              'my account' in driver.page_source.lower() or
                              'player_name' in driver.page_source.lower()
            )
            print("✅ Login verified!")
            return True
        except:
            print("⚠️  Could not verify login, but continuing anyway...")
            return True
    
    def scrape_replay(self, url: str, save_raw: bool = True, raw_data_dir: str = 'data/raw') -> Optional[Dict]:
        """
        Scrape a single replay page
        
        Args:
            url: BGA replay URL
            save_raw: Whether to save raw HTML
            raw_data_dir: Directory to save raw HTML files
            
        Returns:
            dict: Scraped data or None if failed
        """
        if not self.driver:
            raise RuntimeError("Browser not started. Call start_browser() first.")
        
        # Extract replay ID from URL
        replay_id = self._extract_replay_id(url)
        if not replay_id:
            logger.error(f"Could not extract replay ID from {url}")
            return None
        
        logger.info(f"Scraping replay {replay_id}")
        
        try:
            # Navigate to the replay URL
            print(f"Navigating to: {url}")
            self.driver.get(url)
            time.sleep(5)  # Wait for page to load
            
            # Check if we got an error page
            page_source = self.driver.page_source
            if 'must be logged' in page_source.lower():
                print("❌ Authentication error - please make sure you're logged into BGA")
                return None
            
            if 'fatal error' in page_source.lower():
                print("❌ Fatal error on page - replay might not be accessible")
                return None
            
            # Save raw HTML if requested
            if save_raw:
                os.makedirs(raw_data_dir, exist_ok=True)
                raw_file_path = os.path.join(raw_data_dir, f"replay_{replay_id}.html")
                
                with open(raw_file_path, 'w', encoding='utf-8') as f:
                    f.write(page_source)
                logger.info(f"Saved raw HTML to {raw_file_path}")
            
            # Parse the HTML to extract basic information
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Extract basic replay information
            replay_data = {
                'replay_id': replay_id,
                'url': url,
                'scraped_at': datetime.now().isoformat(),
                'html_length': len(page_source),
                'title': None,
                'players': [],
                'game_logs_found': False
            }
            
            # Try to extract title
            title_elem = soup.find('title')
            if title_elem:
                replay_data['title'] = title_elem.get_text().strip()
            
            # Look for game logs section
            game_logs = soup.find_all('div', class_='replaylogs_move')
            if game_logs:
                replay_data['game_logs_found'] = True
                replay_data['num_moves'] = len(game_logs)
                logger.info(f"Found {len(game_logs)} game log entries")
                print(f"✅ Found {len(game_logs)} game log entries")
            else:
                logger.warning("No game logs found in replay")
                print("⚠️  No game logs found - checking page content...")
                
                # Debug: check what we actually got
                if len(page_source) < 1000:
                    print(f"Page seems too short ({len(page_source)} chars)")
                    print("First 500 chars:", page_source[:500])
            
            # Try to extract player information
            player_elements = soup.find_all('span', class_='playername')
            for player_elem in player_elements:
                player_name = player_elem.get_text().strip()
                if player_name:
                    replay_data['players'].append(player_name)
            
            logger.info(f"Successfully scraped replay {replay_id}")
            return replay_data
            
        except Exception as e:
            logger.error(f"Error scraping replay {replay_id}: {e}")
            print(f"❌ Error scraping replay: {e}")
            return None
    
    def scrape_multiple_replays(self, urls: List[str], save_raw: bool = True, 
                              raw_data_dir: str = 'data/raw') -> List[Dict]:
        """
        Scrape multiple replay pages
        
        Args:
            urls: List of BGA replay URLs
            save_raw: Whether to save raw HTML
            raw_data_dir: Directory to save raw HTML files
            
        Returns:
            list: List of scraped data dictionaries
        """
        results = []
        
        logger.info(f"Starting batch scraping of {len(urls)} replays")
        
        for i, url in enumerate(urls, 1):
            logger.info(f"Processing replay {i}/{len(urls)}")
            print(f"\nProcessing replay {i}/{len(urls)}")
            
            result = self.scrape_replay(url, save_raw, raw_data_dir)
            if result:
                results.append(result)
            
            # Delay between requests (except for the last one)
            if i < len(urls):
                print(f"Waiting {self.request_delay} seconds...")
                time.sleep(self.request_delay)
        
        logger.info(f"Batch scraping completed. Successfully scraped {len(results)}/{len(urls)} replays")
        return results
    
    def close_browser(self):
        """Close the browser"""
        if self.driver:
            try:
                self.driver.quit()
                print("Browser closed")
            except:
                pass
    
    def _extract_replay_id(self, url: str) -> Optional[str]:
        """Extract replay ID from BGA replay URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            path_parts = parsed.path.split('/')
            
            # URL format: /archive/replay/REPLAY_ID/
            if 'replay' in path_parts:
                replay_idx = path_parts.index('replay')
                if replay_idx + 1 < len(path_parts):
                    return path_parts[replay_idx + 1]
            
            return None
        except Exception as e:
            logger.error(f"Error extracting replay ID from {url}: {e}")
            return None

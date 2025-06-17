"""
Web scraper for Terraforming Mars replay data from BoardGameArena
"""
import time
import os
import logging
import re
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

class TMScraper:
    """Web scraper for Terraforming Mars replays from BoardGameArena"""
    
    def __init__(self, chromedriver_path: str, request_delay: int = 1, headless: bool = False):
        """
        Initialize the scraper
        
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
    
    def scrape_table_and_replay(self, table_id: str, save_raw: bool = True, raw_data_dir: str = 'data/raw') -> Optional[Dict]:
        """
        Scrape both table page and replay page for a game
        
        Args:
            table_id: BGA table ID
            save_raw: Whether to save raw HTML
            raw_data_dir: Directory to save raw HTML files
            
        Returns:
            dict: Combined scraped data or None if failed
        """
        if not self.driver:
            raise RuntimeError("Browser not started. Call start_browser() first.")
        
        logger.info(f"Scraping table and replay for game {table_id}")
        
        try:
            # Step 1: Scrape table page for ELO data
            logger.info("Scraping table page...")
            table_data = self.scrape_table_page(table_id, save_raw, raw_data_dir)
            if not table_data:
                logger.error(f"Failed to scrape table page for {table_id}")
                return None

            # Step 2: Extract player IDs from table page
            logger.info("Extracting player IDs...")
            player_ids = self.extract_player_ids_from_table(table_data['html_content'])
            if not player_ids:
                logger.warning(f"No player IDs found in table page for {table_id}")
                # Use a default player ID or continue without it
                player_ids = ["86296239"]  # Fallback from original URL
            
            # Step 3: Construct and scrape replay page
            logger.info("Extracting replay...")
            replay_data = self.scrape_replay_from_table(table_id, player_ids[0], save_raw, raw_data_dir)
            if not replay_data:
                logger.error(f"Failed to scrape replay page for {table_id}")
                # Continue with just table data
                replay_data = {}
            
            # Step 4: Combine results
            combined_data = {
                'table_id': table_id,
                'table_data': table_data,
                'replay_data': replay_data,
                'scraped_at': datetime.now().isoformat(),
                'success': True
            }
            
            logger.info(f"Successfully scraped table and replay for game {table_id}")
            return combined_data
            
        except Exception as e:
            logger.error(f"Error scraping table and replay for {table_id}: {e}")
            return None
    
    def scrape_table_page(self, table_id: str, save_raw: bool = True, raw_data_dir: str = 'data/raw') -> Optional[Dict]:
        """
        Scrape a table page for ELO information
        
        Args:
            table_id: BGA table ID
            save_raw: Whether to save raw HTML
            raw_data_dir: Directory to save raw HTML files
            
        Returns:
            dict: Table page data or None if failed
        """
        from config import TABLE_URL_TEMPLATE
        
        table_url = TABLE_URL_TEMPLATE.format(table_id=table_id)
        logger.info(f"Scraping table page: {table_url}")
        
        try:
            # Navigate to the table URL
            print(f"Navigating to table page: {table_url}")
            self.driver.get(table_url)
            time.sleep(5)  # Wait for page to load
            
            # Check if we got an error page
            page_source = self.driver.page_source
            if 'must be logged' in page_source.lower():
                print("❌ Authentication error - please make sure you're logged into BGA")
                return None
            
            if 'fatal error' in page_source.lower():
                print("❌ Fatal error on page - table might not be accessible")
                return None
            
            # Save raw HTML if requested
            if save_raw:
                os.makedirs(raw_data_dir, exist_ok=True)
                raw_file_path = os.path.join(raw_data_dir, f"table_{table_id}.html")
                
                with open(raw_file_path, 'w', encoding='utf-8') as f:
                    f.write(page_source)
                logger.info(f"Saved table HTML to {raw_file_path}")
            
            # Parse basic table information
            soup = BeautifulSoup(page_source, 'html.parser')
            
            table_data = {
                'table_id': table_id,
                'url': table_url,
                'scraped_at': datetime.now().isoformat(),
                'html_length': len(page_source),
                'html_content': page_source,
                'players_found': [],
                'elo_data_found': False
            }
            
            # Look for player information and ELO data
            player_elements = soup.find_all('span', class_='playername')
            for player_elem in player_elements:
                player_name = player_elem.get_text().strip()
                if player_name:
                    table_data['players_found'].append(player_name)
            
            # Check if ELO data is present
            if 'rankdetails' in page_source or 'winpoints' in page_source:
                table_data['elo_data_found'] = True
                logger.info(f"ELO data found in table page for {table_id}")
                print(f"✅ ELO data found in table page")
            else:
                logger.warning(f"No ELO data found in table page for {table_id}")
                print("⚠️  No ELO data found in table page")
            
            logger.info(f"Successfully scraped table page for {table_id}")
            return table_data
            
        except Exception as e:
            logger.error(f"Error scraping table page for {table_id}: {e}")
            print(f"❌ Error scraping table page: {e}")
            return None
    
    def extract_player_ids_from_table(self, html_content: str) -> List[str]:
        """
        Extract player IDs from table page HTML using efficient BeautifulSoup parsing
        
        Args:
            html_content: HTML content of the table page
            
        Returns:
            list: List of player IDs found
        """
        player_ids = []
        
        try:
            logger.info("Parsing HTML with BeautifulSoup...")
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Method 1: Look for elements with player IDs in common attributes
            logger.info("Searching for player IDs in element attributes...")
            
            # Look for elements with IDs containing player IDs
            for element in soup.find_all(attrs={'id': True}):
                element_id = element.get('id', '')
                # Look for 8+ digit numbers in IDs
                id_matches = re.findall(r'\d{8,}', element_id)
                for match in id_matches:
                    if match not in player_ids:
                        player_ids.append(match)
            
            # Look for elements with classes containing player IDs
            for element in soup.find_all(attrs={'class': True}):
                classes = element.get('class', [])
                for class_name in classes:
                    class_matches = re.findall(r'\d{8,}', str(class_name))
                    for match in class_matches:
                        if match not in player_ids:
                            player_ids.append(match)
            
            # Method 2: Look for data attributes
            logger.info("Searching for player IDs in data attributes...")
            for element in soup.find_all(attrs=lambda x: any(attr.startswith('data-') for attr in x.keys()) if x and hasattr(x, 'keys') else False):
                try:
                    for attr_name, attr_value in element.attrs.items():
                        if attr_name.startswith('data-'):
                            data_matches = re.findall(r'\d{8,}', str(attr_value))
                            for match in data_matches:
                                if match not in player_ids:
                                    player_ids.append(match)
                except (AttributeError, TypeError) as e:
                    logger.debug(f"Skipping element due to attribute error: {e}")
                    continue
            
            # Method 3: Look in href attributes (links to player profiles)
            logger.info("Searching for player IDs in links...")
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if 'player' in href.lower():
                    href_matches = re.findall(r'\d{8,}', href)
                    for match in href_matches:
                        if match not in player_ids:
                            player_ids.append(match)
            
            # Method 4: Fallback - limited regex search on smaller chunks
            if not player_ids:
                logger.info("Fallback: searching in text content around player names...")
                player_name_elements = soup.find_all('span', class_='playername')
                for elem in player_name_elements:
                    # Get parent elements and search in a limited scope
                    parent = elem.parent
                    if parent:
                        parent_text = str(parent)[:1000]  # Limit to 1000 chars to avoid backtracking
                        simple_matches = re.findall(r'\b\d{8,}\b', parent_text)
                        for match in simple_matches:
                            if match not in player_ids:
                                player_ids.append(match)
            
            # Remove duplicates while preserving order and filter valid IDs
            unique_player_ids = []
            for pid in player_ids:
                if len(pid) >= 8 and len(pid) <= 12 and pid not in unique_player_ids:  # Reasonable length for player IDs
                    unique_player_ids.append(pid)
            
            logger.info(f"Extracted {len(unique_player_ids)} player IDs from table page: {unique_player_ids}")
            return unique_player_ids
            
        except Exception as e:
            logger.error(f"Error extracting player IDs: {e}")
            return []
    
    def scrape_replay_from_table(self, table_id: str, player_id: str, save_raw: bool = True, raw_data_dir: str = 'data/raw') -> Optional[Dict]:
        """
        Scrape replay page using table ID and player ID
        
        Args:
            table_id: BGA table ID
            player_id: Player ID for replay URL construction
            save_raw: Whether to save raw HTML
            raw_data_dir: Directory to save raw HTML files
            
        Returns:
            dict: Replay data or None if failed
        """
        from config import REPLAY_URL_TEMPLATE
        
        replay_url = REPLAY_URL_TEMPLATE.format(table_id=table_id, player_id=player_id)
        logger.info(f"Scraping replay page: {replay_url}")
        
        # Use existing scrape_replay method with constructed URL
        # The scrape_replay method already has robust error handling for authentication issues
        return self.scrape_replay(replay_url, save_raw, raw_data_dir)

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
            
            # Check for authentication errors and retry once
            if 'must be logged' in page_source.lower() or 'fatalerror' in page_source.lower():
                logger.warning("Authentication error detected, attempting re-login...")
                print("⚠️  Session expired! Attempting to re-authenticate...")
                
                # Try to re-authenticate
                self.login_to_bga()
                
                # Retry the replay page
                print(f"Retrying replay page: {url}")
                self.driver.get(url)
                time.sleep(5)
                
                # Check again
                page_source = self.driver.page_source
                if 'must be logged' in page_source.lower() or 'fatalerror' in page_source.lower():
                    print("❌ Authentication failed even after re-login")
                    return None
                else:
                    print("✅ Re-authentication successful!")
            
            if 'fatal error' in page_source.lower() and 'must be logged' not in page_source.lower():
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
    
    def scrape_player_game_history(self, player_id: str, max_clicks: int = 100, 
                                 click_delay: int = 1, filter_arena_season: int = None) -> List[str]:
        """
        Scrape all table IDs from a player's game history by auto-clicking "See more"
        
        Args:
            player_id: BGA player ID
            max_clicks: Maximum number of "See more" clicks to prevent infinite loops
            click_delay: Delay between clicks in seconds
            filter_arena_season: If specified, only return games from this Arena season
            
        Returns:
            list: List of table IDs found in the player's game history
        """
        if not self.driver:
            raise RuntimeError("Browser not started. Call start_browser() first.")
        
        # Construct player history URL - this may need to be adjusted based on actual BGA URL pattern
        player_url = f"https://boardgamearena.com/gamestats?player={player_id}&opponent_id=0&game_id=1924&finished=1"        
        logger.info(f"Scraping game history for player {player_id}")
        
        try:
            # Navigate to player page
            print(f"Navigating to player page: {player_url}")
            self.driver.get(player_url)
            time.sleep(5)  # Wait for page to load
            
            # Check if we got an error page
            page_source = self.driver.page_source
            if 'must be logged' in page_source.lower():
                print("❌ Authentication error - please make sure you're logged into BGA")
                return []
            
            if 'fatal error' in page_source.lower():
                print("❌ Fatal error on page - player page might not be accessible")
                return []
            
            click_count = 0
            games_loaded = 0
            
            print("Starting to load all games by clicking 'See more'...")
            
            while click_count < max_clicks:
                # Primary strategy: Look for the specific ID "see_more_tables"
                see_more_element = None
                
                try:
                    see_more_element = self.driver.find_element(By.ID, "see_more_tables")
                    print(f"Found 'See more' button using ID: see_more_tables")
                except:
                    # Fallback strategies if ID method fails
                    print("ID method failed, trying fallback strategies...")
                    
                    # Strategy 1: Look for exact text "See more"
                    see_more_elements = self.driver.find_elements(By.XPATH, 
                        "//*[contains(text(), 'See more')]")
                    
                    if see_more_elements:
                        see_more_element = see_more_elements[0]
                        print(f"Found 'See more' using text search")
                    
                    # Strategy 2: Look for links with "See more" text
                    if not see_more_element:
                        see_more_elements = self.driver.find_elements(By.XPATH, 
                            "//a[contains(text(), 'See more')]")
                        if see_more_elements:
                            see_more_element = see_more_elements[0]
                            print(f"Found 'See more' link")
                    
                    # Strategy 3: Look for buttons with "See more" text
                    if not see_more_element:
                        see_more_elements = self.driver.find_elements(By.XPATH, 
                            "//button[contains(text(), 'See more')]")
                        if see_more_elements:
                            see_more_element = see_more_elements[0]
                            print(f"Found 'See more' button")
                    
                    # Strategy 4: Look for elements with class names that might indicate "see more"
                    if not see_more_element:
                        see_more_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                            "[class*='more'], [class*='load'], [class*='expand']")
                        for elem in see_more_elements:
                            try:
                                if 'see more' in elem.text.lower() or 'more' in elem.text.lower():
                                    see_more_element = elem
                                    print(f"Found 'See more' using CSS selector: {elem.text}")
                                    break
                            except:
                                continue
                    
                    # Strategy 5: Look for clickable elements at the bottom of the page
                    if not see_more_element:
                        # Scroll to bottom first
                        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(1)
                        
                        # Look for clickable elements near the bottom
                        clickable_elements = self.driver.find_elements(By.XPATH, 
                            "//a | //button | //div[@onclick] | //span[@onclick]")
                        
                        for elem in clickable_elements:
                            try:
                                elem_text = elem.text.lower().strip()
                                if any(phrase in elem_text for phrase in ['see more', 'more', 'load more', 'show more']):
                                    see_more_element = elem
                                    print(f"Found potential 'See more' element: '{elem.text}'")
                                    break
                            except:
                                continue
                
                # If no element found, break
                if not see_more_element:
                    print("No 'See more' button found - all games may be loaded")
                    # Save current page source for debugging
                    if click_count == 0:
                        print("Saving page source for debugging...")
                        with open('debug_page_source.html', 'w', encoding='utf-8') as f:
                            f.write(self.driver.page_source)
                        print("Page source saved to debug_page_source.html")
                    break
                
                # Try to click the found element
                try:
                    # Scroll to element to make sure it's visible
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", see_more_element)
                    time.sleep(1)
                    
                    # Try different click methods
                    try:
                        # Method 1: Regular click
                        see_more_element.click()
                    except:
                        try:
                            # Method 2: JavaScript click
                            self.driver.execute_script("arguments[0].click();", see_more_element)
                        except:
                            # Method 3: Action chains click
                            from selenium.webdriver.common.action_chains import ActionChains
                            ActionChains(self.driver).move_to_element(see_more_element).click().perform()
                    
                    click_count += 1
                    print(f"Clicked 'See more' #{click_count}, waiting for content to load...")
                    time.sleep(click_delay)
                    
                    # Check for "No more results" message
                    no_more_results = self.driver.find_elements(By.XPATH, 
                        "//*[contains(text(), 'No more results')]")
                    
                    if no_more_results:
                        print("✅ 'No more results' detected - all games loaded!")
                        break
                    
                    # Count current games for progress tracking
                    current_games = len(self.driver.find_elements(By.XPATH, 
                        "//*[contains(@class, 'game') or contains(text(), '#')]"))
                    
                    if current_games > games_loaded:
                        games_loaded = current_games
                        print(f"Progress: ~{games_loaded} games loaded so far...")
                    
                except Exception as e:
                    logger.warning(f"Error clicking 'See more' button: {e}")
                    print(f"⚠️  Error clicking 'See more': {e}")
                    print(f"Element tag: {see_more_element.tag_name}, text: '{see_more_element.text}'")
                    break
            
            if click_count >= max_clicks:
                print(f"⚠️  Reached maximum click limit ({max_clicks}). Some games might not be loaded.")
            
            # Extract table IDs from the fully loaded page
            print("Extracting table IDs from loaded page...")
            page_source = self.driver.page_source
            table_ids = self._extract_table_ids_from_history(page_source)
            
            logger.info(f"Successfully extracted {len(table_ids)} table IDs from player {player_id}")
            print(f"✅ Found {len(table_ids)} table IDs for player {player_id}")
            
            return table_ids
            
        except Exception as e:
            logger.error(f"Error scraping player game history for {player_id}: {e}")
            print(f"❌ Error scraping player game history: {e}")
            return []
    
    def _extract_table_ids_from_history(self, html_content: str) -> List[str]:
        """
        Extract table IDs from player game history HTML
        
        Args:
            html_content: HTML content of the player history page
            
        Returns:
            list: List of unique table IDs found
        """
        table_ids = []
        
        try:
            # Method 1: Look for table IDs in the format #XXXXXXXXX
            table_id_pattern = r'#(\d{8,})'
            matches = re.findall(table_id_pattern, html_content)
            table_ids.extend(matches)
            
            # Method 2: Parse with BeautifulSoup for more structured extraction
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for links or elements that might contain table IDs
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if 'table' in href:
                    # Extract table ID from URL parameters
                    table_matches = re.findall(r'table[=:](\d+)', href)
                    table_ids.extend(table_matches)
            
            # Look for elements with table ID text content
            for element in soup.find_all(text=re.compile(r'#\d{8,}')):
                text_matches = re.findall(r'#(\d{8,})', element)
                table_ids.extend(text_matches)
            
            # Remove duplicates while preserving order
            unique_table_ids = []
            seen = set()
            for table_id in table_ids:
                if table_id not in seen and len(table_id) >= 8:
                    unique_table_ids.append(table_id)
                    seen.add(table_id)
            
            logger.info(f"Extracted {len(unique_table_ids)} unique table IDs")
            return unique_table_ids
            
        except Exception as e:
            logger.error(f"Error extracting table IDs from history: {e}")
            return []

    def scrape_multiple_tables_and_replays(self, table_ids: List[str], save_raw: bool = True, 
                                         raw_data_dir: str = 'data/raw') -> List[Dict]:
        """
        Scrape multiple table and replay pages
        
        Args:
            table_ids: List of BGA table IDs
            save_raw: Whether to save raw HTML
            raw_data_dir: Directory to save raw HTML files
            
        Returns:
            list: List of scraped data dictionaries
        """
        results = []
        
        logger.info(f"Starting batch scraping of {len(table_ids)} games (table + replay)")
        
        for i, table_id in enumerate(table_ids, 1):
            logger.info(f"Processing game {i}/{len(table_ids)} (table ID: {table_id})")
            print(f"\nProcessing game {i}/{len(table_ids)} (table ID: {table_id})")
            
            result = self.scrape_table_and_replay(table_id, save_raw, raw_data_dir)
            if result:
                results.append(result)
            
            # Delay between requests (except for the last one)
            if i < len(table_ids):
                print(f"Waiting {self.request_delay} seconds...")
                time.sleep(self.request_delay)
        
        logger.info(f"Batch scraping completed. Successfully scraped {len(results)}/{len(table_ids)} games")
        return results

    def scrape_multiple_replays(self, urls: List[str], save_raw: bool = True, 
                              raw_data_dir: str = 'data/raw') -> List[Dict]:
        """
        Scrape multiple replay pages (legacy method)
        
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
    
    def _check_login_status(self) -> bool:
        """Check if we're still logged into BGA"""
        try:
            if not self.driver:
                return False
            
            # Check current page for login indicators
            page_source = self.driver.page_source.lower()
            
            # If we see login indicators, we're logged out
            if any(indicator in page_source for indicator in ['must be logged', 'login', 'sign in']):
                return False
            
            # If we see logout indicators, we're logged in
            if any(indicator in page_source for indicator in ['logout', 'my account', 'player_name']):
                return True
            
            # If unclear, try a quick navigation to main page to check
            current_url = self.driver.current_url
            self.driver.get("https://boardgamearena.com")
            time.sleep(2)
            
            page_source = self.driver.page_source.lower()
            is_logged_in = any(indicator in page_source for indicator in ['logout', 'my account', 'player_name'])
            
            logger.info(f"Login status check: {'logged in' if is_logged_in else 'logged out'}")
            return is_logged_in
            
        except Exception as e:
            logger.error(f"Error checking login status: {e}")
            return False

    def _extract_replay_id(self, url: str) -> Optional[str]:
        """Extract replay ID from BGA replay URL (table parameter)"""
        try:
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(url)
            
            # Extract the table parameter from query string
            query_params = parse_qs(parsed.query)
            if 'table' in query_params:
                table_values = query_params['table']
                if table_values:
                    return table_values[0]  # Return the first table value
            
            return None
        except Exception as e:
            logger.error(f"Error extracting replay ID from {url}: {e}")
            return None

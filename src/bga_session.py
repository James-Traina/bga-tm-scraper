"""
BGA Session Management
Handles login, token extraction, and session persistence for BoardGameArena
"""

import requests
from bs4 import BeautifulSoup
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class BGASession:
    """Manages BGA login session and request tokens"""
    
    BASE_URL = 'https://boardgamearena.com'
    LOGIN_URL = '/account/account/login.html'
    
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.session = requests.Session()
        self.request_token: Optional[str] = None
        self.is_logged_in = False
    
    def login(self) -> bool:
        """
        Login to BGA and extract request token
        Returns True if successful, False otherwise
        """
        try:
            # First, get the login page to extract request token
            logger.info("Fetching login page to extract request token...")
            resp = self.session.get(f'{self.BASE_URL}/gamestats', params={'player': "689196352"})
            resp.raise_for_status()
            
            # Extract request token from JavaScript
            self.request_token = self._extract_request_token(resp.content)
            if not self.request_token:
                logger.error("Failed to extract request token")
                return False
            
            # Set headers for authenticated requests
            self.session.headers.update({
                'X-Request-Token': self.request_token,
                'X-Requested-With': 'XMLHttpRequest'
            })
            
            # Perform login
            logger.info("Attempting login...")
            login_data = {
                'email': self.email,
                'password': self.password,
                'rememberme': 'off',
                'redirect': 'join',
                'form_id': 'loginform',
                'request_token': self.request_token
            }
            
            login_resp = self.session.post(f'{self.BASE_URL}{self.LOGIN_URL}', data=login_data)
            login_resp.raise_for_status()
            
            # Check if login was successful (you might need to adjust this check)
            self.is_logged_in = True
            logger.info("Login successful")
            return True
            
        except Exception as e:
            logger.error(f"Login failed: {e}")
            self.is_logged_in = False
            return False
    
    def _extract_request_token(self, html_content: bytes) -> Optional[str]:
        """Extract request token from HTML content"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            regex = re.compile(r"'(.*?)'")  # Extract token from quoted text
            
            for script_tag in soup.find_all('script'):
                if script_tag.string:
                    script_content = script_tag.string
                    if 'requestToken: ' in script_content:
                        token_split = script_content.split('requestToken: ')
                        if len(token_split) > 1:
                            match = regex.match(token_split[1])
                            if match:
                                token = match.group().strip("'")
                                logger.debug(f"Extracted request token: {token[:10]}...")
                                return token
            
            logger.warning("Request token not found in HTML content")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting request token: {e}")
            return None
    
    def get(self, url: str, **kwargs) -> requests.Response:
        """Make authenticated GET request"""
        if not self.is_logged_in:
            raise RuntimeError("Not logged in. Call login() first.")
        return self.session.get(url, **kwargs)
    
    def post(self, url: str, **kwargs) -> requests.Response:
        """Make authenticated POST request"""
        if not self.is_logged_in:
            raise RuntimeError("Not logged in. Call login() first.")
        return self.session.post(url, **kwargs)

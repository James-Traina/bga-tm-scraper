"""
Master Games Registry Manager

Handles the centralized registry of all scraped games to prevent duplicates
and maintain a comprehensive overview of all processed games.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Set


class GamesRegistry:
    """Manages the master games registry file"""
    
    def __init__(self, registry_path: str = "data/processed/master_games_registry.json"):
        self.registry_path = registry_path
        self.registry_data = None
        self.load_registry()
    
    def load_registry(self) -> None:
        """Load the master games registry from file"""
        if os.path.exists(self.registry_path):
            try:
                with open(self.registry_path, 'r', encoding='utf-8') as f:
                    self.registry_data = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load registry file: {e}")
                self._create_empty_registry()
        else:
            self._create_empty_registry()
    
    def _create_empty_registry(self) -> None:
        """Create an empty registry structure"""
        self.registry_data = {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "total_games": 0,
                "description": "Master registry of all scraped games across all players"
            },
            "games": {}
        }
    
    def save_registry(self) -> None:
        """Save the registry to file"""
        # Update metadata
        self.registry_data["metadata"]["last_updated"] = datetime.now().isoformat()
        self.registry_data["metadata"]["total_games"] = len(self.registry_data["games"])
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.registry_path), exist_ok=True)
        
        # Save to file
        with open(self.registry_path, 'w', encoding='utf-8') as f:
            json.dump(self.registry_data, f, indent=2, ensure_ascii=False)
    
    def is_game_scraped(self, table_id: str) -> bool:
        """Check if a game has already been scraped"""
        return table_id in self.registry_data["games"]
    
    def get_scraped_game_ids(self) -> Set[str]:
        """Get set of all scraped game IDs"""
        return set(self.registry_data["games"].keys())
    
    def add_game(self, table_id: str, raw_datetime: str, parsed_datetime: str, 
                 players: List[Dict], scraped_by_player: str = None) -> None:
        """Add a game to the registry"""
        game_entry = {
            "table_id": table_id,
            "raw_datetime": raw_datetime,
            "parsed_datetime": parsed_datetime,
            "players": players,
            "scraped_at": datetime.now().isoformat(),
            "scraped_successfully": True
        }
        
        if scraped_by_player:
            game_entry["scraped_by_player"] = scraped_by_player
        
        self.registry_data["games"][table_id] = game_entry
    
    def mark_game_failed(self, table_id: str, error_reason: str, 
                        scraped_by_player: str = None) -> None:
        """Mark a game as failed to scrape"""
        game_entry = {
            "table_id": table_id,
            "scraped_at": datetime.now().isoformat(),
            "scraped_successfully": False,
            "error_reason": error_reason
        }
        
        if scraped_by_player:
            game_entry["scraped_by_player"] = scraped_by_player
        
        self.registry_data["games"][table_id] = game_entry
    
    def get_game_info(self, table_id: str) -> Optional[Dict]:
        """Get information about a specific game"""
        return self.registry_data["games"].get(table_id)
    
    def get_all_games(self) -> Dict[str, Dict]:
        """Get all games in the registry"""
        return self.registry_data["games"]
    
    def get_successful_games(self) -> Dict[str, Dict]:
        """Get only successfully scraped games"""
        return {
            table_id: game_data 
            for table_id, game_data in self.registry_data["games"].items()
            if game_data.get("scraped_successfully", False)
        }
    
    def get_failed_games(self) -> Dict[str, Dict]:
        """Get only failed games"""
        return {
            table_id: game_data 
            for table_id, game_data in self.registry_data["games"].items()
            if not game_data.get("scraped_successfully", True)
        }
    
    def filter_new_games(self, game_list: List[Dict]) -> List[Dict]:
        """Filter out games that have already been scraped"""
        scraped_ids = self.get_scraped_game_ids()
        return [
            game for game in game_list 
            if game.get("table_id") not in scraped_ids
        ]
    
    def get_stats(self) -> Dict:
        """Get registry statistics"""
        all_games = self.registry_data["games"]
        successful = len(self.get_successful_games())
        failed = len(self.get_failed_games())
        
        return {
            "total_games": len(all_games),
            "successful_scrapes": successful,
            "failed_scrapes": failed,
            "success_rate": (successful / len(all_games) * 100) if all_games else 0
        }
    
    def print_stats(self) -> None:
        """Print registry statistics"""
        stats = self.get_stats()
        print(f"\n=== Master Games Registry Stats ===")
        print(f"Total games tracked: {stats['total_games']}")
        print(f"Successfully scraped: {stats['successful_scrapes']}")
        print(f"Failed scrapes: {stats['failed_scrapes']}")
        print(f"Success rate: {stats['success_rate']:.1f}%")

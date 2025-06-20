"""
Utility script to view and manage the master games registry
"""

import json
import sys
from bga_tm_scraper.games_registry import GamesRegistry


def main():
    """Main function to view registry information"""
    
    # Initialize registry
    registry = GamesRegistry()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "stats":
            registry.print_stats()
            
        elif command == "list":
            games = registry.get_successful_games()
            print(f"\n=== Successfully Scraped Games ({len(games)}) ===")
            
            for table_id, game_data in sorted(games.items()):
                print(f"\nGame {table_id}:")
                print(f"  Date: {game_data.get('raw_datetime', 'N/A')}")
                print(f"  Parsed: {game_data.get('parsed_datetime', 'N/A')}")
                print(f"  Players: {len(game_data.get('players', []))}")
                if game_data.get('scraped_by_player'):
                    print(f"  Scraped by: {game_data['scraped_by_player']}")
                print(f"  Scraped at: {game_data.get('scraped_at', 'N/A')}")
                
                # Show player names if available
                players = game_data.get('players', [])
                if players:
                    player_names = [p.get('name', 'Unknown') for p in players if p.get('name')]
                    if player_names:
                        print(f"  Player names: {', '.join(player_names)}")
                        
        elif command == "failed":
            failed_games = registry.get_failed_games()
            print(f"\n=== Failed Games ({len(failed_games)}) ===")
            
            for table_id, game_data in sorted(failed_games.items()):
                print(f"\nGame {table_id}:")
                print(f"  Error: {game_data.get('error_reason', 'Unknown')}")
                print(f"  Attempted at: {game_data.get('scraped_at', 'N/A')}")
                if game_data.get('scraped_by_player'):
                    print(f"  Attempted by: {game_data['scraped_by_player']}")
                    
        elif command == "search":
            if len(sys.argv) < 3:
                print("Usage: python view_registry.py search <table_id>")
                return
                
            table_id = sys.argv[2]
            game_info = registry.get_game_info(table_id)
            
            if game_info:
                print(f"\n=== Game {table_id} ===")
                print(json.dumps(game_info, indent=2, ensure_ascii=False))
            else:
                print(f"Game {table_id} not found in registry")
                
        elif command == "export":
            filename = "master_games_export.json" if len(sys.argv) < 3 else sys.argv[2]
            all_games = registry.get_all_games()
            
            export_data = {
                'exported_at': registry.registry_data['metadata']['last_updated'],
                'total_games': len(all_games),
                'games': all_games
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            print(f"Registry exported to {filename}")
            
        else:
            print_help()
    else:
        print_help()
        registry.print_stats()


def print_help():
    """Print help information"""
    print("\n=== Master Games Registry Viewer ===")
    print("Usage: python view_registry.py <command>")
    print("\nCommands:")
    print("  stats          - Show registry statistics")
    print("  list           - List all successfully scraped games")
    print("  failed         - List all failed games")
    print("  search <id>    - Search for a specific game by table ID")
    print("  export [file]  - Export registry to JSON file")
    print("\nExamples:")
    print("  python view_registry.py stats")
    print("  python view_registry.py list")
    print("  python view_registry.py search 688771617")
    print("  python view_registry.py export my_games.json")


if __name__ == "__main__":
    main()

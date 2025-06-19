#!/usr/bin/env python3
"""
Game Reparser Script
Reparse games from existing HTML files using the latest parser logic
"""

import argparse
import os
import sys
import logging
from typing import List, Optional
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def setup_directories():
    """Ensure required directories exist"""
    directories = ['data/raw', 'data/parsed']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def get_game_ids_from_args(args) -> List[str]:
    """Get game IDs from command line arguments"""
    game_ids = []
    
    # If --file argument provided, read from file
    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                for line in f:
                    game_id = line.strip()
                    if game_id and game_id.isdigit():
                        game_ids.append(game_id)
            print(f"📁 Loaded {len(game_ids)} game IDs from {args.file}")
        except FileNotFoundError:
            print(f"❌ File not found: {args.file}")
            return []
        except Exception as e:
            print(f"❌ Error reading file {args.file}: {e}")
            return []
    
    # Add game IDs from positional arguments
    if args.game_ids:
        for game_id in args.game_ids:
            if game_id.isdigit():
                game_ids.append(game_id)
            else:
                print(f"⚠️  Skipping invalid game ID: {game_id}")
    
    return game_ids

def get_game_ids_interactive() -> List[str]:
    """Get game IDs through interactive input"""
    print("\n🎮 Interactive Game Reparser")
    print("=" * 40)
    print("Enter game IDs to reparse (one per line)")
    print("Press Enter on empty line to start processing")
    print("Type 'quit' to exit")
    print()
    
    game_ids = []
    while True:
        try:
            game_id = input("Game ID: ").strip()
            
            if not game_id:
                break
            
            if game_id.lower() == 'quit':
                print("👋 Goodbye!")
                sys.exit(0)
            
            if game_id.isdigit():
                game_ids.append(game_id)
                print(f"✅ Added game ID: {game_id}")
            else:
                print(f"❌ Invalid game ID: {game_id} (must be numeric)")
        
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            sys.exit(0)
    
    return game_ids

def check_html_files_exist(game_id: str) -> tuple[bool, str, str, str]:
    """Check if required HTML files exist for a game ID and return player perspective"""
    import glob
    
    # First check if files exist in root data/raw directory (old format)
    table_path = f"data/raw/table_{game_id}.html"
    replay_path = f"data/raw/replay_{game_id}.html"
    
    if os.path.exists(table_path) and os.path.exists(replay_path):
        return True, table_path, replay_path, None
    
    # Check in player perspective folders (new format)
    # Look for table file in any player perspective folder
    table_pattern = f"data/raw/*/table_{game_id}.html"
    table_matches = glob.glob(table_pattern)
    
    # Look for replay file in any player perspective folder
    replay_pattern = f"data/raw/*/replay_{game_id}.html"
    replay_matches = glob.glob(replay_pattern)
    
    if table_matches and replay_matches:
        # Extract player perspective from the path
        table_path = table_matches[0]
        replay_path = replay_matches[0]
        
        # Extract player ID from path like "data/raw/96014413/table_687877071.html"
        player_perspective = os.path.basename(os.path.dirname(table_path))
        
        return True, table_path, replay_path, player_perspective
    
    return False, table_path, replay_path, None

def reparse_single_game(game_id: str) -> dict:
    """Reparse a single game and return result"""
    result = {
        'game_id': game_id,
        'success': False,
        'error': None,
        'output_file': None,
        'players_count': 0,
        'moves_count': 0,
        'elo_data_included': False
    }
    
    try:
        # Check if HTML files exist
        files_exist, table_path, replay_path, player_perspective = check_html_files_exist(game_id)
        
        if not files_exist:
            missing_files = []
            if not os.path.exists(table_path):
                missing_files.append(f"table_{game_id}.html")
            if not os.path.exists(replay_path):
                missing_files.append(f"replay_{game_id}.html")
            
            result['error'] = f"Missing files: {', '.join(missing_files)}"
            return result
        
        # Read HTML files
        print(f"📖 Reading HTML files for game {game_id}...")
        if player_perspective:
            print(f"   Found files in player perspective folder: {player_perspective}")
        
        with open(table_path, 'r', encoding='utf-8') as f:
            table_html = f.read()
        
        with open(replay_path, 'r', encoding='utf-8') as f:
            replay_html = f.read()
        
        # Initialize parser
        from src.parser import Parser
        parser = Parser()
        
        # Parse the game with ELO data
        print(f"🔄 Parsing game {game_id}...")
        game_data = parser.parse_complete_game_with_elo(
            replay_html=replay_html,
            table_html=table_html,
            table_id=game_id
        )
        
        # Export to JSON with player perspective if available
        if player_perspective:
            output_path = f"data/parsed/{player_perspective}/game_{game_id}.json"
            print(f"💾 Saving to {output_path} (player perspective: {player_perspective})...")
            parser.export_to_json(game_data, output_path)
        else:
            output_path = f"data/parsed/game_{game_id}.json"
            print(f"💾 Saving to {output_path}...")
            parser.export_to_json(game_data, output_path)
        
        # Update result
        result['success'] = True
        result['output_file'] = output_path
        result['players_count'] = len(game_data.players)
        result['moves_count'] = len(game_data.moves)
        result['elo_data_included'] = game_data.metadata.get('elo_data_included', False)
        
        print(f"✅ Successfully reparsed game {game_id}")
        print(f"   Players: {result['players_count']}, Moves: {result['moves_count']}, ELO: {'✅' if result['elo_data_included'] else '❌'}")
        
        return result
        
    except Exception as e:
        result['error'] = str(e)
        print(f"❌ Error reparsing game {game_id}: {e}")
        logger.error(f"Error reparsing game {game_id}: {e}")
        return result

def print_summary(results: List[dict]):
    """Print summary of reparsing results"""
    if not results:
        print("\n📋 No games processed")
        return
    
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    print(f"\n📋 Reparsing Summary")
    print("=" * 40)
    print(f"Total games processed: {len(results)}")
    print(f"✅ Successful: {len(successful)}")
    print(f"❌ Failed: {len(failed)}")
    
    if successful:
        total_players = sum(r['players_count'] for r in successful)
        total_moves = sum(r['moves_count'] for r in successful)
        elo_games = len([r for r in successful if r['elo_data_included']])
        
        print(f"\n📊 Statistics:")
        print(f"   Total players: {total_players}")
        print(f"   Total moves: {total_moves}")
        print(f"   Games with ELO data: {elo_games}/{len(successful)}")
    
    if failed:
        print(f"\n❌ Failed Games:")
        for result in failed:
            print(f"   {result['game_id']}: {result['error']}")
    
    if successful:
        print(f"\n✅ Successfully Reparsed:")
        for result in successful:
            print(f"   {result['game_id']}: {result['players_count']} players, {result['moves_count']} moves")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Reparse Terraforming Mars games from existing HTML files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s 672420918                    # Reparse single game
  %(prog)s 672420918 674028385          # Reparse multiple games
  %(prog)s --file game_ids.txt          # Reparse games from file
  %(prog)s                              # Interactive mode
        """
    )
    
    parser.add_argument(
        'game_ids',
        nargs='*',
        help='Game IDs to reparse'
    )
    
    parser.add_argument(
        '--file', '-f',
        help='File containing game IDs (one per line)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Setup logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Setup directories
    setup_directories()
    
    # Get game IDs
    game_ids = get_game_ids_from_args(args)
    
    # If no game IDs provided, use interactive mode
    if not game_ids:
        game_ids = get_game_ids_interactive()
    
    if not game_ids:
        print("❌ No game IDs provided")
        return
    
    # Remove duplicates while preserving order
    unique_game_ids = []
    seen = set()
    for game_id in game_ids:
        if game_id not in seen:
            unique_game_ids.append(game_id)
            seen.add(game_id)
    
    print(f"\n🚀 Starting to reparse {len(unique_game_ids)} games...")
    print("=" * 50)
    
    # Process each game
    results = []
    for i, game_id in enumerate(unique_game_ids, 1):
        print(f"\n--- Processing game {i}/{len(unique_game_ids)} (ID: {game_id}) ---")
        
        result = reparse_single_game(game_id)
        results.append(result)
        
        # Add delay between games (except for the last one)
        if i < len(unique_game_ids):
            print("⏱️  Waiting 1 second before next game...")
            import time
            time.sleep(1)
    
    # Print summary
    print_summary(results)
    
    print(f"\n🎉 Reparsing complete!")

if __name__ == "__main__":
    main()

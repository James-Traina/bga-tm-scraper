#!/usr/bin/env python3
"""
Re-parse the game with the fixed parser and save the updated JSON
"""

import os
import sys
import logging
from src.parser import Parser

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def reparse_and_save_game():
    """Re-parse the game and save the updated JSON"""
    
    # Initialize parser
    parser = Parser()
    
    # File paths
    html_file = "data/raw/replay_688769496.html"
    output_file = "data/parsed/game_688769496_fixed.json"
    
    if not os.path.exists(html_file):
        logger.error(f"HTML file not found: {html_file}")
        return False
    
    try:
        # Read HTML content
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        logger.info("Re-parsing game with fixed parser...")
        
        # Parse the game
        game_data = parser.parse_complete_game(html_content, "688769496")
        
        # Export to JSON
        parser.export_to_json(game_data, output_file)
        
        logger.info(f"Successfully saved updated game data to: {output_file}")
        
        # Print summary
        logger.info("=== PARSING SUMMARY ===")
        logger.info(f"Total moves: {len(game_data.moves)}")
        logger.info(f"VP progression entries: {len(game_data.vp_progression)}")
        logger.info(f"Players: {len(game_data.players)}")
        
        # Check VP data in moves
        moves_with_vp = sum(1 for move in game_data.moves if move.game_state and move.game_state.player_vp)
        logger.info(f"Moves with VP data: {moves_with_vp}/{len(game_data.moves)}")
        
        # Check milestone and award data
        moves_with_milestones = sum(1 for move in game_data.moves if move.game_state and move.game_state.milestones)
        moves_with_awards = sum(1 for move in game_data.moves if move.game_state and move.game_state.awards)
        logger.info(f"Moves with milestone data: {moves_with_milestones}/{len(game_data.moves)}")
        logger.info(f"Moves with award data: {moves_with_awards}/{len(game_data.moves)}")
        
        # Show sample VP data from a few moves
        logger.info("\n=== SAMPLE VP DATA ===")
        for i, move in enumerate(game_data.moves[::50]):  # Every 50th move
            if move.game_state and move.game_state.player_vp:
                logger.info(f"Move {move.move_number}:")
                for player_id, vp_data in move.game_state.player_vp.items():
                    if isinstance(vp_data, dict):
                        total = vp_data.get('total', 'N/A')
                        details = vp_data.get('total_details', {})
                        logger.info(f"  Player {player_id}: {total} VP (TR: {details.get('tr', 'N/A')}, Cards: {details.get('cards', 'N/A')}, Cities: {details.get('cities', 'N/A')})")
        
        # Show milestone and award data if any
        final_state = game_data.final_state
        if final_state.milestones:
            logger.info(f"\n=== MILESTONES ===")
            for milestone, data in final_state.milestones.items():
                logger.info(f"{milestone}: {data}")
        
        if final_state.awards:
            logger.info(f"\n=== AWARDS ===")
            for award, data in final_state.awards.items():
                logger.info(f"{award}: {data}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error re-parsing game: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = reparse_and_save_game()
    if success:
        print("✅ Game re-parsing completed successfully!")
        print("📁 Updated JSON saved as: data/parsed/game_688769496_fixed.json")
    else:
        print("❌ Game re-parsing failed!")
        sys.exit(1)

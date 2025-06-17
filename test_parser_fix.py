#!/usr/bin/env python3
"""
Test script to verify the parser fixes for VP, milestone, and award extraction
"""

import os
import sys
import logging
from src.parser import Parser

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_parser_with_sample_game():
    """Test the parser with the sample game data"""
    
    # Initialize parser
    parser = Parser()
    
    # Look for HTML files in the raw data directory
    raw_data_dir = "data/raw"
    if not os.path.exists(raw_data_dir):
        logger.error(f"Raw data directory not found: {raw_data_dir}")
        return False
    
    # Find HTML files
    html_files = [f for f in os.listdir(raw_data_dir) if f.endswith('.html')]
    if not html_files:
        logger.error("No HTML files found in raw data directory")
        return False
    
    # Use the first HTML file for testing
    test_file = html_files[0]
    html_path = os.path.join(raw_data_dir, test_file)
    
    logger.info(f"Testing parser with file: {test_file}")
    
    try:
        # Read HTML content
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Extract game ID from filename
        game_id = test_file.replace('.html', '').replace('game_', '')
        
        # Parse the game
        game_data = parser.parse_complete_game(html_content, game_id)
        
        # Check if we have moves
        if not game_data.moves:
            logger.error("No moves found in parsed data")
            return False
        
        logger.info(f"Successfully parsed {len(game_data.moves)} moves")
        
        # Check VP progression
        logger.info(f"VP progression entries: {len(game_data.vp_progression)}")
        
        # Check a few moves for VP data
        moves_with_vp = 0
        moves_with_milestones = 0
        moves_with_awards = 0
        
        for i, move in enumerate(game_data.moves[:10]):  # Check first 10 moves
            if move.game_state:
                if move.game_state.player_vp:
                    moves_with_vp += 1
                    logger.info(f"Move {move.move_number}: VP data found for {len(move.game_state.player_vp)} players")
                    
                    # Show sample VP data
                    for player_id, vp_data in move.game_state.player_vp.items():
                        if isinstance(vp_data, dict) and 'total' in vp_data:
                            logger.info(f"  Player {player_id}: {vp_data['total']} VP")
                
                if move.game_state.milestones:
                    moves_with_milestones += 1
                    logger.info(f"Move {move.move_number}: Milestones: {list(move.game_state.milestones.keys())}")
                
                if move.game_state.awards:
                    moves_with_awards += 1
                    logger.info(f"Move {move.move_number}: Awards: {list(move.game_state.awards.keys())}")
        
        logger.info(f"Summary:")
        logger.info(f"  Moves with VP data: {moves_with_vp}/10")
        logger.info(f"  Moves with milestone data: {moves_with_milestones}/10")
        logger.info(f"  Moves with award data: {moves_with_awards}/10")
        
        # Test g_gamelogs extraction
        gamelogs = parser._extract_g_gamelogs(html_content)
        if gamelogs:
            logger.info(f"Successfully extracted g_gamelogs with {len(gamelogs.get('data', {}).get('data', []))} entries")
            
            # Test scoring data extraction
            scoring_entries = parser._parse_scoring_data_from_gamelogs(gamelogs)
            logger.info(f"Found {len(scoring_entries)} scoring entries")
            
            # Show sample scoring data
            if scoring_entries:
                sample_entry = scoring_entries[0]
                logger.info(f"Sample scoring entry: move_id={sample_entry.get('move_id')}, players={len(sample_entry.get('scoring_data', {}))}")
        else:
            logger.warning("g_gamelogs not found or empty")
        
        return True
        
    except Exception as e:
        logger.error(f"Error testing parser: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_parser_with_sample_game()
    if success:
        print("✅ Parser test completed successfully!")
    else:
        print("❌ Parser test failed!")
        sys.exit(1)

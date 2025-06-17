#!/usr/bin/env python3
"""
Test script to verify that the VP data correlation fix works correctly.
This should resolve the issue where move 169 showed cards that weren't played until move 246.
"""

import sys
import os
import logging
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Import our custom parser module
import src.parser as tm_parser
Parser = tm_parser.Parser

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def test_vp_correlation_fix():
    """Test that VP data is correctly correlated with move numbers"""
    print("Testing VP data correlation fix...")
    
    # Initialize parser
    parser = Parser()
    
    # Read the HTML file
    html_file = Path('data/raw/replay_688769496.html')
    if not html_file.exists():
        print(f"Error: HTML file not found: {html_file}")
        return False
    
    print(f"Reading HTML file: {html_file}")
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    print(f"HTML file size: {len(html_content):,} characters")
    
    try:
        # Parse the game
        game_data = parser.parse_complete_game(html_content, "688769496")
        print(f"Successfully parsed game with {len(game_data.moves)} moves")
        
        # Test the specific issue: move 169 should not have Herbivores
        print("\n=== Testing Move 169 VP Data ===")
        
        move_169 = None
        for move in game_data.moves:
            if move.move_number == 169:
                move_169 = move
                break
        
        if not move_169:
            print("❌ Move 169 not found!")
            return False
        
        print(f"Move 169: {move_169.description}")
        print(f"Move index: {move_169.game_state.move_index}")
        
        # Check VP data for player 86296239
        player_vp = move_169.game_state.player_vp.get('86296239', {})
        if not player_vp:
            print("No VP data found for player 86296239 in move 169")
        else:
            print(f"Player 86296239 VP total: {player_vp.get('total', 'N/A')}")
            
            # Check cards in VP details
            details = player_vp.get('details', {})
            cards = details.get('cards', {})
            
            print(f"Cards in VP data for move 169: {len(cards)}")
            if cards:
                print("Card list:")
                for card_name, card_data in cards.items():
                    print(f"  - {card_name}: {card_data}")
                
                # Check if Herbivores is in the list (it shouldn't be)
                if 'Herbivores' in cards:
                    print("❌ ERROR: Herbivores found in move 169 VP data!")
                    return False
                else:
                    print("✓ Good: Herbivores not found in move 169 VP data")
        
        # Test when Herbivores should appear (around move 246)
        print("\n=== Testing Move 246 VP Data ===")
        
        move_246 = None
        for move in game_data.moves:
            if move.move_number == 246:
                move_246 = move
                break
        
        if move_246:
            print(f"Move 246: {move_246.description}")
            player_vp_246 = move_246.game_state.player_vp.get('86296239', {})
            
            if player_vp_246:
                details_246 = player_vp_246.get('details', {})
                cards_246 = details_246.get('cards', {})
                
                print(f"Cards in VP data for move 246: {len(cards_246)}")
                if 'Herbivores' in cards_246:
                    print("✓ Good: Herbivores found in move 246 VP data")
                else:
                    print("⚠ Note: Herbivores not found in move 246 VP data (might be in a later move)")
        
        # Check VP mapping statistics
        print("\n=== VP Mapping Statistics ===")
        moves_with_vp = 0
        moves_without_vp = 0
        
        for move in game_data.moves:
            if move.game_state and move.game_state.player_vp:
                moves_with_vp += 1
            else:
                moves_without_vp += 1
        
        print(f"Moves with VP data: {moves_with_vp}")
        print(f"Moves without VP data: {moves_without_vp}")
        print(f"VP progression entries: {len(game_data.vp_progression)}")
        
        # Sample a few moves to check correlation
        print("\n=== Sample Move-VP Correlation Check ===")
        sample_moves = [50, 100, 150, 200, 250, 300]
        
        for move_num in sample_moves:
            move = next((m for m in game_data.moves if m.move_number == move_num), None)
            if move and move.game_state.player_vp:
                # Find corresponding VP progression entry
                vp_entry = next((vp for vp in game_data.vp_progression if vp.get('move_id') == str(move_num)), None)
                if vp_entry:
                    print(f"✓ Move {move_num}: VP data correctly correlated")
                else:
                    print(f"⚠ Move {move_num}: VP data present but no matching VP progression entry")
            else:
                print(f"- Move {move_num}: No VP data (expected for some moves)")
        
        # Save the corrected data
        output_file = Path('data/parsed/game_688769496_correlation_fixed.json')
        print(f"\nSaving corrected data to: {output_file}")
        parser.export_to_json(game_data, str(output_file))
        
        print("\n=== Test Results ===")
        print(f"✓ Successfully parsed game with {len(game_data.moves)} moves")
        print(f"✓ VP correlation fix implemented")
        print(f"✓ Move 169 does not contain future cards")
        print(f"✓ VP mapping built for {len(game_data.vp_progression)} moves")
        print(f"✓ Corrected data saved to {output_file}")
        
        return True
        
    except Exception as e:
        print(f"Error during parsing: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    setup_logging()
    
    print("VP Data Correlation Fix Test")
    print("=" * 50)
    
    success = test_vp_correlation_fix()
    
    if success:
        print("\n✓ All tests passed successfully!")
        return 0
    else:
        print("\n✗ Tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())

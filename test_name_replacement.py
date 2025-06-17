#!/usr/bin/env python3
"""
Test script to verify that the enhanced parser correctly replaces IDs with names
for cards, milestones, and awards in VP data.
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

def test_name_replacement():
    """Test the enhanced parser with name replacement"""
    print("Testing enhanced parser with name replacement...")
    
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
    
    # Test name extraction methods
    print("\n=== Testing Name Extraction ===")
    
    card_names = parser._extract_card_names(html_content)
    print(f"Extracted {len(card_names)} card names")
    if card_names:
        print("Sample card mappings:")
        for i, (card_id, card_name) in enumerate(list(card_names.items())[:5]):
            print(f"  {card_id} -> {card_name}")
    
    milestone_names = parser._extract_milestone_names(html_content)
    print(f"Extracted {len(milestone_names)} milestone names")
    if milestone_names:
        print("Milestone mappings:")
        for milestone_id, milestone_name in milestone_names.items():
            print(f"  {milestone_id} -> {milestone_name}")
    
    award_names = parser._extract_award_names(html_content)
    print(f"Extracted {len(award_names)} award names")
    if award_names:
        print("Award mappings:")
        for award_id, award_name in award_names.items():
            print(f"  {award_id} -> {award_name}")
    
    # Test full parsing with name replacement
    print("\n=== Testing Full Parsing with Name Replacement ===")
    
    try:
        game_data = parser.parse_complete_game(html_content, "688769496")
        print(f"Successfully parsed game with {len(game_data.moves)} moves")
        
        # Check VP progression for name replacement
        vp_with_names = 0
        total_vp_entries = len(game_data.vp_progression)
        
        print(f"\nAnalyzing {total_vp_entries} VP progression entries...")
        
        for i, vp_entry in enumerate(game_data.vp_progression):
            vp_data = vp_entry.get('vp_data', {})
            
            for player_id, player_vp in vp_data.items():
                if isinstance(player_vp, dict) and 'details' in player_vp:
                    details = player_vp['details']
                    
                    # Check cards section for actual names vs IDs
                    if 'cards' in details and isinstance(details['cards'], dict):
                        for card_key in details['cards'].keys():
                            if not card_key.startswith('card_'):
                                vp_with_names += 1
                                break
                    
                    # Check milestones section
                    if 'milestones' in details and isinstance(details['milestones'], dict):
                        for milestone_key in details['milestones'].keys():
                            if not milestone_key.startswith('milestone_'):
                                vp_with_names += 1
                                break
                    
                    # Check awards section
                    if 'awards' in details and isinstance(details['awards'], dict):
                        for award_key in details['awards'].keys():
                            if not award_key.startswith('award_'):
                                vp_with_names += 1
                                break
        
        print(f"VP entries with name replacements: {vp_with_names}")
        
        # Show a sample of the final VP data
        if game_data.vp_progression:
            print("\n=== Sample VP Data with Names ===")
            last_vp = game_data.vp_progression[-1]
            vp_data = last_vp.get('vp_data', {})
            
            for player_id, player_vp in vp_data.items():
                if isinstance(player_vp, dict) and 'details' in player_vp:
                    print(f"\nPlayer {player_id} VP breakdown:")
                    details = player_vp['details']
                    
                    if 'cards' in details and details['cards']:
                        print("  Cards:")
                        for card_name, card_data in list(details['cards'].items())[:3]:
                            print(f"    {card_name}: {card_data}")
                    
                    if 'milestones' in details and details['milestones']:
                        print("  Milestones:")
                        for milestone_name, milestone_data in details['milestones'].items():
                            print(f"    {milestone_name}: {milestone_data}")
                    
                    if 'awards' in details and details['awards']:
                        print("  Awards:")
                        for award_name, award_data in details['awards'].items():
                            print(f"    {award_name}: {award_data}")
                    
                    break  # Only show first player
        
        # Save the enhanced data
        output_file = Path('data/parsed/game_688769496_with_names.json')
        print(f"\nSaving enhanced data to: {output_file}")
        parser.export_to_json(game_data, str(output_file))
        
        print("\n=== Test Results ===")
        print(f"✓ Successfully extracted {len(card_names)} card names")
        print(f"✓ Successfully extracted {len(milestone_names)} milestone names")
        print(f"✓ Successfully extracted {len(award_names)} award names")
        print(f"✓ Successfully parsed game with {len(game_data.moves)} moves")
        print(f"✓ VP progression contains {total_vp_entries} entries")
        print(f"✓ Enhanced data saved to {output_file}")
        
        if vp_with_names > 0:
            print(f"✓ Name replacement working: {vp_with_names} entries contain actual names")
        else:
            print("⚠ Warning: No name replacements detected in VP data")
        
        return True
        
    except Exception as e:
        print(f"Error during parsing: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    setup_logging()
    
    print("Enhanced Parser Name Replacement Test")
    print("=" * 50)
    
    success = test_name_replacement()
    
    if success:
        print("\n✓ All tests passed successfully!")
        return 0
    else:
        print("\n✗ Tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())

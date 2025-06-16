#!/usr/bin/env python3
"""
Test script for the Terraforming Mars parser
"""
import os
import json
import logging
from src.parser import Parser

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_parser():
    """Test the parser with the existing game data"""
    
    # Initialize parser
    parser = Parser()
    
    # Load the HTML file
    html_file = "data/raw/replay_250604-1037.html"
    
    if not os.path.exists(html_file):
        print(f"❌ HTML file not found: {html_file}")
        print("Please ensure you have scraped game data first.")
        return
    
    print(f"📖 Loading HTML file: {html_file}")
    
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    print(f"✅ Loaded HTML file ({len(html_content):,} characters)")
    
    # Parse the game
    print(f"🔄 Parsing game with parser...")
    
    try:
        game_data = parser.parse_complete_game(html_content, "250604-1037")
        
        print(f"✅ Parsing successful!")
        print(f"   Replay ID: {game_data.replay_id}")
        print(f"   Game Date: {game_data.game_date}")
        print(f"   Duration: {game_data.game_duration}")
        print(f"   Winner: {game_data.winner}")
        print(f"   Players: {len(game_data.players)}")
        print(f"   Total Moves: {len(game_data.moves)}")
        print(f"   VP Progression Points: {len(game_data.vp_progression)}")
        print(f"   Parameter Progression Points: {len(game_data.parameter_progression)}")
        
        # Show player details
        print(f"\n👥 Player Details:")
        for player_id, player in game_data.players.items():
            print(f"   {player.player_name} ({player_id}):")
            print(f"     Corporation: {player.corporation}")
            print(f"     Final VP: {player.final_vp}")
            print(f"     Final TR: {player.final_tr}")
            print(f"     Cards Played: {len(player.cards_played)}")
            print(f"     Milestones: {player.milestones_claimed}")
            print(f"     Awards: {player.awards_funded}")
        
        # Show final game state
        print(f"\n🌍 Final Game State:")
        final = game_data.final_state
        print(f"   Generation: {final.generation}")
        print(f"   Temperature: {final.temperature}°C")
        print(f"   Oxygen: {final.oxygen}%")
        print(f"   Oceans: {final.oceans}")
        
        # Show some move examples
        print(f"\n🎮 Sample Moves:")
        for i, move in enumerate(game_data.moves[:5]):
            print(f"   Move {move.move_number} ({move.timestamp}): {move.player_name} - {move.action_type}")
            if move.card_played:
                print(f"     Card: {move.card_played}")
            if move.tile_placed:
                print(f"     Tile: {move.tile_placed} at {move.tile_location}")
            if move.resource_changes:
                print(f"     Resources: {move.resource_changes}")
            if move.production_changes:
                print(f"     Production: {move.production_changes}")
        
        # Export to JSON
        output_file = "data/parsed/game_250604-1037.json"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        print(f"\n💾 Exporting to: {output_file}")
        parser.export_to_json(game_data, output_file)
        
        # Show file size
        file_size = os.path.getsize(output_file)
        print(f"✅ Export complete! File size: {file_size:,} bytes")
        
        # Show some statistics
        print(f"\n📊 Game Statistics:")
        card_plays = [m for m in game_data.moves if m.action_type == 'play_card']
        tile_placements = [m for m in game_data.moves if m.action_type == 'place_tile']
        
        print(f"   Card plays: {len(card_plays)}")
        print(f"   Tile placements: {len(tile_placements)}")
        print(f"   Generations: {final.generation}")
        
        # VP progression analysis
        if game_data.vp_progression:
            start_vp = game_data.vp_progression[0]['combined_total']
            end_vp = game_data.vp_progression[-1]['combined_total']
            print(f"   VP progression: {start_vp} → {end_vp}")
        
        return game_data
        
    except Exception as e:
        print(f"❌ Error during parsing: {e}")
        import traceback
        traceback.print_exc()
        return None

def analyze_unified_data():
    """Analyze the game data"""
    
    output_file = "data/parsed/game_250604-1037.json"
    
    if not os.path.exists(output_file):
        print(f"❌ Data file not found: {output_file}")
        print("Run the parser first.")
        return
    
    print(f"📊 Analyzing game data...")
    
    with open(output_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"✅ Loaded data")
    
    # Analyze move distribution by type
    move_types = {}
    for move in data['moves']:
        action_type = move['action_type']
        move_types[action_type] = move_types.get(action_type, 0) + 1
    
    print(f"\n🎯 Move Type Distribution:")
    for action_type, count in sorted(move_types.items(), key=lambda x: x[1], reverse=True):
        print(f"   {action_type}: {count}")
    
    # Analyze resource flow
    print(f"\n💰 Resource Analysis:")
    total_resources = {}
    for move in data['moves']:
        for resource, change in move['resource_changes'].items():
            total_resources[resource] = total_resources.get(resource, 0) + abs(change)
    
    for resource, total in sorted(total_resources.items(), key=lambda x: x[1], reverse=True):
        print(f"   {resource}: {total} total changes")
    
    # Analyze VP progression
    if data['vp_progression']:
        print(f"\n📈 VP Progression Analysis:")
        vp_points = [entry['combined_total'] for entry in data['vp_progression']]
        print(f"   Start: {vp_points[0]} VP")
        print(f"   End: {vp_points[-1]} VP")
        print(f"   Peak: {max(vp_points)} VP")
        print(f"   Data points: {len(vp_points)}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'analyze':
        analyze_unified_data()
    else:
        game_data = test_parser()
        if game_data:
            print(f"\n🎉 Parsing test completed successfully!")
            print(f"   Run 'python test_parser.py analyze' to analyze the data")

"""
Test script for the Terraforming Mars parser
"""
import os
import logging
from src.parser import TMGameParser

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_parser():
    """Test the parser with existing scraped data"""
    
    # Initialize parser
    parser = TMGameParser()
    
    # Load the raw HTML file
    html_file = 'data/raw/replay_250604-1037.html'
    
    if not os.path.exists(html_file):
        print(f"❌ HTML file not found: {html_file}")
        return
    
    print(f"📖 Loading HTML file: {html_file}")
    
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    print(f"✅ Loaded HTML file ({len(html_content):,} characters)")
    
    # Parse the game
    print("\n🔍 Parsing game...")
    replay_id = "250604-1037"
    game = parser.parse_game_from_html(html_content, replay_id)
    
    # Display results
    print(f"\n📊 Parsing Results:")
    print(f"   Replay ID: {game.replay_id}")
    print(f"   Players: {game.players}")
    print(f"   Corporations: {game.corporations}")
    print(f"   Total moves: {len(game.moves)}")
    print(f"   Final state:")
    print(f"     Generation: {game.final_state.generation}")
    print(f"     Temperature: {game.final_state.temperature}°C")
    print(f"     Oxygen: {game.final_state.oxygen}%")
    print(f"     Oceans: {game.final_state.oceans}")
    
    # Show some example moves
    print(f"\n🎯 Sample Moves:")
    for i, move in enumerate(game.moves[:10]):  # First 10 moves
        print(f"   Move {move.move_number}: {move.player} - {move.action_type}")
        if move.card_play:
            print(f"     Card: {move.card_play.card_name}")
        if move.tile_place:
            print(f"     Tile: {move.tile_place.tile_type} at {move.tile_place.location}")
        if move.parameter_changes:
            print(f"     Parameters: {move.parameter_changes}")
        print(f"     Description: {move.description[:100]}...")
        print()
    
    # Show action type distribution
    action_types = {}
    for move in game.moves:
        action_types[move.action_type] = action_types.get(move.action_type, 0) + 1
    
    print(f"📈 Action Type Distribution:")
    for action_type, count in sorted(action_types.items(), key=lambda x: x[1], reverse=True):
        print(f"   {action_type}: {count}")
    
    # Export results
    print(f"\n💾 Exporting results...")
    
    # Create output directory
    os.makedirs('data/parsed', exist_ok=True)
    
    # Export to JSON
    json_file = f'data/parsed/game_{replay_id}.json'
    parser.export_to_json(game, json_file)
    print(f"   ✅ JSON exported to: {json_file}")
    
    # Export to CSV
    csv_file = f'data/parsed/moves_{replay_id}.csv'
    parser.export_moves_to_csv(game, csv_file)
    print(f"   ✅ CSV exported to: {csv_file}")
    
    # Show some statistics
    card_plays = [move for move in game.moves if move.action_type == 'play_card']
    tile_places = [move for move in game.moves if move.tile_place]
    
    print(f"\n📊 Game Statistics:")
    print(f"   Cards played: {len(card_plays)}")
    print(f"   Tiles placed: {len(tile_places)}")
    print(f"   Game duration: {game.moves[-1].timestamp if game.moves else 'Unknown'}")
    
    # Show unique cards played
    unique_cards = set()
    for move in card_plays:
        if move.card_play and move.card_play.card_name:
            unique_cards.add(move.card_play.card_name)
    
    print(f"   Unique cards: {len(unique_cards)}")
    if unique_cards:
        print(f"   Sample cards: {list(unique_cards)[:5]}")
    
    print(f"\n🎉 Parser test completed successfully!")

if __name__ == "__main__":
    test_parser()

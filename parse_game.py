"""
Main script to parse scraped Terraforming Mars games
"""
import os
import json
import logging
from src.parser import TMGameParser

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def parse_all_games():
    """Parse all scraped games in the raw data directory"""
    
    parser = TMGameParser()
    raw_dir = 'data/raw'
    parsed_dir = 'data/parsed'
    
    # Create output directory
    os.makedirs(parsed_dir, exist_ok=True)
    
    if not os.path.exists(raw_dir):
        print(f"❌ Raw data directory not found: {raw_dir}")
        return
    
    # Find all HTML files
    html_files = [f for f in os.listdir(raw_dir) if f.endswith('.html')]
    
    if not html_files:
        print(f"❌ No HTML files found in {raw_dir}")
        return
    
    print(f"🔍 Found {len(html_files)} HTML files to parse")
    
    parsed_games = []
    
    for html_file in html_files:
        print(f"\n📖 Parsing {html_file}...")
        
        # Extract replay ID from filename
        replay_id = html_file.replace('replay_', '').replace('.html', '')
        
        # Load HTML content
        html_path = os.path.join(raw_dir, html_file)
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Parse the game
        try:
            game = parser.parse_game_from_html(html_content, replay_id)
            
            # Export individual game files
            json_file = os.path.join(parsed_dir, f'game_{replay_id}.json')
            csv_file = os.path.join(parsed_dir, f'moves_{replay_id}.csv')
            
            parser.export_to_json(game, json_file)
            parser.export_moves_to_csv(game, csv_file)
            
            # Add to summary
            parsed_games.append({
                'replay_id': game.replay_id,
                'players': game.players,
                'corporations': game.corporations,
                'total_moves': len(game.moves),
                'final_temperature': game.final_state.temperature,
                'final_oxygen': game.final_state.oxygen,
                'final_oceans': game.final_state.oceans,
                'generations': game.final_state.generation,
                'cards_played': len([m for m in game.moves if m.action_type == 'play_card']),
                'tiles_placed': len([m for m in game.moves if m.tile_place]),
                'game_duration': game.moves[-1].timestamp if game.moves else 'Unknown'
            })
            
            print(f"✅ Successfully parsed {replay_id}")
            
        except Exception as e:
            print(f"❌ Error parsing {html_file}: {e}")
            continue
    
    # Create summary file
    summary_file = os.path.join(parsed_dir, 'parsing_summary.json')
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            'total_games_parsed': len(parsed_games),
            'parsing_timestamp': parser.parse_game_from_html.__defaults__,
            'games': parsed_games
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n🎉 Parsing complete!")
    print(f"   Games parsed: {len(parsed_games)}")
    print(f"   Summary saved to: {summary_file}")
    
    # Show some statistics
    if parsed_games:
        avg_moves = sum(g['total_moves'] for g in parsed_games) / len(parsed_games)
        avg_cards = sum(g['cards_played'] for g in parsed_games) / len(parsed_games)
        avg_generations = sum(g['generations'] for g in parsed_games) / len(parsed_games)
        
        print(f"\n📊 Statistics:")
        print(f"   Average moves per game: {avg_moves:.1f}")
        print(f"   Average cards played: {avg_cards:.1f}")
        print(f"   Average generations: {avg_generations:.1f}")
        
        # Final terraforming states
        final_temps = [g['final_temperature'] for g in parsed_games]
        final_oxygen = [g['final_oxygen'] for g in parsed_games]
        final_oceans = [g['final_oceans'] for g in parsed_games]
        
        print(f"   Temperature range: {min(final_temps)}°C to {max(final_temps)}°C")
        print(f"   Oxygen range: {min(final_oxygen)}% to {max(final_oxygen)}%")
        print(f"   Oceans range: {min(final_oceans)} to {max(final_oceans)}")

def analyze_parsed_data():
    """Analyze the parsed game data"""
    
    parsed_dir = 'data/parsed'
    summary_file = os.path.join(parsed_dir, 'parsing_summary.json')
    
    if not os.path.exists(summary_file):
        print(f"❌ No summary file found. Run parse_all_games() first.")
        return
    
    with open(summary_file, 'r', encoding='utf-8') as f:
        summary = json.load(f)
    
    games = summary['games']
    
    print(f"📊 Analysis of {len(games)} parsed games:\n")
    
    # Corporation analysis
    corp_counts = {}
    for game in games:
        for player, corp in game['corporations'].items():
            corp_counts[corp] = corp_counts.get(corp, 0) + 1
    
    print("🏢 Corporation Usage:")
    for corp, count in sorted(corp_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"   {corp}: {count} times")
    
    # Game completion analysis
    completed_games = [g for g in games if g['final_oxygen'] == 14 and g['final_temperature'] >= 8 and g['final_oceans'] == 9]
    print(f"\n🎯 Terraforming Completion:")
    print(f"   Fully terraformed games: {len(completed_games)}/{len(games)} ({len(completed_games)/len(games)*100:.1f}%)")
    
    # Strategy analysis
    avg_cards = sum(g['cards_played'] for g in games) / len(games)
    avg_generations = sum(g['generations'] for g in games) / len(games)
    
    print(f"\n🎮 Strategy Patterns:")
    engine_games = [g for g in games if g['cards_played'] > avg_cards * 1.2]
    rush_games = [g for g in games if g['generations'] < avg_generations * 0.8]
    
    print(f"   Engine-heavy games (>20% more cards): {len(engine_games)}")
    print(f"   Rush games (<20% generations): {len(rush_games)}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'analyze':
        analyze_parsed_data()
    else:
        parse_all_games()

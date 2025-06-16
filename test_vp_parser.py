#!/usr/bin/env python3
"""
Test script for the enhanced VP tracking parser
"""
import logging
from src.parser import TMGameParser

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_vp_parser():
    """Test the enhanced parser with VP tracking"""
    parser = TMGameParser()
    
    # Read the existing HTML file
    html_file = "data/raw/replay_250604-1037.html"
    
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        logger.info(f"Loaded HTML file: {len(html_content)} characters")
        
        # Parse the game
        game = parser.parse_game_from_html(html_content, "250604-1037")
        
        # Print results
        print(f"\n=== GAME ANALYSIS ===")
        print(f"Replay ID: {game.replay_id}")
        print(f"Players: {game.players}")
        print(f"Corporations: {game.corporations}")
        print(f"Total moves: {len(game.moves)}")
        print(f"Final state: Gen {game.final_state.generation}, Temp {game.final_state.temperature}°C, O2 {game.final_state.oxygen}%, Oceans {game.final_state.oceans}")
        
        print(f"\n=== MILESTONES ===")
        for name, milestone in game.final_state.milestones.items():
            print(f"- {name}: {milestone.vp_value} VP (claimed by: {milestone.claimed_by})")
        
        print(f"\n=== AWARDS ===")
        for name, award in game.final_state.awards.items():
            print(f"- {name}: {award.vp_value} VP (funded by: {award.funded_by})")
        
        print(f"\n=== VICTORY POINTS ===")
        for player, vp in game.final_state.player_vp.items():
            print(f"\n{player} ({game.corporations.get(player, 'Unknown')}):")
            print(f"  TR Rating: {vp.tr_rating}")
            print(f"  Milestones: {sum(vp.milestones.values())} VP {vp.milestones}")
            print(f"  Awards: {sum(vp.awards.values())} VP {vp.awards}")
            print(f"  Cards: {sum(vp.cards.values())} VP {vp.cards}")
            print(f"  Board Tiles: {vp.board_tiles} VP")
            print(f"  TOTAL: {vp.total} VP")
        
        # Export enhanced data
        parser.export_to_json(game, "data/parsed/game_250604-1037_enhanced.json")
        parser.export_moves_to_csv(game, "data/parsed/moves_250604-1037_enhanced.csv")
        parser.export_vp_breakdown_to_csv(game, "data/parsed/vp_breakdown_250604-1037.csv")
        
        print(f"\n=== EXPORTS ===")
        print("Enhanced JSON: data/parsed/game_250604-1037_enhanced.json")
        print("Enhanced CSV: data/parsed/moves_250604-1037_enhanced.csv")
        print("VP Breakdown: data/parsed/vp_breakdown_250604-1037.csv")
        
    except FileNotFoundError:
        logger.error(f"HTML file not found: {html_file}")
    except Exception as e:
        logger.error(f"Error parsing game: {e}")
        raise

if __name__ == "__main__":
    test_vp_parser()

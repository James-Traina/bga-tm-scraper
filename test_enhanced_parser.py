#!/usr/bin/env python3
"""
Test script for the enhanced VP tracking parser with progression analysis
"""
import logging
from src.parser import TMGameParser

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_enhanced_parser():
    """Test the enhanced parser with complete VP tracking and progression"""
    parser = TMGameParser()
    
    # Read the existing HTML file
    html_file = "data/raw/replay_250604-1037.html"
    
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        logger.info(f"Loaded HTML file: {len(html_content)} characters")
        
        # Parse the game with enhanced VP tracking
        game = parser.parse_game_from_html(html_content, "250604-1037")
        
        # Print comprehensive results
        print(f"\n=== ENHANCED GAME ANALYSIS ===")
        print(f"Replay ID: {game.replay_id}")
        print(f"Players: {game.players}")
        print(f"Corporations: {game.corporations}")
        print(f"Total moves: {len(game.moves)}")
        print(f"Final state: Gen {game.final_state.generation}, Temp {game.final_state.temperature}°C, O2 {game.final_state.oxygen}%, Oceans {game.final_state.oceans}")
        
        print(f"\n=== ACCURATE VICTORY POINTS (from game data) ===")
        for player, vp in game.final_state.player_vp.items():
            corp = game.corporations.get(player, 'Unknown')
            print(f"\n{player} ({corp}):")
            print(f"  TR Rating: {vp.tr_rating} VP")
            print(f"  Milestones: {sum(vp.milestones.values())} VP {vp.milestones}")
            print(f"  Awards: {sum(vp.awards.values())} VP {vp.awards}")
            print(f"  Cards: {sum(vp.cards.values())} VP {vp.cards}")
            print(f"  Board Tiles: {vp.board_tiles} VP")
            print(f"  TOTAL: {vp.total} VP")
        
        # Export all data formats
        parser.export_to_json(game, "data/parsed/game_250604-1037_final.json")
        parser.export_moves_to_csv(game, "data/parsed/moves_250604-1037_final.csv")
        parser.export_vp_breakdown_to_csv(game, "data/parsed/vp_breakdown_250604-1037_final.csv")
        
        # Export VP progression
        parser.export_vp_progression_to_csv(game, html_content, "data/parsed/vp_progression_250604-1037_final.csv")
        
        # Analyze VP progression
        vp_progression = parser.extract_vp_progression(html_content)
        
        print(f"\n=== VP PROGRESSION ANALYSIS ===")
        print(f"Total VP data points: {len(vp_progression)}")
        
        if vp_progression:
            start_vp = vp_progression[0]['combined_total']
            end_vp = vp_progression[-1]['combined_total']
            print(f"VP progression: {start_vp} -> {end_vp} (+{end_vp - start_vp} total)")
            
            # Show key progression milestones
            print(f"\n=== KEY VP MILESTONES ===")
            milestone_thresholds = [50, 75, 100, 125]
            
            for threshold in milestone_thresholds:
                for entry in vp_progression:
                    if entry['combined_total'] >= threshold:
                        print(f"Combined VP reached {threshold}: Move {entry['move_index']}")
                        print(f"  Player 1: {entry['player_86296239_total']} VP")
                        print(f"  Player 2: {entry['player_97116430_total']} VP")
                        break
            
            # Analyze award flips
            print(f"\n=== AWARD LEADERSHIP ANALYSIS ===")
            award_leaders = {}
            
            for entry in vp_progression:
                vp_data = entry['vp_data']
                
                for player_id, player_data in vp_data.items():
                    details = player_data.get('details', {})
                    awards = details.get('awards', {})
                    
                    for award_id, award_data in awards.items():
                        place = award_data.get('place', 0)
                        if place == 1:  # First place
                            if award_id not in award_leaders:
                                award_leaders[award_id] = []
                            
                            # Check if leadership changed
                            if not award_leaders[award_id] or award_leaders[award_id][-1]['player'] != player_id:
                                award_leaders[award_id].append({
                                    'move': entry['move_index'],
                                    'player': player_id,
                                    'counter': award_data.get('counter', 0)
                                })
            
            for award_id, leadership_history in award_leaders.items():
                print(f"\nAward {award_id} leadership changes:")
                for i, leader in enumerate(leadership_history):
                    if i == 0:
                        print(f"  Move {leader['move']}: Player {leader['player']} takes the lead (counter: {leader['counter']})")
                    else:
                        prev_leader = leadership_history[i-1]['player']
                        print(f"  Move {leader['move']}: Leadership flips from {prev_leader} to {leader['player']} (counter: {leader['counter']})")
        
        print(f"\n=== EXPORTS ===")
        print("Final Game JSON: data/parsed/game_250604-1037_final.json")
        print("Final Moves CSV: data/parsed/moves_250604-1037_final.csv")
        print("Final VP Breakdown: data/parsed/vp_breakdown_250604-1037_final.csv")
        print("VP Progression CSV: data/parsed/vp_progression_250604-1037_final.csv")
        
        return game, vp_progression
        
    except FileNotFoundError:
        logger.error(f"HTML file not found: {html_file}")
        return None, None
    except Exception as e:
        logger.error(f"Error parsing game: {e}")
        raise

if __name__ == "__main__":
    game, progression = test_enhanced_parser()
    
    if game and progression:
        print(f"\n=== SUMMARY ===")
        print(f"Successfully parsed game with {len(game.moves)} moves and {len(progression)} VP data points")
        print(f"Final scores:")
        for player, vp in game.final_state.player_vp.items():
            print(f"  {player}: {vp.total} VP")
        
        # Determine winner
        winner = max(game.final_state.player_vp.items(), key=lambda x: x[1].total)
        print(f"Winner: {winner[0]} with {winner[1].total} VP")

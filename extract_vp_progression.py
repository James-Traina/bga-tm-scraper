#!/usr/bin/env python3
"""
Extract VP progression throughout the game from raw HTML
"""
import re
import json
from typing import List, Dict, Any

def extract_vp_progression():
    """Extract VP data progression throughout the entire game"""
    html_file = "data/raw/replay_250604-1037.html"
    
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all VP data structures throughout the game
    # Pattern to match any VP data with both players
    pattern = r'"data":\{("86296239":\{.*?"total":(\d+).*?\}.*?"97116430":\{.*?"total":(\d+).*?\})\}'
    
    matches = re.findall(pattern, content, re.DOTALL)
    print(f"Found {len(matches)} VP data points throughout the game")
    
    vp_progression = []
    
    for i, (match_data, total1, total2) in enumerate(matches):
        try:
            # Add braces to make it valid JSON
            json_str = "{" + match_data + "}"
            
            # Try to fix JSON structure if needed
            brace_count = match_data.count('{') - match_data.count('}')
            if brace_count > 0:
                json_str = "{" + match_data + '}' * brace_count + "}"
            
            vp_data = json.loads(json_str)
            
            # Add metadata
            vp_entry = {
                'move_index': i,
                'combined_total': int(total1) + int(total2),
                'player_86296239_total': int(total1),
                'player_97116430_total': int(total2),
                'vp_data': vp_data
            }
            
            vp_progression.append(vp_entry)
            
        except json.JSONDecodeError:
            # Skip malformed entries
            continue
    
    print(f"Successfully parsed {len(vp_progression)} VP data points")
    
    if vp_progression:
        # Analyze progression
        print(f"\n=== VP PROGRESSION ANALYSIS ===")
        print(f"Game start: {vp_progression[0]['combined_total']} total VP")
        print(f"Game end: {vp_progression[-1]['combined_total']} total VP")
        
        # Show key milestones
        print(f"\n=== KEY VP MILESTONES ===")
        prev_total = 0
        generation_markers = []
        
        for entry in vp_progression:
            current_total = entry['combined_total']
            if current_total > prev_total + 10:  # Significant VP jump
                print(f"Move {entry['move_index']}: Combined VP jumped to {current_total}")
                print(f"  Player 86296239: {entry['player_86296239_total']} VP")
                print(f"  Player 97116430: {entry['player_97116430_total']} VP")
            prev_total = current_total
        
        # Extract generation boundaries (when VP totals reset or jump significantly)
        generations = []
        current_gen = []
        
        for i, entry in enumerate(vp_progression):
            current_gen.append(entry)
            
            # Check if this might be end of generation (next entry has lower or reset VP)
            if i < len(vp_progression) - 1:
                next_entry = vp_progression[i + 1]
                # If next total is much lower, might be generation boundary
                if (next_entry['combined_total'] < entry['combined_total'] - 5 or
                    (i > 0 and entry['combined_total'] > vp_progression[i-1]['combined_total'] + 20)):
                    generations.append(current_gen)
                    current_gen = []
        
        if current_gen:  # Add final generation
            generations.append(current_gen)
        
        print(f"\n=== GENERATION ANALYSIS ===")
        print(f"Detected {len(generations)} potential generations")
        
        for gen_num, gen_data in enumerate(generations[:5]):  # Show first 5 generations
            if gen_data:
                start_vp = gen_data[0]['combined_total']
                end_vp = gen_data[-1]['combined_total']
                print(f"Generation {gen_num + 1}: {start_vp} -> {end_vp} VP ({len(gen_data)} moves)")
        
        # Save detailed progression data
        output_data = {
            'metadata': {
                'total_moves': len(vp_progression),
                'total_generations': len(generations),
                'final_combined_vp': vp_progression[-1]['combined_total'] if vp_progression else 0
            },
            'progression': vp_progression,
            'generations': generations
        }
        
        with open('data/parsed/vp_progression.json', 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"\nSaved VP progression data to: data/parsed/vp_progression.json")
        
        # Create simplified CSV for analysis
        create_vp_progression_csv(vp_progression)
        
        return output_data
    
    return None

def create_vp_progression_csv(vp_progression: List[Dict[str, Any]]):
    """Create a CSV file with VP progression for easy analysis"""
    import csv
    
    with open('data/parsed/vp_progression.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow([
            'move_index', 'combined_total',
            'player_86296239_total', 'player_86296239_tr', 'player_86296239_awards', 'player_86296239_milestones',
            'player_86296239_cities', 'player_86296239_greeneries', 'player_86296239_cards',
            'player_97116430_total', 'player_97116430_tr', 'player_97116430_awards', 'player_97116430_milestones',
            'player_97116430_cities', 'player_97116430_greeneries', 'player_97116430_cards'
        ])
        
        # Data rows
        for entry in vp_progression:
            vp_data = entry['vp_data']
            
            # Player 86296239 data
            p1_data = vp_data.get('86296239', {})
            p1_details = p1_data.get('total_details', {})
            
            # Player 97116430 data
            p2_data = vp_data.get('97116430', {})
            p2_details = p2_data.get('total_details', {})
            
            writer.writerow([
                entry['move_index'],
                entry['combined_total'],
                p1_data.get('total', 0),
                p1_details.get('tr', 0),
                p1_details.get('awards', 0),
                p1_details.get('milestones', 0),
                p1_details.get('cities', 0),
                p1_details.get('greeneries', 0),
                p1_details.get('cards', 0),
                p2_data.get('total', 0),
                p2_details.get('tr', 0),
                p2_details.get('awards', 0),
                p2_details.get('milestones', 0),
                p2_details.get('cities', 0),
                p2_details.get('greeneries', 0),
                p2_details.get('cards', 0)
            ])
    
    print(f"Created VP progression CSV: data/parsed/vp_progression.csv")

def analyze_award_flips(vp_progression: List[Dict[str, Any]]):
    """Analyze award position changes throughout the game"""
    print(f"\n=== AWARD FLIP ANALYSIS ===")
    
    award_history = {}
    
    for entry in vp_progression:
        vp_data = entry['vp_data']
        move_index = entry['move_index']
        
        for player_id, player_data in vp_data.items():
            details = player_data.get('details', {})
            awards = details.get('awards', {})
            
            for award_id, award_data in awards.items():
                place = award_data.get('place', 0)
                counter = award_data.get('counter', 0)
                
                if award_id not in award_history:
                    award_history[award_id] = []
                
                award_history[award_id].append({
                    'move': move_index,
                    'player': player_id,
                    'place': place,
                    'counter': counter
                })
    
    # Analyze flips
    for award_id, history in award_history.items():
        print(f"\nAward {award_id} progression:")
        prev_leader = None
        
        for entry in history:
            if entry['place'] == 1:  # First place
                if prev_leader and prev_leader != entry['player']:
                    print(f"  Move {entry['move']}: Leadership flipped from {prev_leader} to {entry['player']}")
                elif not prev_leader:
                    print(f"  Move {entry['move']}: {entry['player']} takes the lead")
                prev_leader = entry['player']

if __name__ == "__main__":
    progression_data = extract_vp_progression()
    if progression_data:
        analyze_award_flips(progression_data['progression'])

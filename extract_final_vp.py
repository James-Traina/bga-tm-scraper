#!/usr/bin/env python3
"""
Extract final VP data from raw HTML
"""
import re
import json

def extract_final_vp():
    """Extract the final VP data from the HTML file"""
    html_file = "data/raw/replay_250604-1037.html"
    
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Look for the complete VP data structure with both players
    # Pattern to find JSON with both player IDs and their complete data
    pattern = r'"data":\{("86296239":\{[^}]*"total":\d+.*?"97116430":\{[^}]*"total":\d+.*?)\}'
    
    matches = re.findall(pattern, content, re.DOTALL)
    print(f"Found {len(matches)} complete VP data structures")
    
    if matches:
        # Get the last match (final game state)
        final_match = matches[-1]
        print(f"\nFinal VP data structure:")
        print(f"Length: {len(final_match)} characters")
        
        # Try to parse as JSON
        try:
            # Add braces to make it valid JSON
            json_str = "{" + final_match + "}"
            vp_data = json.loads(json_str)
            
            print(f"\n=== PARSED FINAL VP DATA ===")
            print(json.dumps(vp_data, indent=2))
            
            # Extract and display summary
            print(f"\n=== VP SUMMARY ===")
            for player_id, data in vp_data.items():
                total = data.get('total', 0)
                details = data.get('total_details', {})
                print(f"\nPlayer {player_id}: {total} VP")
                print(f"  TR: {details.get('tr', 0)}")
                print(f"  Awards: {details.get('awards', 0)}")
                print(f"  Milestones: {details.get('milestones', 0)}")
                print(f"  Cities: {details.get('cities', 0)}")
                print(f"  Greeneries: {details.get('greeneries', 0)}")
                print(f"  Cards: {details.get('cards', 0)}")
                
                # Show detailed breakdown
                if 'details' in data:
                    print(f"  Detailed breakdown:")
                    for category, items in data['details'].items():
                        if items:
                            print(f"    {category}: {len(items)} items")
                            for item_id, item_data in items.items():
                                vp = item_data.get('vp', 0)
                                if vp != 0:
                                    print(f"      {item_id}: {vp} VP")
            
            return vp_data
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Raw data (first 1000 chars): {final_match[:1000]}")
    
    # Alternative: look for individual final states
    print(f"\n=== Looking for individual final states ===")
    
    # Find all VP data and get the highest totals
    all_vp_pattern = r'"data":\{"(\d+)":\{"total":(\d+).*?\}\}'
    all_matches = re.findall(all_vp_pattern, content, re.DOTALL)
    
    # Group by player and find max total
    player_max = {}
    for player_id, total in all_matches:
        total = int(total)
        if player_id not in player_max or total > player_max[player_id]:
            player_max[player_id] = total
    
    print(f"Maximum VP found per player:")
    for player_id, max_vp in player_max.items():
        print(f"  Player {player_id}: {max_vp} VP")

if __name__ == "__main__":
    extract_final_vp()

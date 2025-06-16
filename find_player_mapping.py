#!/usr/bin/env python3
"""
Find the mapping between player names and IDs in the HTML
"""
import re
import json

def find_player_mapping():
    """Find how player names map to player IDs"""
    html_file = "data/raw/replay_250604-1037.html"
    
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # First, find all player IDs in VP data
    vp_pattern = r'"data":\{("(\d+)":\{.*?"total":\d+.*?\})\}'
    vp_matches = re.findall(vp_pattern, content, re.DOTALL)
    
    player_ids = set()
    for match_data, player_id in vp_matches:
        player_ids.add(player_id)
    
    print(f"Found player IDs in VP data: {sorted(player_ids)}")
    
    # Look for player names in various contexts
    player_names = ['petersenhauke', 'StrandedKnight']
    
    print(f"\n=== Searching for player name contexts ===")
    
    for name in player_names:
        print(f"\nPlayer: {name}")
        
        # Search for various patterns that might link names to IDs
        patterns = [
            rf'{name}.*?(\d{{8,}})',  # name followed by long number
            rf'(\d{{8,}}).*?{name}',  # long number followed by name
            rf'player.*?{name}.*?(\d{{8,}})',  # player context
            rf'(\d{{8,}}).*?player.*?{name}',  # reverse
            rf'{name}.*?id.*?(\d{{8,}})',  # name with id
            rf'id.*?(\d{{8,}}).*?{name}',  # id with name
        ]
        
        for i, pattern in enumerate(patterns):
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                print(f"  Pattern {i+1}: Found {len(matches)} matches")
                for match in matches[:3]:  # Show first 3
                    print(f"    {match}")
    
    # Look for color-based mapping (common in BGA)
    print(f"\n=== Color-based mapping ===")
    color_patterns = [
        r'player.*?color.*?(\w+).*?(petersenhauke|StrandedKnight)',
        r'(petersenhauke|StrandedKnight).*?color.*?(\w+)',
        r'#([a-fA-F0-9]{6}).*?(petersenhauke|StrandedKnight)',
        r'(petersenhauke|StrandedKnight).*?#([a-fA-F0-9]{6})',
    ]
    
    for pattern in color_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            print(f"Color pattern matches: {matches[:5]}")
    
    # Look for player board structures
    print(f"\n=== Player board structures ===")
    board_patterns = [
        r'player_board.*?(\d{8,})',
        r'(\d{8,}).*?player_board',
        r'board.*?player.*?(\d{8,})',
    ]
    
    for pattern in board_patterns:
        matches = re.findall(pattern, content)
        if matches:
            print(f"Board pattern: {len(matches)} matches - {matches[:5]}")
    
    # Try to find the actual VP data structure and extract all player IDs
    print(f"\n=== Complete VP data structure analysis ===")
    
    # Find the most complete VP data
    complete_pattern = r'"data":\{((?:"(\d+)":\{[^}]*"total":\d+[^}]*\}[,\s]*)+)\}'
    complete_matches = re.findall(complete_pattern, content, re.DOTALL)
    
    if complete_matches:
        print(f"Found {len(complete_matches)} complete VP structures")
        
        # Get the last one (final state)
        final_vp_data = complete_matches[-1][0]
        print(f"Final VP data structure (first 500 chars):")
        print(final_vp_data[:500])
        
        # Extract all player IDs from this structure
        id_pattern = r'"(\d+)":\{'
        all_ids = re.findall(id_pattern, final_vp_data)
        print(f"All player IDs in final VP data: {all_ids}")
        
        # Try to parse the complete structure
        try:
            json_str = "{" + final_vp_data + "}"
            # Fix JSON if needed
            brace_count = final_vp_data.count('{') - final_vp_data.count('}')
            if brace_count > 0:
                json_str = "{" + final_vp_data + '}' * brace_count + "}"
            
            vp_data = json.loads(json_str)
            print(f"\nParsed VP data for {len(vp_data)} players:")
            for player_id, data in vp_data.items():
                total = data.get('total', 0)
                print(f"  Player {player_id}: {total} VP")
                
        except json.JSONDecodeError as e:
            print(f"Failed to parse VP JSON: {e}")

if __name__ == "__main__":
    find_player_mapping()

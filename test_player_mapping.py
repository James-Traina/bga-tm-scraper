#!/usr/bin/env python3
"""
Test the player ID mapping extraction
"""
import re
from src.parser import TMGameParser

def test_player_mapping():
    """Test extracting player names and mapping them to IDs"""
    parser = TMGameParser()
    
    # Read the HTML file
    html_file = "data/raw/replay_250604-1037.html"
    
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    print("=== TESTING PLAYER ID MAPPING ===")
    
    # First, extract players using the parser
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    players = parser._extract_players(soup)
    print(f"Extracted players: {players}")
    
    # Extract VP data
    vp_data = parser._extract_vp_data_from_html(html_content)
    print(f"VP data player IDs: {list(vp_data.keys())}")
    
    for player_id, data in vp_data.items():
        total = data.get('total', 0)
        print(f"  Player {player_id}: {total} VP")
    
    # Test the HTML-based mapping
    print(f"\n=== TESTING HTML-BASED MAPPING ===")
    html_mapping = parser._extract_player_id_mapping_from_html(html_content, players)
    print(f"HTML-based mapping: {html_mapping}")
    
    # Test the fallback VP-based mapping
    print(f"\n=== TESTING VP-BASED MAPPING ===")
    vp_mapping = parser._map_players_to_ids(players, vp_data)
    print(f"VP-based mapping: {vp_mapping}")
    
    # Show which player should have which VP total
    print(f"\n=== CORRECT MAPPING VERIFICATION ===")
    print("Based on VP totals:")
    player_ids_by_vp = []
    for player_id, data in vp_data.items():
        total_vp = data.get('total', 0)
        player_ids_by_vp.append((player_id, total_vp))
    
    player_ids_by_vp.sort(key=lambda x: x[1], reverse=True)
    
    for i, (player_id, vp_total) in enumerate(player_ids_by_vp):
        print(f"  Rank {i+1}: Player ID {player_id} with {vp_total} VP")
    
    print(f"\nCorrect mapping verification:")
    print("The HTML-based mapping should be used as the ground truth.")
    print("The VP-based mapping should match the HTML-based mapping when both work.")
    
    print(f"\nActual VP totals by player ID:")
    for player_id, vp_total in player_ids_by_vp:
        print(f"  Player ID {player_id}: {vp_total} VP")
    
    # Verify mappings match
    print(f"\nMapping consistency check:")
    if html_mapping and vp_mapping:
        mappings_match = True
        for player in players:
            html_id = html_mapping.get(player)
            vp_id = vp_mapping.get(player)
            if html_id != vp_id:
                mappings_match = False
                print(f"  MISMATCH: {player} -> HTML: {html_id}, VP: {vp_id}")
            else:
                print(f"  MATCH: {player} -> {html_id}")
        
        if mappings_match:
            print("✅ All mappings are consistent!")
        else:
            print("❌ Mappings are inconsistent!")
    else:
        print("Cannot verify consistency - one or both mappings failed")

if __name__ == "__main__":
    test_player_mapping()

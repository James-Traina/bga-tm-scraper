"""
Test script to debug ELO extraction from scraped table HTML
"""
import os
from src.parser import Parser
from bs4 import BeautifulSoup
import re

def test_elo_extraction():
    """Test ELO extraction from the scraped table HTML"""
    
    # Load the table HTML file
    table_html_path = "data/raw/table_688769496.html"
    
    if not os.path.exists(table_html_path):
        print(f"❌ Table HTML file not found: {table_html_path}")
        return
    
    print(f"📁 Loading table HTML from: {table_html_path}")
    
    with open(table_html_path, 'r', encoding='utf-8') as f:
        table_html = f.read()
    
    print(f"📊 HTML file size: {len(table_html):,} characters")
    
    # Initialize parser
    parser = Parser()
    
    # Test ELO extraction
    print("\n🔍 Testing ELO data extraction...")
    elo_data = parser.parse_elo_data(table_html)
    
    print(f"\n📈 ELO data found for {len(elo_data)} players:")
    for player_name, elo in elo_data.items():
        print(f"  {player_name}:")
        print(f"    Arena Points: {elo.arena_points}")
        print(f"    Arena Points Change: {elo.arena_points_change}")
        print(f"    Game Rank: {elo.game_rank}")
        print(f"    Game Rank Change: {elo.game_rank_change}")
    
    # Let's also manually examine the HTML structure
    print("\n🔍 Manual HTML analysis...")
    soup = BeautifulSoup(table_html, 'html.parser')
    
    # Find all player names
    player_names = []
    player_elements = soup.find_all('span', class_='playername')
    for elem in player_elements:
        name = elem.get_text().strip()
        if name and name not in ['Visitor'] and name not in player_names:
            player_names.append(name)
    
    print(f"👥 Players found in HTML: {player_names}")
    
    # Look for ELO-related sections
    print("\n🎯 Searching for ELO patterns...")
    
    # Look for winpoints sections
    winpoints_sections = soup.find_all('div', class_='winpoints')
    print(f"💰 Found {len(winpoints_sections)} winpoints sections")
    
    for i, section in enumerate(winpoints_sections):
        print(f"  Section {i+1}: {section.get_text().strip()}")
        # Look for associated player
        parent = section.parent
        while parent and parent.name != 'body':
            player_elem = parent.find('span', class_='playername')
            if player_elem:
                player_name = player_elem.get_text().strip()
                if player_name not in ['Visitor']:
                    print(f"    Associated with player: {player_name}")
                break
            parent = parent.parent
    
    # Look for rankdetails sections
    rankdetails_sections = soup.find_all('span', class_='rankdetails')
    print(f"🏆 Found {len(rankdetails_sections)} rankdetails sections")
    
    # Look for newrank sections
    newrank_sections = soup.find_all('div', class_='newrank')
    print(f"📊 Found {len(newrank_sections)} newrank sections")
    
    for i, section in enumerate(newrank_sections):
        print(f"  Section {i+1}: {section.get_text().strip()}")
    
    # Look for specific patterns we saw earlier
    print("\n🔍 Searching for specific ELO values...")
    
    # Search for the values we know should be there
    expected_values = ['+24', '-24', '+14', '-14', '1754', '1769']
    for value in expected_values:
        if value in table_html:
            print(f"✅ Found '{value}' in HTML")
            # Find context around this value
            index = table_html.find(value)
            start = max(0, index - 200)
            end = min(len(table_html), index + 200)
            context = table_html[start:end]
            print(f"   Context: ...{context}...")
        else:
            print(f"❌ '{value}' not found in HTML")

def debug_specific_player_section():
    """Debug specific player sections in detail"""
    
    table_html_path = "data/raw/table_688769496.html"
    
    with open(table_html_path, 'r', encoding='utf-8') as f:
        table_html = f.read()
    
    soup = BeautifulSoup(table_html, 'html.parser')
    
    print("\n🔍 Detailed player section analysis...")
    
    # Find score entries (these seem to contain the player data)
    score_entries = soup.find_all('div', class_='score-entry')
    print(f"📊 Found {len(score_entries)} score entries")
    
    for i, entry in enumerate(score_entries):
        print(f"\n--- Score Entry {i+1} ---")
        
        # Find player name
        player_elem = entry.find('a', class_='playername')
        if player_elem:
            player_name = player_elem.get_text().strip()
            player_id = player_elem.get('href', '').split('id=')[-1] if 'id=' in player_elem.get('href', '') else 'unknown'
            print(f"👤 Player: {player_name} (ID: {player_id})")
        
        # Find all winpoints in this entry
        winpoints = entry.find_all('div', class_='winpoints')
        for j, wp in enumerate(winpoints):
            print(f"💰 Winpoints {j+1}: {wp.get_text().strip()}")
        
        # Find all newrank in this entry
        newranks = entry.find_all('div', class_='newrank')
        for j, nr in enumerate(newranks):
            print(f"🏆 Newrank {j+1}: {nr.get_text().strip()}")
        
        # Look for specific IDs that might contain ELO data
        for element in entry.find_all(attrs={'id': True}):
            element_id = element.get('id')
            if any(keyword in element_id for keyword in ['winpoints', 'newrank', 'arena']):
                print(f"🎯 ELO element: {element_id} = {element.get_text().strip()}")

if __name__ == "__main__":
    print("=== ELO Extraction Debug Test ===\n")
    test_elo_extraction()
    debug_specific_player_section()

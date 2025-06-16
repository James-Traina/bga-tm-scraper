"""
Debug script to examine HTML structure for parser improvement
"""
import re
from bs4 import BeautifulSoup

def analyze_html_structure():
    """Analyze the HTML structure to understand resource patterns"""
    
    with open('data/raw/replay_250604-1037.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find a few sample moves with resource changes
    move_divs = soup.find_all('div', class_='replaylogs_move')
    
    print("🔍 Analyzing HTML structure for resource extraction...\n")
    
    # Look at moves that should have parameter changes
    for i, move_div in enumerate(move_divs[4:10]):  # Moves 5-10 should have some parameter changes
        move_info = move_div.find('div', class_='smalltext')
        if move_info:
            move_text = move_info.get_text()
            move_match = re.search(r'Move (\d+)', move_text)
            if move_match:
                move_number = int(move_match.group(1))
                
                print(f"=== Move {move_number} ===")
                
                log_entries = move_div.find_all('div', class_='gamelogreview')
                for j, entry in enumerate(log_entries):
                    print(f"Entry {j+1}:")
                    print(f"  Text: {entry.get_text()}")
                    print(f"  HTML: {str(entry)[:200]}...")
                    
                    # Look for specific patterns
                    if 'increases' in entry.get_text() and 'step' in entry.get_text():
                        print(f"  *** PARAMETER CHANGE DETECTED ***")
                    
                    if any(word in entry.get_text() for word in ['gains', 'pays']):
                        print(f"  *** RESOURCE CHANGE DETECTED ***")
                    
                    print()
                
                print("-" * 50)
                
                if move_number >= 10:  # Just analyze first few moves
                    break

def test_regex_patterns():
    """Test regex patterns on actual HTML"""
    
    with open('data/raw/replay_250604-1037.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Sample text that should contain parameter changes
    sample_texts = [
        'StrandedKnight increases <div class="token_img tracker_w" title="Oceans"></div> by 1 step/s to a value of 1',
        'StrandedKnight increases <div class="token_img tracker_o" title="Oxygen Level"></div> by 1 step/s to a value of 1',
        'StrandedKnight increases <div class="token_img tracker_t" title="Temperature"></div> by 2 step/s to a value of -26',
    ]
    
    print("\n🧪 Testing regex patterns...\n")
    
    # Test parameter change patterns
    for text in sample_texts:
        print(f"Testing: {text}")
        
        # Temperature
        temp_match = re.search(r'increases.*Temperature.*by (\d+) step.*to a value of (-?\d+)', text)
        if temp_match:
            print(f"  Temperature: {temp_match.group(2)}")
        
        # Oxygen
        oxygen_match = re.search(r'increases.*Oxygen Level.*by (\d+) step.*to a value of (\d+)', text)
        if oxygen_match:
            print(f"  Oxygen: {oxygen_match.group(2)}")
        
        # Oceans
        ocean_match = re.search(r'increases.*Oceans.*by (\d+) step.*to a value of (\d+)', text)
        if ocean_match:
            print(f"  Oceans: {ocean_match.group(2)}")
        
        print()

if __name__ == "__main__":
    analyze_html_structure()
    test_regex_patterns()

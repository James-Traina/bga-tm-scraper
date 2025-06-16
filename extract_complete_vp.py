#!/usr/bin/env python3
"""
Extract complete final VP data from raw HTML
"""
import re
import json

def extract_complete_vp():
    """Extract the complete final VP data from the HTML file"""
    html_file = "data/raw/replay_250604-1037.html"
    
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Look for the most complete VP data structure
    # Find all instances and get the one with highest totals
    pattern = r'"data":\{("86296239":\{.*?"total":(\d+).*?\}.*?"97116430":\{.*?"total":(\d+).*?\})\}'
    
    matches = re.findall(pattern, content, re.DOTALL)
    print(f"Found {len(matches)} VP data structures with both players")
    
    if matches:
        # Find the match with highest combined total
        best_match = None
        best_total = 0
        
        for match_data, total1, total2 in matches:
            combined_total = int(total1) + int(total2)
            if combined_total > best_total:
                best_total = combined_total
                best_match = match_data
        
        print(f"Best match has combined total: {best_total} VP")
        
        if best_match:
            # Try to parse as JSON
            try:
                # Add braces to make it valid JSON
                json_str = "{" + best_match + "}"
                vp_data = json.loads(json_str)
                
                print(f"\n=== FINAL VP DATA ===")
                print(json.dumps(vp_data, indent=2))
                
                # Save to file for analysis
                with open('data/parsed/final_vp_data.json', 'w') as f:
                    json.dump(vp_data, f, indent=2)
                
                print(f"\nSaved complete VP data to: data/parsed/final_vp_data.json")
                
                return vp_data
                
            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {e}")
                print(f"Trying to fix JSON structure...")
                
                # Try to fix common JSON issues
                fixed_json = best_match
                # Ensure proper closing braces
                brace_count = fixed_json.count('{') - fixed_json.count('}')
                fixed_json += '}' * brace_count
                
                try:
                    json_str = "{" + fixed_json + "}"
                    vp_data = json.loads(json_str)
                    print(f"Successfully parsed after fixing!")
                    
                    print(f"\n=== FINAL VP DATA ===")
                    print(json.dumps(vp_data, indent=2))
                    
                    return vp_data
                    
                except json.JSONDecodeError as e2:
                    print(f"Still failed: {e2}")
                    print(f"Raw data length: {len(best_match)}")
                    print(f"Raw data (first 2000 chars):")
                    print(best_match[:2000])
    
    # Fallback: extract individual player data
    print(f"\n=== FALLBACK: Individual player extraction ===")
    
    players = ['86296239', '97116430']
    final_vp = {}
    
    for player_id in players:
        # Find the highest total for this player
        player_pattern = rf'"{player_id}":\{{"total":(\d+).*?\}}'
        player_matches = re.findall(player_pattern, content, re.DOTALL)
        
        if player_matches:
            max_total = max(int(total) for total in player_matches)
            print(f"Player {player_id}: {max_total} VP")
            
            # Find the complete data for this max total
            complete_pattern = rf'"{player_id}":\{{"total":{max_total}(.*?)\}}\}}'
            complete_matches = re.findall(complete_pattern, content, re.DOTALL)
            
            if complete_matches:
                complete_data = '{"total":' + str(max_total) + complete_matches[0] + '}}'
                try:
                    player_vp = json.loads(complete_data)
                    final_vp[player_id] = player_vp
                    print(f"  Successfully parsed player {player_id} data")
                except json.JSONDecodeError:
                    print(f"  Failed to parse player {player_id} data")
    
    if final_vp:
        print(f"\n=== EXTRACTED INDIVIDUAL VP DATA ===")
        print(json.dumps(final_vp, indent=2))
        
        with open('data/parsed/final_vp_data_fallback.json', 'w') as f:
            json.dump(final_vp, f, indent=2)
        
        return final_vp

if __name__ == "__main__":
    extract_complete_vp()

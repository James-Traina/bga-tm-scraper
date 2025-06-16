#!/usr/bin/env python3
"""
Extract VP data from raw HTML
"""
import re
import json

def extract_vp_data():
    """Extract VP data from the HTML file"""
    html_file = "data/raw/replay_250604-1037.html"
    
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Look for JSON data containing VP information
    # Try different patterns to find the VP data
    patterns = [
        r'"data":\{[^}]*"total":\d+[^}]*\}',
        r'\{"86296239":\{[^}]*"total":\d+[^}]*\}[^}]*\}',
        r'\{"\d+":\{[^}]*"total":\d+.*?\}\}',
        r'"data":\{.*?"total":\d+.*?\}\}',
    ]
    
    for i, pattern in enumerate(patterns):
        print(f"\n=== Pattern {i+1}: {pattern} ===")
        matches = re.findall(pattern, content, re.DOTALL)
        print(f"Found {len(matches)} matches")
        
        for j, match in enumerate(matches[:3]):  # Show first 3 matches
            print(f"\nMatch {j+1} (first 500 chars):")
            print(match[:500])
            if len(match) > 500:
                print("...")
    
    # Try to find the specific player IDs mentioned
    print(f"\n=== Searching for player IDs ===")
    player_patterns = [
        r'86296239.*?total.*?62',
        r'97116430.*?total.*?33',
    ]
    
    for pattern in player_patterns:
        matches = re.findall(pattern, content, re.DOTALL)
        print(f"Pattern '{pattern}': {len(matches)} matches")
        for match in matches[:1]:
            print(f"Match: {match[:200]}...")
    
    # Look for JavaScript variables that might contain the data
    print(f"\n=== Looking for JavaScript variables ===")
    js_patterns = [
        r'var\s+\w+\s*=\s*\{[^}]*"total":\d+',
        r'window\.\w+\s*=\s*\{[^}]*"total":\d+',
        r'gamedata\s*=\s*\{.*?"total":\d+',
        r'vpdata\s*=\s*\{.*?"total":\d+',
    ]
    
    for pattern in js_patterns:
        matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
        print(f"JS Pattern '{pattern}': {len(matches)} matches")
        for match in matches[:1]:
            print(f"Match: {match[:200]}...")

if __name__ == "__main__":
    extract_vp_data()

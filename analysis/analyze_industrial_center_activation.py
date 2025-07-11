#!/usr/bin/env python3
"""
Analyze Industrial Center activation rates for each player.
Calculates the ratio of activations to plays for Industrial Center card.
"""

import os
import json
import csv
from collections import defaultdict

def analyze_industrial_center():
    """Analyze Industrial Center activation rates for each player."""
    
    # Dictionary to store player data: {player_id: {'plays': count, 'activations': count, 'name': name}}
    player_data = defaultdict(lambda: {'plays': 0, 'activations': 0, 'name': ''})
    
    # Get all player directories
    parsed_dir = 'data/parsed'
    if not os.path.exists(parsed_dir):
        print(f"Directory {parsed_dir} not found!")
        return
    
    player_dirs = [d for d in os.listdir(parsed_dir) if os.path.isdir(os.path.join(parsed_dir, d))]
    
    total_players = len(player_dirs)
    processed_players = 0
    
    print(f"Found {total_players} player directories to process...")
    
    for player_id in player_dirs:
        player_dir = os.path.join(parsed_dir, player_id)
        game_files = [f for f in os.listdir(player_dir) if f.endswith('.json')]
        
        print(f"Processing player {player_id} ({len(game_files)} games)...")
        
        for game_file in game_files:
            game_path = os.path.join(player_dir, game_file)
            
            try:
                with open(game_path, 'r', encoding='utf-8') as f:
                    game_data = json.load(f)
                
                # Check if moves exist in the game data
                if 'moves' not in game_data:
                    continue
                
                moves = game_data['moves']
                
                # Process each move
                for move in moves:
                    if move.get('player_id') == player_id:
                        # Store player name
                        if player_data[player_id]['name'] == '' and 'player_name' in move:
                            player_data[player_id]['name'] = move['player_name']
                        
                        # Check for Industrial Center plays
                        if (move.get('action_type') == 'play_card' and 
                            move.get('card_played') == 'Industrial Center'):
                            player_data[player_id]['plays'] += 1
                        
                        # Check for Industrial Center activations
                        elif (move.get('action_type') == 'activate_card' and 
                              'Industrial Center' in move.get('description', '')):
                            player_data[player_id]['activations'] += 1
                            
            except Exception as e:
                print(f"Error processing {game_path}: {e}")
                continue
        
        processed_players += 1
        if processed_players % 10 == 0:
            print(f"Processed {processed_players}/{total_players} players...")
    
    # Calculate ratios and prepare results
    results = []
    
    for player_id, data in player_data.items():
        if data['plays'] > 0:  # Only include players who have played Industrial Center
            activation_ratio = data['activations'] / data['plays']
            results.append({
                'player_id': player_id,
                'player_name': data['name'],
                'times_played': data['plays'],
                'times_activated': data['activations'],
                'activation_ratio': activation_ratio
            })
    
    # Sort by activation ratio (descending)
    results.sort(key=lambda x: x['activation_ratio'], reverse=True)
    
    # Write detailed results
    detailed_file = 'analysis/industrial_center_detailed.csv'
    with open(detailed_file, 'w', newline='', encoding='utf-8') as f:
        if results:
            writer = csv.DictWriter(f, fieldnames=['player_id', 'player_name', 'times_played', 'times_activated', 'activation_ratio'])
            writer.writeheader()
            writer.writerows(results)
    
    # Calculate summary statistics
    if results:
        total_players_with_card = len(results)
        total_plays = sum(r['times_played'] for r in results)
        total_activations = sum(r['times_activated'] for r in results)
        overall_ratio = total_activations / total_plays if total_plays > 0 else 0
        
        ratios = [r['activation_ratio'] for r in results]
        avg_ratio = sum(ratios) / len(ratios)
        min_ratio = min(ratios)
        max_ratio = max(ratios)
        
        # Write summary
        summary_file = 'analysis/industrial_center_summary.csv'
        with open(summary_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Metric', 'Value'])
            writer.writerow(['Total Players with Industrial Center', total_players_with_card])
            writer.writerow(['Total Times Played', total_plays])
            writer.writerow(['Total Times Activated', total_activations])
            writer.writerow(['Overall Activation Ratio', f'{overall_ratio:.4f}'])
            writer.writerow(['Average Player Activation Ratio', f'{avg_ratio:.4f}'])
            writer.writerow(['Min Player Activation Ratio', f'{min_ratio:.4f}'])
            writer.writerow(['Max Player Activation Ratio', f'{max_ratio:.4f}'])
        
        print(f"\nAnalysis complete!")
        print(f"Players with Industrial Center: {total_players_with_card}")
        print(f"Total plays: {total_plays}")
        print(f"Total activations: {total_activations}")
        print(f"Overall activation ratio: {overall_ratio:.4f}")
        print(f"Average player activation ratio: {avg_ratio:.4f}")
        print(f"Results saved to {detailed_file} and {summary_file}")
    else:
        print("No Industrial Center plays found in the data.")

if __name__ == "__main__":
    analyze_industrial_center()

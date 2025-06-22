#!/usr/bin/env python3
"""
Analyze average ELO gained per corporation in Terraforming Mars games.

This script processes all parsed game files to calculate the average ELO rating change
(game_rank_change) for each corporation across all games. Unlike other analysis scripts
that focus on perspective players, this one examines all players in each game to get
a comprehensive view of corporation performance.

ELO data comes from the elo_data.game_rank_change field for each player.
"""

import json
import os
import sys
from collections import defaultdict
from pathlib import Path
import csv

def normalize_corporation_name(raw_name):
    """
    Normalize corporation names to their full official names.
    Maps abbreviated or truncated names to their complete versions.
    """
    if not raw_name:
        return "Unknown"
    
    # Corporation name mapping dictionary
    name_mapping = {
        "Valley": "Valley Trust",
        "Mining": "Mining Guild",
        "Point": "Point Luna", 
        "Robinson": "Robinson Industries",
        "Cheung": "Cheung Shing Mars",
        "Interplanetary": "Interplanetary Cinematics",
        "Tharsis": "Tharsis Republic",
        "Saturn": "Saturn Systems",
        # Keep full names as-is
        "Valley Trust": "Valley Trust",
        "Mining Guild": "Mining Guild",
        "Point Luna": "Point Luna",
        "Robinson Industries": "Robinson Industries", 
        "Cheung Shing Mars": "Cheung Shing Mars",
        "Interplanetary Cinematics": "Interplanetary Cinematics",
        "Tharsis Republic": "Tharsis Republic",
        "Saturn Systems": "Saturn Systems",
        "CrediCor": "CrediCor",
        "Ecoline": "Ecoline",
        "Helion": "Helion",
        "Inventrix": "Inventrix",
        "PhoboLog": "PhoboLog",
        "Teractor": "Teractor",
        "ThorGate": "ThorGate",
        "United Nations Mars Initiative": "United Nations Mars Initiative",
        "Vitor": "Vitor"
    }
    
    # Return mapped name or original if not found in mapping
    return name_mapping.get(raw_name, raw_name)

def process_game_for_elo_data(file_path):
    """
    Process a single game file to extract ELO data for all players.
    Returns list of (corporation, elo_change) tuples or empty list if processing fails.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            game_data = json.load(f)
        
        # Get all players from the game
        players = game_data.get('players', {})
        if not players:
            print(f"Warning: No players found in {file_path}")
            return []
        
        elo_data_list = []
        
        # Extract corporation and ELO change for each player
        for player_id, player_data in players.items():
            corporation = player_data.get('corporation')
            elo_data = player_data.get('elo_data')
            
            if not corporation:
                print(f"Warning: No corporation found for player {player_id} in {file_path}")
                continue
            
            # Check if elo_data exists and is not None
            if not elo_data or not isinstance(elo_data, dict):
                print(f"Warning: No elo_data found for player {player_id} ({corporation}) in {file_path}")
                continue
            
            # Get ELO change (game_rank_change)
            elo_change = elo_data.get('game_rank_change')
            
            if elo_change is None:
                print(f"Warning: No game_rank_change found for player {player_id} ({corporation}) in {file_path}")
                continue
            
            # Normalize corporation name
            normalized_corporation = normalize_corporation_name(corporation)
            
            # Add to results
            elo_data_list.append({
                'corporation': normalized_corporation,
                'elo_change': elo_change,
                'player_id': player_id,
                'player_name': player_data.get('player_name', 'Unknown'),
                'replay_id': game_data.get('replay_id', 'unknown'),
                'game_date': game_data.get('game_date', 'unknown')
            })
        
        return elo_data_list
        
    except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
        print(f"Warning: Could not process {file_path}: {e}")
        return []

def find_all_game_files(data_dir):
    """Find all JSON game files in the parsed data directory."""
    game_files = []
    data_path = Path(data_dir)
    
    if not data_path.exists():
        print(f"Error: Data directory {data_dir} does not exist")
        return game_files
    
    # Look for all JSON files in player subdirectories
    for player_dir in data_path.iterdir():
        if player_dir.is_dir() and player_dir.name.isdigit():
            for game_file in player_dir.glob("*.json"):
                game_files.append(game_file)
    
    return game_files

def analyze_corporation_elo(data_dir):
    """
    Main analysis function that processes all games and calculates corporation ELO statistics.
    """
    print("Starting Corporation ELO analysis...")
    
    # Find all game files
    game_files = find_all_game_files(data_dir)
    print(f"Found {len(game_files)} game files to process")
    
    if not game_files:
        print("No game files found. Please check the data directory.")
        return None, []
    
    # Data structures for aggregation
    corporation_stats = defaultdict(lambda: {
        'total_elo_change': 0,
        'game_count': 0,
        'elo_changes': [],  # For calculating statistics
        'player_instances': []  # For detailed tracking
    })
    
    all_elo_data = []
    total_games_processed = 0
    total_player_instances = 0
    
    # Process each game file
    for i, game_file in enumerate(game_files):
        elo_data_list = process_game_for_elo_data(game_file)
        
        if elo_data_list:
            total_games_processed += 1
            
            # Process each player's data from this game
            for elo_data in elo_data_list:
                corporation = elo_data['corporation']
                elo_change = elo_data['elo_change']
                
                # Update corporation statistics
                corporation_stats[corporation]['total_elo_change'] += elo_change
                corporation_stats[corporation]['game_count'] += 1
                corporation_stats[corporation]['elo_changes'].append(elo_change)
                corporation_stats[corporation]['player_instances'].append(elo_data)
                
                # Add to overall data
                all_elo_data.append(elo_data)
                total_player_instances += 1
        
        # Progress indicator
        if (i + 1) % 50 == 0:
            print(f"Processed {i + 1} games...")
    
    print(f"\nAnalysis complete!")
    print(f"Games processed: {total_games_processed}")
    print(f"Total player instances: {total_player_instances}")
    print(f"Unique corporations: {len(corporation_stats)}")
    
    # Calculate final statistics for each corporation
    corporation_results = {}
    for corporation, stats in corporation_stats.items():
        avg_elo_change = stats['total_elo_change'] / stats['game_count']
        
        # Calculate additional statistics
        elo_changes = stats['elo_changes']
        min_elo = min(elo_changes)
        max_elo = max(elo_changes)
        
        # Calculate win rate (positive ELO changes)
        positive_changes = [x for x in elo_changes if x > 0]
        win_rate = len(positive_changes) / len(elo_changes) if elo_changes else 0
        
        corporation_results[corporation] = {
            'corporation': corporation,
            'game_count': stats['game_count'],
            'total_elo_change': stats['total_elo_change'],
            'avg_elo_change': avg_elo_change,
            'min_elo_change': min_elo,
            'max_elo_change': max_elo,
            'win_rate': win_rate,
            'player_instances': stats['player_instances']
        }
    
    return corporation_results, all_elo_data

def display_results(corporation_results):
    """Display analysis results."""
    if not corporation_results:
        print("No results to display.")
        return
    
    print("\n" + "="*100)
    print("CORPORATION ELO ANALYSIS RESULTS")
    print("="*100)
    print("Average ELO change (game_rank_change) per corporation")
    print("Positive values indicate corporations that tend to gain ELO rating")
    print("="*100)
    
    # Sort corporations by average ELO change (descending)
    sorted_corps = sorted(corporation_results.items(), 
                         key=lambda x: x[1]['avg_elo_change'], 
                         reverse=True)
    
    print(f"\n{'Rank':<4} {'Corporation':<25} {'Games':<6} {'Avg ELO':<8} {'Total':<7} {'Min':<6} {'Max':<6} {'Win%':<6}")
    print("-" * 100)
    
    for rank, (corporation, stats) in enumerate(sorted_corps, 1):
        print(f"{rank:<4} {corporation:<25} {stats['game_count']:<6} "
              f"{stats['avg_elo_change']:<8.2f} {stats['total_elo_change']:<7} "
              f"{stats['min_elo_change']:<6} {stats['max_elo_change']:<6} "
              f"{stats['win_rate']*100:<6.1f}")
    
    # Calculate overall statistics
    all_avg_elos = [stats['avg_elo_change'] for stats in corporation_results.values()]
    all_game_counts = [stats['game_count'] for stats in corporation_results.values()]
    
    overall_avg = sum(all_avg_elos) / len(all_avg_elos)
    total_games = sum(all_game_counts)
    
    print(f"\n{'='*100}")
    print(f"SUMMARY STATISTICS:")
    print(f"Total corporation instances: {total_games}")
    print(f"Overall average ELO change: {overall_avg:.3f}")
    print(f"Best performing: {sorted_corps[0][0]} (+{sorted_corps[0][1]['avg_elo_change']:.2f})")
    print(f"Worst performing: {sorted_corps[-1][0]} ({sorted_corps[-1][1]['avg_elo_change']:.2f})")
    print(f"{'='*100}")

def save_detailed_results_to_csv(all_elo_data, output_file):
    """Save detailed game-by-game results to a CSV file."""
    if not all_elo_data:
        print("No detailed results to save.")
        return
    
    try:
        fieldnames = ['corporation', 'elo_change', 'player_id', 'player_name', 
                     'replay_id', 'game_date']
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            writer.writeheader()
            
            # Sort by corporation, then by game_date
            sorted_results = sorted(all_elo_data, 
                                  key=lambda x: (x['corporation'], x['game_date']))
            
            for result in sorted_results:
                writer.writerow(result)
        
        print(f"\nDetailed results saved to: {output_file}")
        
    except Exception as e:
        print(f"Error saving detailed CSV file: {e}")

def save_corporation_summary_to_csv(corporation_results, output_file):
    """Save corporation summary statistics to a CSV file."""
    if not corporation_results:
        print("No corporation summary to save.")
        return
    
    try:
        fieldnames = ['corporation', 'game_count', 'total_elo_change', 'avg_elo_change', 
                     'min_elo_change', 'max_elo_change', 'win_rate']
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            writer.writeheader()
            
            # Sort by average ELO change (descending)
            sorted_corps = sorted(corporation_results.items(), 
                                key=lambda x: x[1]['avg_elo_change'], 
                                reverse=True)
            
            for corporation, stats in sorted_corps:
                row = {
                    'corporation': corporation,
                    'game_count': stats['game_count'],
                    'total_elo_change': stats['total_elo_change'],
                    'avg_elo_change': round(stats['avg_elo_change'], 4),
                    'min_elo_change': stats['min_elo_change'],
                    'max_elo_change': stats['max_elo_change'],
                    'win_rate': round(stats['win_rate'], 4)
                }
                writer.writerow(row)
        
        print(f"Corporation summary saved to: {output_file}")
        
    except Exception as e:
        print(f"Error saving corporation summary CSV file: {e}")

def main():
    """Main function to run the Corporation ELO analysis."""
    # Set up paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    data_dir = project_root / "data" / "parsed"
    detailed_output_file = script_dir / "corporation_elo_detailed.csv"
    summary_output_file = script_dir / "corporation_elo_summary.csv"
    
    print("Terraforming Mars - Corporation ELO Analysis")
    print("=" * 50)
    
    # Run the analysis
    corporation_results, all_elo_data = analyze_corporation_elo(data_dir)
    
    if corporation_results:
        # Display results
        display_results(corporation_results)
        
        # Save to CSV files
        save_detailed_results_to_csv(all_elo_data, detailed_output_file)
        save_corporation_summary_to_csv(corporation_results, summary_output_file)
        
        print(f"\nAnalysis complete! Check the CSV files for detailed data.")
    else:
        print("No data found to analyze.")

if __name__ == "__main__":
    main()

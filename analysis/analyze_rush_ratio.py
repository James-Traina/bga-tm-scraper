#!/usr/bin/env python3
"""
Analyze Rush Ratio for Terraforming Mars players.

Rush Ratio is calculated as: (TR + Greeneries VP) / Final VP
This measures how much of a player's victory points come from terraforming activities
(temperature/oxygen increases via TR and greenery placement) versus other sources.

This script processes all parsed game files to calculate each player's average Rush Ratio
across all their games from their perspective.
"""

import json
from collections import defaultdict
from pathlib import Path
import csv

def process_game_for_rush_ratio(file_path, player_perspective_id):
    """
    Process a single game file to extract Rush Ratio data for the perspective player.
    Returns dict with game data or None if processing fails.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            game_data = json.load(f)
        
        # Get the perspective player's data
        players = game_data.get('players', {})
        if player_perspective_id not in players:
            print(f"Warning: Player {player_perspective_id} not found in {file_path}")
            return None
        
        player_data = players[player_perspective_id]
        
        # Extract required data
        final_tr = player_data.get('final_tr', 0)
        final_vp = player_data.get('final_vp', 0)
        
        # Get greeneries VP from vp_breakdown
        vp_breakdown = player_data.get('vp_breakdown', {})
        greeneries_vp = vp_breakdown.get('greeneries', 0)
        
        # Skip games where final_vp is 0 to avoid division by zero
        if final_vp == 0:
            print(f"Warning: Final VP is 0 in {file_path}, skipping")
            return None
        
        # Calculate Rush Ratio
        rush_ratio = (final_tr + greeneries_vp) / final_vp
        
        # Extract additional game info
        replay_id = game_data.get('replay_id', 'unknown')
        game_date = game_data.get('game_date', 'unknown')
        player_name = player_data.get('player_name', 'unknown')
        corporation = player_data.get('corporation', 'unknown')
        
        return {
            'replay_id': replay_id,
            'game_date': game_date,
            'player_id': player_perspective_id,
            'player_name': player_name,
            'corporation': corporation,
            'final_tr': final_tr,
            'greeneries_vp': greeneries_vp,
            'final_vp': final_vp,
            'rush_ratio': rush_ratio
        }
        
    except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
        print(f"Warning: Could not process {file_path}: {e}")
        return None

def find_all_game_files(data_dir):
    """Find all JSON game files organized by player perspective ID."""
    player_games = defaultdict(list)
    data_path = Path(data_dir)
    
    if not data_path.exists():
        print(f"Error: Data directory {data_dir} does not exist")
        return player_games
    
    # Look for all JSON files in player subdirectories
    for player_dir in data_path.iterdir():
        if player_dir.is_dir() and player_dir.name.isdigit():
            player_id = player_dir.name
            for game_file in player_dir.glob("*.json"):
                player_games[player_id].append(game_file)
    
    return player_games

def analyze_rush_ratio(data_dir):
    """
    Main analysis function that processes all games and calculates Rush Ratio statistics.
    """
    print("Starting Rush Ratio analysis...")
    
    # Find all game files organized by player
    player_games = find_all_game_files(data_dir)
    print(f"Found {len(player_games)} players with game data")
    
    if not player_games:
        print("No game files found. Please check the data directory.")
        return None
    
    # Data structures for aggregation
    player_stats = {}
    all_game_results = []
    
    total_games_processed = 0
    total_games_found = 0
    
    # Process each player's games
    for player_id, game_files in player_games.items():
        print(f"\nProcessing player {player_id}...")
        total_games_found += len(game_files)
        
        player_rush_ratios = []
        player_game_data = []
        
        # Process each game for this player
        for game_file in game_files:
            game_result = process_game_for_rush_ratio(game_file, player_id)
            
            if game_result:
                player_rush_ratios.append(game_result['rush_ratio'])
                player_game_data.append(game_result)
                all_game_results.append(game_result)
                total_games_processed += 1
        
        # Calculate player statistics
        if player_rush_ratios:
            avg_rush_ratio = sum(player_rush_ratios) / len(player_rush_ratios)
            min_rush_ratio = min(player_rush_ratios)
            max_rush_ratio = max(player_rush_ratios)
            
            # Get player name from first game
            player_name = player_game_data[0]['player_name'] if player_game_data else 'Unknown'
            
            player_stats[player_id] = {
                'player_name': player_name,
                'games_count': len(player_rush_ratios),
                'avg_rush_ratio': avg_rush_ratio,
                'min_rush_ratio': min_rush_ratio,
                'max_rush_ratio': max_rush_ratio,
                'game_data': player_game_data
            }
            
            print(f"  {player_name}: {len(player_rush_ratios)} games, avg Rush Ratio: {avg_rush_ratio:.3f}")
        else:
            print(f"  No valid games found for player {player_id}")
    
    print(f"\nAnalysis complete!")
    print(f"Total games found: {total_games_found}")
    print(f"Total games processed: {total_games_processed}")
    print(f"Players with data: {len(player_stats)}")
    
    return player_stats, all_game_results

def display_results(player_stats):
    """Display analysis results."""
    if not player_stats:
        print("No results to display.")
        return
    
    print("\n" + "="*80)
    print("RUSH RATIO ANALYSIS RESULTS")
    print("="*80)
    print("Rush Ratio = (TR + Greeneries VP) / Final VP")
    print("Higher values indicate more focus on terraforming activities")
    print("="*80)
    
    # Sort players by average Rush Ratio (descending)
    sorted_players = sorted(player_stats.items(), 
                          key=lambda x: x[1]['avg_rush_ratio'], 
                          reverse=True)
    
    print(f"\n{'Rank':<4} {'Player Name':<20} {'ID':<10} {'Games':<6} {'Avg':<7} {'Min':<7} {'Max':<7}")
    print("-" * 80)
    
    for rank, (player_id, stats) in enumerate(sorted_players, 1):
        print(f"{rank:<4} {stats['player_name']:<20} {player_id:<10} "
              f"{stats['games_count']:<6} {stats['avg_rush_ratio']:<7.3f} "
              f"{stats['min_rush_ratio']:<7.3f} {stats['max_rush_ratio']:<7.3f}")
    
    # Calculate overall statistics
    all_avg_ratios = [stats['avg_rush_ratio'] for stats in player_stats.values()]
    overall_avg = sum(all_avg_ratios) / len(all_avg_ratios)
    
    print(f"\n{'='*80}")
    print(f"SUMMARY STATISTICS:")
    print(f"Overall average Rush Ratio: {overall_avg:.3f}")
    print(f"Highest average: {max(all_avg_ratios):.3f}")
    print(f"Lowest average: {min(all_avg_ratios):.3f}")
    print(f"{'='*80}")

def save_detailed_results_to_csv(all_game_results, output_file):
    """Save detailed game-by-game results to a CSV file."""
    if not all_game_results:
        print("No detailed results to save.")
        return
    
    try:
        fieldnames = ['player_id', 'player_name', 'replay_id', 'game_date', 'corporation',
                     'final_tr', 'greeneries_vp', 'final_vp', 'rush_ratio']
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            writer.writeheader()
            
            # Sort by player_id, then by game_date
            sorted_results = sorted(all_game_results, 
                                  key=lambda x: (x['player_id'], x['game_date']))
            
            for result in sorted_results:
                writer.writerow(result)
        
        print(f"\nDetailed results saved to: {output_file}")
        
    except Exception as e:
        print(f"Error saving CSV file: {e}")

def save_player_summary_to_csv(player_stats, output_file):
    """Save player summary statistics to a CSV file."""
    if not player_stats:
        print("No player summary to save.")
        return
    
    try:
        fieldnames = ['player_id', 'player_name', 'games_count', 'avg_rush_ratio', 
                     'min_rush_ratio', 'max_rush_ratio']
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            writer.writeheader()
            
            # Sort by average rush ratio (descending)
            sorted_players = sorted(player_stats.items(), 
                                  key=lambda x: x[1]['avg_rush_ratio'], 
                                  reverse=True)
            
            for player_id, stats in sorted_players:
                row = {
                    'player_id': player_id,
                    'player_name': stats['player_name'],
                    'games_count': stats['games_count'],
                    'avg_rush_ratio': round(stats['avg_rush_ratio'], 4),
                    'min_rush_ratio': round(stats['min_rush_ratio'], 4),
                    'max_rush_ratio': round(stats['max_rush_ratio'], 4)
                }
                writer.writerow(row)
        
        print(f"Player summary saved to: {output_file}")
        
    except Exception as e:
        print(f"Error saving player summary CSV file: {e}")

def main():
    """Main function to run the Rush Ratio analysis."""
    # Set up paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    data_dir = project_root / "data" / "parsed"
    detailed_output_file = script_dir / "rush_ratio_detailed.csv"
    summary_output_file = script_dir / "rush_ratio_summary.csv"
    
    print("Terraforming Mars - Rush Ratio Analysis")
    print("=" * 50)
    
    # Run the analysis
    player_stats, all_game_results = analyze_rush_ratio(data_dir)
    
    if player_stats:
        # Display results
        display_results(player_stats)
        
        # Save to CSV files
        save_detailed_results_to_csv(all_game_results, detailed_output_file)
        save_player_summary_to_csv(player_stats, summary_output_file)
        
        print(f"\nAnalysis complete! Check the CSV files for detailed data.")
    else:
        print("No data found to analyze.")

if __name__ == "__main__":
    main()

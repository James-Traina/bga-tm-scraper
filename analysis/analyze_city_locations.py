#!/usr/bin/env python3
"""
Analyze the most valuable city locations on the Tharsis map from Terraforming Mars games.

This script processes all parsed game files to determine:
- Total VP scored by cities on each hex location
- Average VP per city placement on each hex
- Frequency of city placements by location
"""

import json
import os
import sys
from collections import defaultdict
from pathlib import Path
import csv

def extract_city_data_from_game(file_path):
    """
    Extract city placement data from a single game file.
    Returns a list of (hex_location, vp_value, generation_placed) tuples.
    """
    cities_data = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            game_data = json.load(f)
            
            if 'final_state' not in game_data or 'moves' not in game_data:
                return cities_data
                
            final_state = game_data['final_state']
            moves = game_data['moves']
            
            if 'player_vp' not in final_state:
                return cities_data
            
            # Track when each city first appears for each player
            city_placement_generations = {}
            
            # Go through moves to find when cities first appear
            for move in moves:
                if 'game_state' not in move or 'player_vp' not in move['game_state']:
                    continue
                    
                current_generation = move['game_state'].get('generation', 1)
                current_player_vp = move['game_state']['player_vp']
                
                for player_id, player_data in current_player_vp.items():
                    if 'details' in player_data and 'cities' in player_data['details']:
                        cities = player_data['details']['cities']
                        
                        for hex_location in cities.keys():
                            # Create unique key for player-location combination
                            city_key = f"{player_id}_{hex_location}"
                            
                            # Record the first time we see this city
                            if city_key not in city_placement_generations:
                                city_placement_generations[city_key] = current_generation
            
            # Now get final city data with placement generations
            for player_id, player_data in final_state['player_vp'].items():
                if 'details' in player_data and 'cities' in player_data['details']:
                    cities = player_data['details']['cities']
                    
                    for hex_location, city_info in cities.items():
                        if 'vp' in city_info:
                            city_key = f"{player_id}_{hex_location}"
                            generation_placed = city_placement_generations.get(city_key, None)
                            cities_data.append((hex_location, city_info['vp'], generation_placed))
                            
    except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
        print(f"Warning: Could not process {file_path}: {e}")
        
    return cities_data

def find_all_game_files(data_dir):
    """Find all JSON game files in the parsed data directory."""
    game_files = []
    data_path = Path(data_dir)
    
    if not data_path.exists():
        print(f"Error: Data directory {data_dir} does not exist")
        return game_files
    
    # Look for all JSON files in player subdirectories
    for player_dir in data_path.iterdir():
        if player_dir.is_dir():
            for game_file in player_dir.glob("*.json"):
                game_files.append(game_file)
                
    return game_files

def analyze_city_locations(data_dir):
    """
    Main analysis function that processes all games and calculates city location statistics.
    """
    print("Starting city location analysis...")
    
    # Find all game files
    game_files = find_all_game_files(data_dir)
    print(f"Found {len(game_files)} game files to process")
    
    if not game_files:
        print("No game files found. Please check the data directory.")
        return
    
    # Data structures for aggregation
    hex_stats = defaultdict(lambda: {
        'total_vp': 0,
        'placement_count': 0,
        'vp_values': [],
        'generation_values': []
    })
    
    processed_games = 0
    total_cities = 0
    
    # Process each game file
    for game_file in game_files:
        cities_data = extract_city_data_from_game(game_file)
        
        if cities_data:
            processed_games += 1
            total_cities += len(cities_data)
            
            # Aggregate data by hex location
            for hex_location, vp_value, generation_placed in cities_data:
                hex_stats[hex_location]['total_vp'] += vp_value
                hex_stats[hex_location]['placement_count'] += 1
                hex_stats[hex_location]['vp_values'].append(vp_value)
                if generation_placed is not None:
                    hex_stats[hex_location]['generation_values'].append(generation_placed)
        
        # Progress indicator
        if processed_games % 10 == 0:
            print(f"Processed {processed_games} games...")
    
    print(f"\nAnalysis complete!")
    print(f"Processed {processed_games} games with city data")
    print(f"Total cities analyzed: {total_cities}")
    print(f"Unique hex locations: {len(hex_stats)}")
    
    # Calculate averages and prepare results
    results = []
    for hex_location, stats in hex_stats.items():
        avg_vp = stats['total_vp'] / stats['placement_count']
        avg_generation = None
        if stats['generation_values']:
            avg_generation = round(sum(stats['generation_values']) / len(stats['generation_values']), 1)
        
        results.append({
            'hex_location': hex_location,
            'total_vp': stats['total_vp'],
            'placement_count': stats['placement_count'],
            'average_vp': round(avg_vp, 2),
            'average_generation': avg_generation,
            'frequency_percent': round((stats['placement_count'] / processed_games) * 100, 2)
        })
    
    return results, processed_games, total_cities

def display_results(results):
    """Display analysis results in a formatted way."""
    if not results:
        print("No results to display.")
        return
    
    print("\n" + "="*80)
    print("CITY LOCATION ANALYSIS RESULTS")
    print("="*80)
    
    # Sort by total VP (most valuable overall)
    print("\nTOP 15 LOCATIONS BY TOTAL VP SCORED:")
    print("-" * 85)
    print(f"{'Hex Location':<25} {'Total VP':<10} {'Count':<8} {'Avg VP':<8} {'Avg Gen':<8} {'Freq %':<8}")
    print("-" * 85)
    
    sorted_by_total = sorted(results, key=lambda x: x['total_vp'], reverse=True)
    for i, result in enumerate(sorted_by_total[:15], 1):
        avg_gen_str = str(result['average_generation']) if result['average_generation'] is not None else "N/A"
        print(f"{result['hex_location']:<25} {result['total_vp']:<10} "
              f"{result['placement_count']:<8} {result['average_vp']:<8} {avg_gen_str:<8} {result['frequency_percent']:<8}")
    
    # Sort by average VP (most valuable per placement)
    print(f"\nTOP 15 LOCATIONS BY AVERAGE VP PER CITY:")
    print("-" * 85)
    print(f"{'Hex Location':<25} {'Avg VP':<10} {'Count':<8} {'Total VP':<10} {'Avg Gen':<8} {'Freq %':<8}")
    print("-" * 85)
    
    # Filter out locations with very few placements for average calculation
    filtered_for_avg = [r for r in results if r['placement_count'] >= 3]
    sorted_by_avg = sorted(filtered_for_avg, key=lambda x: x['average_vp'], reverse=True)
    
    for i, result in enumerate(sorted_by_avg[:15], 1):
        avg_gen_str = str(result['average_generation']) if result['average_generation'] is not None else "N/A"
        print(f"{result['hex_location']:<25} {result['average_vp']:<10} "
              f"{result['placement_count']:<8} {result['total_vp']:<10} {avg_gen_str:<8} {result['frequency_percent']:<8}")
    
    # Sort by frequency (most popular locations)
    print(f"\nTOP 15 MOST POPULAR CITY LOCATIONS:")
    print("-" * 85)
    print(f"{'Hex Location':<25} {'Count':<8} {'Freq %':<8} {'Avg VP':<8} {'Avg Gen':<8} {'Total VP':<10}")
    print("-" * 85)
    
    sorted_by_freq = sorted(results, key=lambda x: x['placement_count'], reverse=True)
    for i, result in enumerate(sorted_by_freq[:15], 1):
        avg_gen_str = str(result['average_generation']) if result['average_generation'] is not None else "N/A"
        print(f"{result['hex_location']:<25} {result['placement_count']:<8} "
              f"{result['frequency_percent']:<8} {result['average_vp']:<8} {avg_gen_str:<8} {result['total_vp']:<10}")

def save_results_to_csv(results, output_file):
    """Save detailed results to a CSV file."""
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['hex_location', 'total_vp', 'placement_count', 'average_vp', 'average_generation', 'frequency_percent']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            
            writer.writeheader()
            # Sort by total VP for CSV output
            sorted_results = sorted(results, key=lambda x: x['total_vp'], reverse=True)
            for result in sorted_results:
                writer.writerow(result)
                
        print(f"\nDetailed results saved to: {output_file}")
        
    except Exception as e:
        print(f"Error saving CSV file: {e}")

def main():
    """Main function to run the city location analysis."""
    # Set up paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    data_dir = project_root / "data" / "parsed"
    output_file = script_dir / "city_locations_analysis.csv"
    
    print("Terraforming Mars - City Location Analysis")
    print("=" * 50)
    
    # Run the analysis
    results, processed_games, total_cities = analyze_city_locations(data_dir)
    
    if results:
        # Display results
        display_results(results)
        
        # Save to CSV
        save_results_to_csv(results, output_file)
        
        print(f"\n" + "="*80)
        print("SUMMARY STATISTICS:")
        print(f"Games processed: {processed_games}")
        print(f"Total cities analyzed: {total_cities}")
        print(f"Unique hex locations: {len(results)}")
        print(f"Average cities per game: {round(total_cities / processed_games, 1)}")
        print("="*80)
    else:
        print("No data found to analyze.")

if __name__ == "__main__":
    main()

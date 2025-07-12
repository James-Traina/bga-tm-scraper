#!/usr/bin/env python3
"""
Analyze average ELO rating (elo_data.game_rank) of all players across all Terraforming Mars games.

This script processes all parsed game files to calculate comprehensive statistics
about ELO ratings, including overall average, median, distribution, etc.

ELO data comes from the elo_data.game_rank field for each player.
"""

import json
from pathlib import Path
import csv
import statistics

def process_game_for_elo_ratings(file_path):
    """
    Process a single game file to extract ELO ratings for all players.
    Returns list of ELO rating data or empty list if processing fails.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            game_data = json.load(f)
        
        # Get all players from the game
        players = game_data.get('players', {})
        if not players:
            print(f"Warning: No players found in {file_path}")
            return []
        
        elo_ratings = []
        
        # Extract ELO rating for each player
        for player_id, player_data in players.items():
            elo_data = player_data.get('elo_data')
            
            # Check if elo_data exists and is not None
            if not elo_data or not isinstance(elo_data, dict):
                print(f"Warning: No elo_data found for player {player_id} in {file_path}")
                continue
            
            # Get ELO rating (game_rank)
            elo_rating = elo_data.get('game_rank')
            
            if elo_rating is None:
                print(f"Warning: No game_rank found for player {player_id} in {file_path}")
                continue
            
            # Add to results
            elo_ratings.append({
                'elo_rating': elo_rating,
                'player_id': player_id,
                'player_name': player_data.get('player_name', 'Unknown'),
                'corporation': player_data.get('corporation', 'Unknown'),
                'replay_id': game_data.get('replay_id', 'unknown'),
                'game_date': game_data.get('game_date', 'unknown')
            })
        
        return elo_ratings
        
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
        if "86296239" in str(player_dir):
            continue

        if player_dir.is_dir() and player_dir.name.isdigit():
            for game_file in player_dir.glob("*.json"):
                game_files.append(game_file)
    
    return game_files

def calculate_elo_distribution(elo_ratings):
    """Calculate ELO rating distribution by ranges."""
    ranges = [
        (0, 800, "< 800"),
        (800, 1000, "800-999"),
        (1000, 1200, "1000-1199"),
        (1200, 1400, "1200-1399"),
        (1400, 1600, "1400-1599"),
        (1600, 1800, "1600-1799"),
        (1800, 2000, "1800-1999"),
        (2000, float('inf'), "2000+")
    ]
    
    distribution = {}
    for min_elo, max_elo, label in ranges:
        count = sum(1 for rating in elo_ratings if min_elo <= rating < max_elo)
        percentage = (count / len(elo_ratings)) * 100 if elo_ratings else 0
        distribution[label] = {
            'count': count,
            'percentage': percentage
        }
    
    return distribution

def analyze_average_elo(data_dir):
    """
    Main analysis function that processes all games and calculates ELO statistics.
    """
    print("Starting Average ELO analysis...")
    
    # Find all game files
    game_files = find_all_game_files(data_dir)
    print(f"Found {len(game_files)} game files to process")
    
    if not game_files:
        print("No game files found. Please check the data directory.")
        return None
    
    all_elo_data = []
    total_games_processed = 0
    
    # Process each game file
    for i, game_file in enumerate(game_files):
        elo_ratings = process_game_for_elo_ratings(game_file)
        
        if elo_ratings:
            total_games_processed += 1
            all_elo_data.extend(elo_ratings)
        
        # Progress indicator
        if (i + 1) % 50 == 0:
            print(f"Processed {i + 1} games...")
    
    print(f"\nAnalysis complete!")
    print(f"Games processed: {total_games_processed}")
    print(f"Total player instances: {len(all_elo_data)}")
    
    if not all_elo_data:
        print("No ELO data found.")
        return None
    
    # Extract just the ELO ratings for statistical calculations
    elo_ratings = [data['elo_rating'] for data in all_elo_data]
    
    # Calculate statistics
    stats = {
        'total_players': len(elo_ratings),
        'average_elo': statistics.mean(elo_ratings),
        'median_elo': statistics.median(elo_ratings),
        'min_elo': min(elo_ratings),
        'max_elo': max(elo_ratings),
        'std_dev': statistics.stdev(elo_ratings) if len(elo_ratings) > 1 else 0,
        'distribution': calculate_elo_distribution(elo_ratings)
    }
    
    return stats, all_elo_data

def display_results(stats):
    """Display analysis results."""
    if not stats:
        print("No results to display.")
        return
    
    print("\n" + "="*80)
    print("AVERAGE ELO ANALYSIS RESULTS")
    print("="*80)
    print("ELO rating statistics across all players in all games")
    print("="*80)
    
    print(f"\nOVERALL STATISTICS:")
    print(f"Total player instances: {stats['total_players']:,}")
    print(f"Average ELO rating: {stats['average_elo']:.2f}")
    print(f"Median ELO rating: {stats['median_elo']:.2f}")
    print(f"Minimum ELO rating: {stats['min_elo']}")
    print(f"Maximum ELO rating: {stats['max_elo']}")
    print(f"Standard deviation: {stats['std_dev']:.2f}")
    
    print(f"\nELO DISTRIBUTION:")
    print(f"{'Range':<12} {'Count':<8} {'Percentage':<10}")
    print("-" * 32)
    
    for range_label, data in stats['distribution'].items():
        print(f"{range_label:<12} {data['count']:<8} {data['percentage']:<10.1f}%")
    
    print(f"\n{'='*80}")

def save_detailed_results_to_csv(all_elo_data, output_file):
    """Save detailed player ELO data to a CSV file."""
    if not all_elo_data:
        print("No detailed results to save.")
        return
    
    try:
        fieldnames = ['elo_rating', 'player_id', 'player_name', 'corporation',
                     'replay_id', 'game_date']
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            writer.writeheader()
            
            # Sort by ELO rating (descending)
            sorted_results = sorted(all_elo_data, 
                                  key=lambda x: x['elo_rating'], 
                                  reverse=True)
            
            for result in sorted_results:
                writer.writerow(result)
        
        print(f"\nDetailed results saved to: {output_file}")
        
    except Exception as e:
        print(f"Error saving detailed CSV file: {e}")

def save_summary_to_csv(stats, output_file):
    """Save summary statistics to a CSV file."""
    if not stats:
        print("No summary to save.")
        return
    
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
            
            # Write header
            writer.writerow(['Statistic', 'Value'])
            
            # Write basic statistics
            writer.writerow(['Total Players', stats['total_players']])
            writer.writerow(['Average ELO', round(stats['average_elo'], 2)])
            writer.writerow(['Median ELO', round(stats['median_elo'], 2)])
            writer.writerow(['Minimum ELO', stats['min_elo']])
            writer.writerow(['Maximum ELO', stats['max_elo']])
            writer.writerow(['Standard Deviation', round(stats['std_dev'], 2)])
            
            # Write distribution
            writer.writerow([])  # Empty row
            writer.writerow(['ELO Range', 'Count', 'Percentage'])
            
            for range_label, data in stats['distribution'].items():
                writer.writerow([range_label, data['count'], 
                               round(data['percentage'], 1)])
        
        print(f"Summary statistics saved to: {output_file}")
        
    except Exception as e:
        print(f"Error saving summary CSV file: {e}")

def main():
    """Main function to run the Average ELO analysis."""
    # Set up paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    data_dir = project_root / "data" / "parsed"
    detailed_output_file = script_dir / "average_elo_detailed.csv"
    summary_output_file = script_dir / "average_elo_summary.csv"
    
    print("Terraforming Mars - Average ELO Analysis")
    print("=" * 50)
    
    # Run the analysis
    result = analyze_average_elo(data_dir)
    
    if result:
        stats, all_elo_data = result
        
        # Display results
        display_results(stats)
        
        # Save to CSV files
        save_detailed_results_to_csv(all_elo_data, detailed_output_file)
        save_summary_to_csv(stats, summary_output_file)
        
        print(f"\nAnalysis complete! Check the CSV files for detailed data.")
    else:
        print("No data found to analyze.")

if __name__ == "__main__":
    main()

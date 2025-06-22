import json
import os
import sys
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
from pathlib import Path

# Add parent directory to path to import config
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

try:
    import config
except ImportError as e:
    print(f"Error importing config: {e}")
    print(f"Current directory: {current_dir}")
    print(f"Parent directory: {parent_dir}")
    print(f"Python path: {sys.path}")
    sys.exit(1)

def analyze_parameter_progression():
    """
    Analyze the average progression of temperature, oxygen, and oceans per generation
    across all parsed Terraforming Mars games.
    """
    
    # Dictionary to store progression data by generation
    # Structure: {generation: {'temperature': [deltas], 'oxygen': [deltas], 'oceans': [deltas]}}
    generation_progressions = defaultdict(lambda: {'temperature': [], 'oxygen': [], 'oceans': []})
    
    # Path to parsed data directory
    parsed_data_dir = Path(config.PARSED_DATA_DIR)
    
    if not parsed_data_dir.exists():
        print(f"Error: Directory {parsed_data_dir} does not exist")
        return
    
    total_games = 0
    processed_games = 0
    
    # Traverse all subdirectories (player IDs) in data/parsed
    for player_dir in parsed_data_dir.iterdir():
        if not player_dir.is_dir():
            continue
            
        # Process all JSON files in each player directory
        for json_file in player_dir.glob('*.json'):
            total_games += 1
            
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    game_data = json.load(f)
                
                # Extract parameter progression
                parameter_progression = game_data.get('parameter_progression', [])
                
                if not parameter_progression:
                    print(f"Warning: No parameter_progression found in {json_file}")
                    continue
                
                # Group progression entries by generation
                generation_data = defaultdict(list)
                for entry in parameter_progression:
                    generation = entry.get('generation')
                    if generation is not None:
                        generation_data[generation].append(entry)
                
                # Calculate progression for each generation in this game
                for generation, entries in generation_data.items():
                    if len(entries) < 1:
                        continue

                    if generation > 13:
                        continue
                    
                    # Sort entries by move_number to get first and last
                    entries.sort(key=lambda x: x.get('move_number', 0))
                    
                    first_entry = entries[0]
                    last_entry = entries[-1]
                    
                    # Calculate deltas (progression = final - initial)
                    temp_delta = (last_entry.get('temperature', 0) - first_entry.get('temperature', 0)) / 2     # Divide by 2 to normalize on number of steps
                    oxygen_delta = last_entry.get('oxygen', 0) - first_entry.get('oxygen', 0)
                    oceans_delta = last_entry.get('oceans', 0) - first_entry.get('oceans', 0)
                    
                    # Store the deltas for this generation
                    generation_progressions[generation]['temperature'].append(temp_delta)
                    generation_progressions[generation]['oxygen'].append(oxygen_delta)
                    generation_progressions[generation]['oceans'].append(oceans_delta)
                
                processed_games += 1
                
            except Exception as e:
                print(f"Error processing {json_file}: {e}")
                continue
    
    print(f"Processed {processed_games} out of {total_games} games")
    
    if not generation_progressions:
        print("No data found to analyze")
        return
    
    # Calculate averages for each generation
    generations = sorted(generation_progressions.keys())
    avg_temp_progression = []
    avg_oxygen_progression = []
    avg_oceans_progression = []
    
    print("\nGeneration-wise average progressions:")
    print("Gen\tTemp\tOxygen\tOceans\tGames")
    
    for gen in generations:
        temp_deltas = generation_progressions[gen]['temperature']
        oxygen_deltas = generation_progressions[gen]['oxygen']
        oceans_deltas = generation_progressions[gen]['oceans']
        
        avg_temp = np.mean(temp_deltas) if temp_deltas else 0
        avg_oxygen = np.mean(oxygen_deltas) if oxygen_deltas else 0
        avg_oceans = np.mean(oceans_deltas) if oceans_deltas else 0
        
        avg_temp_progression.append(avg_temp)
        avg_oxygen_progression.append(avg_oxygen)
        avg_oceans_progression.append(avg_oceans)
        
        print(f"{gen}\t{avg_temp:.2f}\t{avg_oxygen:.2f}\t{avg_oceans:.2f}\t{len(temp_deltas)}")
    
    # Create the matplotlib visualization
    plt.figure(figsize=(12, 8))
    
    plt.plot(generations, avg_temp_progression, linewidth=2, marker='o', label='Temperature', color='red')
    plt.plot(generations, avg_oxygen_progression, linewidth=2, marker='s', label='Oxygen', color='green')
    plt.plot(generations, avg_oceans_progression, linewidth=2, marker='^', label='Oceans', color='blue')
    
    plt.xlabel('Generation', fontsize=12)
    plt.ylabel('Average progression (steps per generation)', fontsize=12)
    plt.title(f"Terraforming Mars: Average parameter progression by generation (N={processed_games})", fontsize=14, fontweight='bold')
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3)
    
    # Set integer ticks for x-axis
    plt.xticks(generations)
    
    # Add some padding to y-axis
    y_min = min(min(avg_temp_progression), min(avg_oxygen_progression), min(avg_oceans_progression))
    y_max = max(max(avg_temp_progression), max(avg_oxygen_progression), max(avg_oceans_progression))
    y_padding = (y_max - y_min) * 0.1
    plt.ylim(y_min - y_padding, y_max + y_padding)
    
    plt.tight_layout()
    
    # Save the plot
    output_file = 'parameter_progression_analysis.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\nVisualization saved as {output_file}")
    
    # Show the plot
    plt.show()
    
    return generation_progressions

if __name__ == "__main__":
    analyze_parameter_progression()

#!/usr/bin/env python3
"""
Script to update the games.csv file with PlayerPerspective column
and populate existing rows with the correct player perspective ID.
"""

import csv
import os
from typing import List, Dict

def update_games_csv():
    """Update the games.csv file to add PlayerPerspective column"""
    csv_path = "data/processed/games.csv"
    
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} does not exist")
        return
    
    # Read existing data
    rows = []
    with open(csv_path, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        
        # Check if PlayerPerspective already exists
        if 'PlayerPerspective' in fieldnames:
            print("PlayerPerspective column already exists in the CSV file")
            return
        
        for row in reader:
            rows.append(row)
    
    # Add PlayerPerspective as the second column
    new_fieldnames = [fieldnames[0], 'PlayerPerspective'] + list(fieldnames[1:])
    
    # Update rows with PlayerPerspective
    for row in rows:
        # Set PlayerPerspective to "96014413" for games that have been scraped/parsed
        # (i.e., have ParsedAt values)
        if row.get('ParsedAt') and row['ParsedAt'].strip():
            row['PlayerPerspective'] = '96014413'
        else:
            row['PlayerPerspective'] = ''
    
    # Write updated data back to CSV
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=new_fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"Successfully updated {csv_path} with PlayerPerspective column")
    print(f"Set PlayerPerspective to '96014413' for {sum(1 for row in rows if row['PlayerPerspective'] == '96014413')} games")

if __name__ == "__main__":
    update_games_csv()

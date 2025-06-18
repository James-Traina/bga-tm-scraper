#!/usr/bin/env python3
"""
Test Players Registry
Simple test script to verify the players registry functionality
"""

import sys
import os
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from players_registry import PlayersRegistry


def test_players_registry():
    """Test the PlayersRegistry class with sample data"""
    
    # Use a test CSV file
    test_csv = 'data/processed/test_players.csv'
    
    print("=== Testing Players Registry ===")
    
    # Initialize registry
    registry = PlayersRegistry(test_csv)
    print(f"✓ Created registry: {test_csv}")
    
    # Test data - sample players
    sample_players = [
        (12345, "TestPlayer1", "Norway", 1),
        (67890, "TestPlayer2", "Germany", 2),
        (11111, "TestPlayer3", "United States", 3),
        (22222, "TestPlayer4", "Norway", 4),
        (33333, "TestPlayer5", "France", 5),
    ]
    
    # Update registry with sample data
    print("\n--- Adding sample players ---")
    stats = registry.update_players(sample_players)
    print(f"✓ Update stats: {stats}")
    
    # Test getting player count
    count = registry.get_player_count()
    print(f"✓ Total players: {count}")
    
    # Test getting top players
    top_players = registry.get_top_players(3)
    print(f"✓ Top 3 players:")
    for player in top_players:
        print(f"  #{player['ArenaRank']}: {player['PlayerName']} ({player['Country']})")
    
    # Test finding specific player
    player = registry.find_player(67890)
    if player:
        print(f"✓ Found player 67890: {player['PlayerName']}")
    else:
        print("✗ Player 67890 not found")
    
    # Test getting players by country
    norway_players = registry.get_players_by_country("Norway")
    print(f"✓ Players from Norway: {len(norway_players)}")
    for player in norway_players:
        print(f"  #{player['ArenaRank']}: {player['PlayerName']}")
    
    # Test registry statistics
    registry_stats = registry.get_registry_stats()
    print(f"✓ Registry statistics:")
    print(f"  Total players: {registry_stats['total_players']}")
    print(f"  Countries: {registry_stats['countries_count']}")
    print(f"  Rank range: {registry_stats['rank_range']}")
    print(f"  Top countries: {registry_stats['top_countries']}")
    
    # Test updating existing players (simulate rank changes)
    print("\n--- Testing updates ---")
    updated_players = [
        (12345, "TestPlayer1", "Norway", 2),  # Rank changed from 1 to 2
        (67890, "TestPlayer2_Updated", "Germany", 1),  # Name and rank changed
        (44444, "NewPlayer", "Sweden", 6),  # New player
    ]
    
    update_stats = registry.update_players(updated_players)
    print(f"✓ Update stats: {update_stats}")
    
    # Show final state
    print("\n--- Final Registry State ---")
    final_top = registry.get_top_players(10)
    for player in final_top:
        print(f"  #{player['ArenaRank']}: {player['PlayerName']} ({player['Country']})")
    
    print(f"\n✓ Test completed successfully!")
    print(f"Test file created: {test_csv}")
    
    # Clean up test file
    try:
        os.remove(test_csv)
        print("✓ Test file cleaned up")
    except:
        print("Note: Test file not cleaned up automatically")


if __name__ == '__main__':
    test_players_registry()

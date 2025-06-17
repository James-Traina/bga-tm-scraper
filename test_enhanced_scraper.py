"""
Test script for the enhanced scraper with ELO data
"""
import os
import sys
import logging
from src.parser import Parser, EloData

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_elo_parsing():
    """Test ELO data parsing with mock HTML"""
    
    # Mock table HTML with ELO data structure
    mock_table_html = """
    <html>
    <body>
        <div class="rankdetails">
            <span class="playername">TestPlayer1</span>
            <div id="winpoints_12345">1754 pts</div>
            <div class="gamerank">453</div>
            <span>+24</span>
        </div>
        <div class="rankdetails">
            <span class="playername">TestPlayer2</span>
            <div id="winpoints_67890">1680 pts</div>
            <div class="gamerank">421</div>
            <span>-12</span>
        </div>
    </body>
    </html>
    """
    
    parser = Parser()
    
    print("Testing ELO data parsing...")
    elo_data = parser.parse_elo_data(mock_table_html)
    
    print(f"Found ELO data for {len(elo_data)} players:")
    for player_name, elo in elo_data.items():
        print(f"  {player_name}:")
        print(f"    Arena Points: {elo.arena_points}")
        print(f"    Arena Points Change: {elo.arena_points_change}")
        print(f"    Game Rank: {elo.game_rank}")
        print(f"    Game Rank Change: {elo.game_rank_change}")
    
    return len(elo_data) > 0

def test_data_structures():
    """Test the new data structures"""
    
    print("\nTesting ELO data structure...")
    elo = EloData(
        arena_points=1754,
        arena_points_change=24,
        game_rank=453,
        game_rank_change=-5
    )
    
    print(f"ELO Data: {elo}")
    print("✅ ELO data structure works correctly")
    
    return True

def test_config_import():
    """Test that the new config variables can be imported"""
    
    print("\nTesting configuration import...")
    try:
        from config import TEST_TABLE_IDS, TABLE_URL_TEMPLATE, REPLAY_URL_TEMPLATE
        
        print(f"TEST_TABLE_IDS: {TEST_TABLE_IDS}")
        print(f"TABLE_URL_TEMPLATE: {TABLE_URL_TEMPLATE}")
        print(f"REPLAY_URL_TEMPLATE: {REPLAY_URL_TEMPLATE}")
        
        # Test URL template formatting
        table_id = "688769496"
        player_id = "86296239"
        
        table_url = TABLE_URL_TEMPLATE.format(table_id=table_id)
        replay_url = REPLAY_URL_TEMPLATE.format(table_id=table_id, player_id=player_id)
        
        print(f"Sample table URL: {table_url}")
        print(f"Sample replay URL: {replay_url}")
        
        print("✅ Configuration import works correctly")
        return True
        
    except ImportError as e:
        print(f"❌ Configuration import failed: {e}")
        return False

def main():
    """Run all tests"""
    
    print("=== Enhanced Scraper Test Suite ===\n")
    
    tests = [
        ("Configuration Import", test_config_import),
        ("Data Structures", test_data_structures),
        ("ELO Parsing", test_elo_parsing),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))
        
        print()
    
    # Summary
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"=== Test Summary ===")
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! The enhanced scraper is ready to use.")
        print("\nTo run the enhanced scraper:")
        print("1. Make sure you're logged into BoardGameArena")
        print("2. Run: python main.py")
        print("3. The scraper will fetch both table and replay data")
        print("4. ELO information will be included in the parsed JSON files")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

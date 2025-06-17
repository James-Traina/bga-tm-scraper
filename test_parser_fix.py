"""
Test script to verify the parser fix for player data extraction
"""
import os
import logging
from src.parser import Parser

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_parser_with_existing_data():
    """Test the parser with existing raw HTML files"""
    table_id = "688771617"
    
    # Check if raw files exist
    table_html_path = f"data/raw/table_{table_id}.html"
    replay_html_path = f"data/raw/replay_{table_id}.html"
    
    if not os.path.exists(table_html_path):
        print(f"❌ Table HTML file not found: {table_html_path}")
        return
    
    if not os.path.exists(replay_html_path):
        print(f"❌ Replay HTML file not found: {replay_html_path}")
        return
    
    print(f"✅ Found raw HTML files for game {table_id}")
    
    # Read the HTML files
    with open(table_html_path, 'r', encoding='utf-8') as f:
        table_html = f.read()
    
    with open(replay_html_path, 'r', encoding='utf-8') as f:
        replay_html = f.read()
    
    print(f"📄 Table HTML: {len(table_html)} characters")
    print(f"📄 Replay HTML: {len(replay_html)} characters")
    
    # Initialize parser
    parser = Parser()
    
    try:
        # Test the complete parsing with ELO data
        print("\n🔄 Testing parser with ELO data...")
        game_data = parser.parse_complete_game_with_elo(replay_html, table_html, table_id)
        
        # Check results
        print(f"\n📊 Parsing Results:")
        print(f"   Players found: {len(game_data.players)}")
        print(f"   Moves found: {len(game_data.moves)}")
        print(f"   ELO data included: {game_data.metadata.get('elo_data_included', False)}")
        print(f"   ELO players found: {game_data.metadata.get('elo_players_found', 0)}")
        
        # Show player details
        if game_data.players:
            print(f"\n👥 Player Details:")
            for player_id, player in game_data.players.items():
                print(f"   {player.player_name} (ID: {player_id})")
                print(f"      Corporation: {player.corporation}")
                print(f"      Final VP: {player.final_vp}")
                if player.elo_data:
                    print(f"      Game Rank: {player.elo_data.game_rank} (change: {player.elo_data.game_rank_change:+d})")
                else:
                    print(f"      ELO Data: None")
        else:
            print("❌ No players found!")
        
        # Export to test JSON
        output_path = f"data/parsed/test_game_{table_id}.json"
        parser.export_to_json(game_data, output_path)
        print(f"\n💾 Exported test results to: {output_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during parsing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Testing Parser Fix for Player Data Extraction")
    print("=" * 50)
    
    success = test_parser_with_existing_data()
    
    if success:
        print("\n✅ Parser test completed successfully!")
    else:
        print("\n❌ Parser test failed!")

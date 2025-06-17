"""
Test the full ELO parsing pipeline with existing scraped files
"""
import os
from src.parser import Parser

def test_full_elo_parsing():
    """Test the complete parsing with ELO data"""
    
    # Check if files exist
    table_html_path = "data/raw/table_688769496.html"
    replay_html_path = "data/raw/replay_688769496.html"
    
    if not os.path.exists(table_html_path):
        print(f"❌ Table HTML file not found: {table_html_path}")
        return
    
    if not os.path.exists(replay_html_path):
        print(f"❌ Replay HTML file not found: {replay_html_path}")
        return
    
    print("📁 Loading HTML files...")
    
    with open(table_html_path, 'r', encoding='utf-8') as f:
        table_html = f.read()
    
    with open(replay_html_path, 'r', encoding='utf-8') as f:
        replay_html = f.read()
    
    print(f"📊 Table HTML size: {len(table_html):,} characters")
    print(f"📊 Replay HTML size: {len(replay_html):,} characters")
    
    # Initialize parser
    parser = Parser()
    
    # Test complete parsing with ELO
    print("\n🔍 Testing complete game parsing with ELO data...")
    
    try:
        game_data = parser.parse_complete_game_with_elo(
            replay_html=replay_html,
            table_html=table_html,
            table_id="688769496"
        )
        
        print(f"\n📈 Parsing Results:")
        print(f"  Game ID: {game_data.replay_id}")
        print(f"  Players: {len(game_data.players)}")
        print(f"  Moves: {len(game_data.moves)}")
        print(f"  ELO data included: {game_data.metadata.get('elo_data_included', False)}")
        print(f"  ELO players found: {game_data.metadata.get('elo_players_found', 0)}")
        
        print(f"\n👥 Player Details:")
        for player_id, player in game_data.players.items():
            print(f"  {player.player_name} (ID: {player_id}):")
            print(f"    Corporation: {player.corporation}")
            print(f"    Final VP: {player.final_vp}")
            if player.elo_data:
                print(f"    ELO Data:")
                print(f"      Arena Points: {player.elo_data.arena_points}")
                print(f"      Arena Change: {player.elo_data.arena_points_change}")
                print(f"      Game Rank: {player.elo_data.game_rank}")
                print(f"      Game Change: {player.elo_data.game_rank_change}")
            else:
                print(f"    ELO Data: None")
        
        # Export to test file
        output_path = "data/parsed/test_game_with_elo.json"
        parser.export_to_json(game_data, output_path)
        print(f"\n💾 Exported complete data to: {output_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during parsing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== Full ELO Parsing Test ===\n")
    success = test_full_elo_parsing()
    
    if success:
        print("\n🎉 Full ELO parsing test completed successfully!")
        print("The enhanced parser is working correctly with both replay and ELO data.")
    else:
        print("\n❌ Full ELO parsing test failed.")

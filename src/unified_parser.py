"""
Unified Terraforming Mars game log parser for BoardGameArena replays
Consolidates all parsing logic into a single comprehensive parser
"""
import re
import json
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from bs4 import BeautifulSoup, Tag
import logging

logger = logging.getLogger(__name__)

@dataclass
class GameState:
    """Represents the game state at a specific point in time"""
    move_index: int
    generation: int
    temperature: int
    oxygen: int
    oceans: int
    player_resources: Dict[str, Dict[str, int]]  # player_id -> resource -> amount
    player_production: Dict[str, Dict[str, int]]  # player_id -> resource -> production
    player_vp: Dict[str, Dict[str, Any]]  # player_id -> VP breakdown
    milestones: Dict[str, Dict[str, Any]]  # milestone_name -> details
    awards: Dict[str, Dict[str, Any]]  # award_name -> details
    
    def __post_init__(self):
        if self.player_resources is None:
            self.player_resources = {}
        if self.player_production is None:
            self.player_production = {}
        if self.player_vp is None:
            self.player_vp = {}
        if self.milestones is None:
            self.milestones = {}
        if self.awards is None:
            self.awards = {}

@dataclass
class Move:
    """Represents a single move in the game"""
    move_number: int
    timestamp: str
    player_id: str
    player_name: str
    action_type: str
    description: str
    
    # Detailed action data
    card_played: Optional[str] = None
    card_cost: Optional[int] = None
    tile_placed: Optional[str] = None
    tile_location: Optional[str] = None
    resource_changes: Dict[str, int] = None
    production_changes: Dict[str, int] = None
    parameter_changes: Dict[str, int] = None  # temperature, oxygen, oceans
    
    # Game state after this move
    game_state: Optional[GameState] = None
    
    def __post_init__(self):
        if self.resource_changes is None:
            self.resource_changes = {}
        if self.production_changes is None:
            self.production_changes = {}
        if self.parameter_changes is None:
            self.parameter_changes = {}

@dataclass
class Player:
    """Represents a player in the game"""
    player_id: str
    player_name: str
    corporation: str
    final_vp: int
    final_tr: int
    final_resources: Dict[str, int]
    final_production: Dict[str, int]
    vp_breakdown: Dict[str, Any]
    cards_played: List[str]
    milestones_claimed: List[str]
    awards_funded: List[str]

@dataclass
class UnifiedGameData:
    """Complete game data structure"""
    # Game metadata
    replay_id: str
    game_date: str
    game_duration: str
    winner: str
    
    # Players
    players: Dict[str, Player]  # player_id -> Player
    
    # All moves with game states
    moves: List[Move]
    
    # Final game state
    final_state: GameState
    
    # Game progression data
    vp_progression: List[Dict[str, Any]]
    parameter_progression: List[Dict[str, Any]]
    
    # Analysis metadata
    metadata: Dict[str, Any]

class UnifiedTMParser:
    """Unified parser that consolidates all parsing logic"""
    
    def __init__(self):
        self.resource_patterns = {
            'M€': r'<div class="token_img tracker_m"[^>]*title="M€"[^>]*></div>',
            'steel': r'<div class="token_img tracker_s"[^>]*title="Steel"[^>]*></div>',
            'titanium': r'<div class="token_img tracker_u"[^>]*title="Titanium"[^>]*></div>',
            'plant': r'<div class="token_img tracker_p"[^>]*title="Plant"[^>]*></div>',
            'energy': r'<div class="token_img tracker_e"[^>]*title="Energy"[^>]*></div>',
            'heat': r'<div class="token_img tracker_h"[^>]*title="Heat"[^>]*></div>',
            'TR': r'<div class="token_img tracker_tr"[^>]*title="TR"[^>]*></div>',
        }
        
        self.production_patterns = {
            'M€_production': r'<div class="token_img tracker_pm"[^>]*title="M€ Production"[^>]*></div>',
            'steel_production': r'<div class="token_img tracker_ps"[^>]*title="Steel Production"[^>]*></div>',
            'titanium_production': r'<div class="token_img tracker_pu"[^>]*title="Titanium Production"[^>]*></div>',
            'plant_production': r'<div class="token_img tracker_pp"[^>]*title="Plant Production"[^>]*></div>',
            'energy_production': r'<div class="token_img tracker_pe"[^>]*title="Energy Production"[^>]*></div>',
            'heat_production': r'<div class="token_img tracker_ph"[^>]*title="Heat Production"[^>]*></div>',
        }
    
    def parse_complete_game(self, html_content: str, replay_id: str) -> UnifiedGameData:
        """Parse a complete game and return unified data structure"""
        logger.info(f"Starting unified parsing for game {replay_id}")
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract basic game info
        players_info = self._extract_players_info(soup, html_content)
        
        # Extract all moves with detailed parsing
        moves = self._extract_all_moves(soup, players_info)
        
        # Extract VP progression throughout the game
        vp_progression = self._extract_vp_progression(html_content)
        
        # Build game states for each move
        moves_with_states = self._build_game_states(moves, vp_progression, players_info)
        
        # Extract parameter progression
        parameter_progression = self._extract_parameter_progression(moves_with_states)
        
        # Build final game state
        final_state = moves_with_states[-1].game_state if moves_with_states else GameState(
            move_index=0, generation=1, temperature=-30, oxygen=0, oceans=0,
            player_resources={}, player_production={}, player_vp={},
            milestones={}, awards={}
        )
        
        # Determine winner
        winner = self._determine_winner(players_info)
        
        # Extract game metadata
        metadata = self._extract_metadata(soup, html_content, moves_with_states)
        
        # Create unified game data
        game_data = UnifiedGameData(
            replay_id=replay_id,
            game_date=self._extract_game_date(soup),
            game_duration=self._calculate_game_duration(moves_with_states),
            winner=winner,
            players=players_info,
            moves=moves_with_states,
            final_state=final_state,
            vp_progression=vp_progression,
            parameter_progression=parameter_progression,
            metadata=metadata
        )
        
        logger.info(f"Unified parsing complete for game {replay_id}: {len(moves_with_states)} moves, {len(players_info)} players")
        return game_data
    
    def _extract_players_info(self, soup: BeautifulSoup, html_content: str) -> Dict[str, Player]:
        """Extract comprehensive player information"""
        # Get player names
        player_names = []
        player_elements = soup.find_all('span', class_='playername')
        for elem in player_elements:
            player_name = elem.get_text().strip()
            if player_name and player_name not in player_names:
                player_names.append(player_name)
        
        # Get player ID mapping
        player_id_map = self._extract_player_id_mapping(html_content, player_names)
        
        # Get VP data for final scores
        vp_data = self._extract_vp_data_from_html(html_content)
        
        # Get corporations
        corporations = self._extract_corporations(soup)
        
        players = {}
        for player_name in player_names:
            player_id = player_id_map.get(player_name, f"unknown_{len(players)}")
            
            # Get final VP and breakdown
            final_vp = 0
            vp_breakdown = {}
            if player_id in vp_data:
                final_vp = vp_data[player_id].get('total', 0)
                vp_breakdown = vp_data[player_id].get('total_details', {})
            
            players[player_id] = Player(
                player_id=player_id,
                player_name=player_name,
                corporation=corporations.get(player_name, 'Unknown'),
                final_vp=final_vp,
                final_tr=vp_breakdown.get('tr', 20),
                final_resources={},  # Will be populated from moves
                final_production={},  # Will be populated from moves
                vp_breakdown=vp_breakdown,
                cards_played=[],  # Will be populated from moves
                milestones_claimed=[],  # Will be populated from moves
                awards_funded=[]  # Will be populated from moves
            )
        
        return players
    
    def _extract_all_moves(self, soup: BeautifulSoup, players_info: Dict[str, Player]) -> List[Move]:
        """Extract all moves with detailed information"""
        moves = []
        move_divs = soup.find_all('div', class_='replaylogs_move')
        
        # Create reverse lookup for player names to IDs
        name_to_id = {player.player_name: player_id for player_id, player in players_info.items()}
        
        for move_div in move_divs:
            move = self._parse_single_move_detailed(move_div, name_to_id)
            if move:
                moves.append(move)
                
                # Update player data based on move
                self._update_player_data_from_move(move, players_info)
        
        return moves
    
    def _parse_single_move_detailed(self, move_div: Tag, name_to_id: Dict[str, str]) -> Optional[Move]:
        """Parse a single move with comprehensive detail extraction"""
        try:
            # Extract move number and timestamp
            move_info = move_div.find('div', class_='smalltext')
            if not move_info:
                return None
            
            move_text = move_info.get_text()
            move_match = re.search(r'Move (\d+)', move_text)
            if not move_match:
                return None
            
            move_number = int(move_match.group(1))
            
            # Extract timestamp
            timestamp_match = re.search(r'(\d{1,2}:\d{2}:\d{2})', move_text)
            timestamp = timestamp_match.group(1) if timestamp_match else ""
            
            # Extract all log entries
            log_entries = move_div.find_all('div', class_='gamelogreview')
            if not log_entries:
                return None
            
            # Combine descriptions
            descriptions = [entry.get_text().strip() for entry in log_entries]
            full_description = ' | '.join(descriptions)
            
            # Determine player
            player_name, player_id = self._determine_move_player(log_entries, full_description, name_to_id)
            
            # Extract action details
            action_type = self._classify_action_type(log_entries, full_description)
            card_played = self._extract_card_played(log_entries)
            card_cost = self._extract_card_cost(log_entries)
            tile_placed, tile_location = self._extract_tile_placement(log_entries)
            
            # Extract resource and production changes
            resource_changes = self._extract_resource_changes_detailed(log_entries)
            production_changes = self._extract_production_changes_detailed(log_entries)
            parameter_changes = self._extract_parameter_changes_detailed(log_entries)
            
            move = Move(
                move_number=move_number,
                timestamp=timestamp,
                player_id=player_id,
                player_name=player_name,
                action_type=action_type,
                description=full_description,
                card_played=card_played,
                card_cost=card_cost,
                tile_placed=tile_placed,
                tile_location=tile_location,
                resource_changes=resource_changes,
                production_changes=production_changes,
                parameter_changes=parameter_changes
            )
            
            return move
            
        except Exception as e:
            logger.error(f"Error parsing move: {e}")
            return None
    
    def _determine_move_player(self, log_entries: List[Tag], description: str, name_to_id: Dict[str, str]) -> Tuple[str, str]:
        """Determine which player made this move"""
        # Look for explicit player mentions
        for entry in log_entries:
            text = entry.get_text()
            
            # Check for player names in the text
            for player_name in name_to_id.keys():
                if player_name in text and any(verb in text for verb in ['plays', 'pays', 'gains', 'increases', 'reduces', 'places', 'chooses']):
                    return player_name, name_to_id[player_name]
            
            # Handle "You" references - would need context to resolve properly
            if text.startswith('You '):
                # For now, return as "You" - could be improved with more context
                return "You", "you"
        
        return "Unknown", "unknown"
    
    def _classify_action_type(self, log_entries: List[Tag], description: str) -> str:
        """Classify the type of action"""
        if 'plays card' in description:
            return 'play_card'
        elif any(phrase in description for phrase in ['places City', 'places Forest', 'places Ocean']):
            return 'place_tile'
        elif 'standard project' in description:
            return 'standard_project'
        elif 'passes' in description:
            return 'pass'
        elif 'Convert heat into temperature' in description:
            return 'convert_heat'
        elif 'claims milestone' in description:
            return 'claim_milestone'
        elif 'funds' in description and 'award' in description:
            return 'fund_award'
        elif 'activates' in description:
            return 'activate_card'
        elif 'New generation' in description:
            return 'new_generation'
        elif 'draft' in description:
            return 'draft_card'
        elif 'Buy Card' in description:
            return 'buy_card'
        else:
            return 'other'
    
    def _extract_card_played(self, log_entries: List[Tag]) -> Optional[str]:
        """Extract the name of the card played"""
        for entry in log_entries:
            text = entry.get_text()
            if 'plays card' in text:
                card_link = entry.find('div', class_='card_hl_tt')
                if card_link:
                    return card_link.get_text().strip()
                else:
                    # Fallback: extract from text
                    match = re.search(r'plays card (.+)', text)
                    if match:
                        return match.group(1).strip()
        return None
    
    def _extract_card_cost(self, log_entries: List[Tag]) -> Optional[int]:
        """Extract the cost of the card played"""
        for entry in log_entries:
            text = entry.get_text()
            if 'pays' in text and 'M€' in text:
                # Look for cost pattern
                cost_match = re.search(r'pays (\d+)', text)
                if cost_match:
                    return int(cost_match.group(1))
        return None
    
    def _extract_tile_placement(self, log_entries: List[Tag]) -> Tuple[Optional[str], Optional[str]]:
        """Extract tile placement information"""
        for entry in log_entries:
            text = entry.get_text()
            if 'places' in text:
                if 'places City on' in text:
                    tile_type = "City"
                    location_match = re.search(r'places City on (.+)', text)
                elif 'places Forest on' in text:
                    tile_type = "Forest"
                    location_match = re.search(r'places Forest on (.+)', text)
                elif 'places Ocean on' in text:
                    tile_type = "Ocean"
                    location_match = re.search(r'places Ocean on (.+)', text)
                else:
                    continue
                
                location = location_match.group(1).strip() if location_match else "Unknown"
                return tile_type, location
        
        return None, None
    
    def _extract_resource_changes_detailed(self, log_entries: List[Tag]) -> Dict[str, int]:
        """Extract detailed resource changes"""
        changes = {}
        
        for entry in log_entries:
            html_content = str(entry)
            
            # Pattern for gains/pays with number before resource
            gain_pattern = r'gains (\d+) <div class="token_img tracker_(\w+)"[^>]*title="([^"]*)"[^>]*></div>'
            pay_pattern = r'pays (\d+) <div class="token_img tracker_(\w+)"[^>]*title="([^"]*)"[^>]*></div>'
            
            # Pattern for gains/pays with number after resource
            gain_after_pattern = r'gains <div class="token_img tracker_(\w+)"[^>]*title="([^"]*)"[^>]*></div>(\d+)'
            pay_after_pattern = r'pays <div class="token_img tracker_(\w+)"[^>]*title="([^"]*)"[^>]*></div>(\d+)'
            
            patterns = [
                (gain_pattern, 1),
                (pay_pattern, -1),
                (gain_after_pattern, 1),
                (pay_after_pattern, -1)
            ]
            
            for pattern, sign in patterns:
                matches = re.finditer(pattern, html_content)
                for match in matches:
                    if pattern in [gain_pattern, pay_pattern]:
                        amount = int(match.group(1)) * sign
                        tracker = match.group(2)
                        title = match.group(3)
                    else:
                        tracker = match.group(1)
                        title = match.group(2)
                        amount = int(match.group(3)) * sign
                    
                    resource_name = self._map_tracker_to_resource(tracker, title)
                    if 'Production' not in title:  # Only count non-production changes here
                        changes[resource_name] = changes.get(resource_name, 0) + amount
        
        return changes
    
    def _extract_production_changes_detailed(self, log_entries: List[Tag]) -> Dict[str, int]:
        """Extract detailed production changes"""
        changes = {}
        
        for entry in log_entries:
            html_content = str(entry)
            
            # Production increase/decrease patterns
            increase_prod_pattern = r'increases <div class="token_img tracker_(\w+)"[^>]*title="([^"]*)"[^>]*></div> by (\d+)'
            reduce_prod_pattern = r'reduces <div class="token_img tracker_(\w+)"[^>]*title="([^"]*)"[^>]*></div> by (\d+)'
            
            patterns = [
                (increase_prod_pattern, 1),
                (reduce_prod_pattern, -1)
            ]
            
            for pattern, sign in patterns:
                matches = re.finditer(pattern, html_content)
                for match in matches:
                    tracker = match.group(1)
                    title = match.group(2)
                    amount = int(match.group(3)) * sign
                    
                    if 'Production' in title:
                        resource_name = self._map_tracker_to_resource(tracker, title)
                        changes[resource_name] = changes.get(resource_name, 0) + amount
        
        return changes
    
    def _extract_parameter_changes_detailed(self, log_entries: List[Tag]) -> Dict[str, int]:
        """Extract terraforming parameter changes"""
        changes = {}
        
        for entry in log_entries:
            html_content = str(entry)
            
            # Temperature changes
            temp_match = re.search(r'increases.*Temperature.*by \d+ step.*to a value of (-?\d+)', html_content)
            if temp_match:
                changes['temperature'] = int(temp_match.group(1))
            
            # Oxygen changes
            oxygen_match = re.search(r'increases.*Oxygen Level.*by \d+ step.*to a value of (\d+)', html_content)
            if oxygen_match:
                changes['oxygen'] = int(oxygen_match.group(1))
            
            # Ocean changes
            ocean_match = re.search(r'increases.*Oceans.*by \d+ step.*to a value of (\d+)', html_content)
            if ocean_match:
                changes['oceans'] = int(ocean_match.group(1))
        
        return changes
    
    def _map_tracker_to_resource(self, tracker: str, title: str) -> str:
        """Map tracker code to resource name"""
        mapping = {
            'm': 'M€',
            's': 'Steel',
            'u': 'Titanium',
            'p': 'Plant',
            'e': 'Energy',
            'h': 'Heat',
            'tr': 'TR',
            'pm': 'M€',
            'ps': 'Steel',
            'pu': 'Titanium',
            'pp': 'Plant',
            'pe': 'Energy',
            'ph': 'Heat',
        }
        
        return mapping.get(tracker, title.replace(' Production', ''))
    
    def _update_player_data_from_move(self, move: Move, players_info: Dict[str, Player]):
        """Update player data based on move information"""
        if move.player_id not in players_info:
            return
        
        player = players_info[move.player_id]
        
        # Track cards played
        if move.card_played:
            player.cards_played.append(move.card_played)
        
        # Track milestones claimed
        if move.action_type == 'claim_milestone':
            milestone_match = re.search(r'claims milestone (\w+)', move.description)
            if milestone_match:
                player.milestones_claimed.append(milestone_match.group(1))
        
        # Track awards funded
        if move.action_type == 'fund_award':
            award_match = re.search(r'funds (\w+) award', move.description)
            if award_match:
                player.awards_funded.append(award_match.group(1))
    
    def _build_game_states(self, moves: List[Move], vp_progression: List[Dict[str, Any]], players_info: Dict[str, Player]) -> List[Move]:
        """Build game states for each move"""
        # Initialize tracking variables
        current_temp = -30
        current_oxygen = 0
        current_oceans = 0
        current_generation = 1
        
        # Track resources and production for each player
        player_resources = {pid: {'M€': 0, 'Steel': 0, 'Titanium': 0, 'Plant': 0, 'Energy': 0, 'Heat': 0, 'TR': 20} 
                          for pid in players_info.keys()}
        player_production = {pid: {'M€': 0, 'Steel': 0, 'Titanium': 0, 'Plant': 0, 'Energy': 0, 'Heat': 0} 
                           for pid in players_info.keys()}
        
        # Process each move and build game state
        for i, move in enumerate(moves):
            # Update parameters
            if 'temperature' in move.parameter_changes:
                current_temp = move.parameter_changes['temperature']
            if 'oxygen' in move.parameter_changes:
                current_oxygen = move.parameter_changes['oxygen']
            if 'oceans' in move.parameter_changes:
                current_oceans = move.parameter_changes['oceans']
            
            # Update generation
            if 'New generation' in move.description:
                gen_match = re.search(r'New generation (\d+)', move.description)
                if gen_match:
                    current_generation = int(gen_match.group(1))
            
            # Update player resources and production
            if move.player_id in player_resources:
                for resource, change in move.resource_changes.items():
                    player_resources[move.player_id][resource] = player_resources[move.player_id].get(resource, 0) + change
                
                for resource, change in move.production_changes.items():
                    player_production[move.player_id][resource] = player_production[move.player_id].get(resource, 0) + change
            
            # Get VP data for this move
            move_vp_data = {}
            if i < len(vp_progression):
                vp_entry = vp_progression[i]
                move_vp_data = vp_entry.get('vp_data', {})
            
            # Create game state
            game_state = GameState(
                move_index=i,
                generation=current_generation,
                temperature=current_temp,
                oxygen=current_oxygen,
                oceans=current_oceans,
                player_resources=dict(player_resources),
                player_production=dict(player_production),
                player_vp=move_vp_data,
                milestones={},  # Could be enhanced to track milestone states
                awards={}  # Could be enhanced to track award states
            )
            
            move.game_state = game_state
        
        return moves
    
    def _extract_vp_progression(self, html_content: str) -> List[Dict[str, Any]]:
        """Extract VP progression throughout the game"""
        # Use the same pattern as the existing VP progression extraction
        pattern = r'"data":\{((?:"(\d+)":\{[^}]*"total":(\d+)[^}]*\}[,\s]*)+)\}'
        
        matches = re.findall(pattern, html_content, re.DOTALL)
        vp_progression = []
        
        for i, match_data in enumerate(matches):
            try:
                json_str = "{" + match_data[0] + "}"
                
                # Fix JSON structure if needed
                brace_count = match_data[0].count('{') - match_data[0].count('}')
                if brace_count > 0:
                    json_str = "{" + match_data[0] + '}' * brace_count + "}"
                
                vp_data = json.loads(json_str)
                
                # Calculate combined total
                combined_total = sum(data.get('total', 0) for data in vp_data.values())
                
                vp_entry = {
                    'move_index': i,
                    'combined_total': combined_total,
                    'vp_data': vp_data
                }
                
                vp_progression.append(vp_entry)
                
            except json.JSONDecodeError:
                continue
        
        return vp_progression
    
    def _extract_parameter_progression(self, moves: List[Move]) -> List[Dict[str, Any]]:
        """Extract parameter progression from moves"""
        progression = []
        
        for move in moves:
            if move.game_state:
                progression.append({
                    'move_index': move.game_state.move_index,
                    'generation': move.game_state.generation,
                    'temperature': move.game_state.temperature,
                    'oxygen': move.game_state.oxygen,
                    'oceans': move.game_state.oceans
                })
        
        return progression
    
    def _extract_vp_data_from_html(self, html_content: str) -> Dict[str, Any]:
        """Extract VP data from HTML - reusing existing logic"""
        pattern = r'"data":\{("(\d+)":\{.*?"total":(\d+).*?\}.*?"(\d+)":\{.*?"total":(\d+).*?\})\}'
        
        matches = re.findall(pattern, html_content, re.DOTALL)
        
        if matches:
            best_match = None
            best_total = 0
            
            for match_data, player1_id, total1, player2_id, total2 in matches:
                combined_total = int(total1) + int(total2)
                if combined_total > best_total:
                    best_total = combined_total
                    best_match = match_data
            
            if best_match:
                try:
                    json_str = "{" + best_match + "}"
                    brace_count = best_match.count('{') - best_match.count('}')
                    if brace_count > 0:
                        json_str = "{" + best_match + '}' * brace_count + "}"
                    
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    pass
        
        return {}
    
    def _extract_player_id_mapping(self, html_content: str, player_names: List[str]) -> Dict[str, str]:
        """Extract player ID mapping - reusing existing logic"""
        player_id_map = {}
        
        # Get valid player IDs from VP data
        vp_data = self._extract_vp_data_from_html(html_content)
        valid_player_ids = set(vp_data.keys())
        
        # Look for player board elements that might contain the mapping
        for player in player_names:
            patterns = [
                rf'{re.escape(player)}[^0-9]*(\d{{8,}})',
                rf'(\d{{8,}})[^a-zA-Z]*{re.escape(player)}',
                rf'player[^>]*{re.escape(player)}[^0-9]*(\d{{8,}})',
                rf'(\d{{8,}})[^>]*player[^>]*{re.escape(player)}',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                if matches:
                    for match in matches:
                        if len(match) >= 8 and match in valid_player_ids:
                            player_id_map[player] = match
                            break
                    
                    if player in player_id_map:
                        break
        
        # Fallback mapping if HTML-based mapping fails
        if len(player_id_map) < len(player_names):
            player_ids = sorted(valid_player_ids)
            for i, player in enumerate(player_names):
                if player not in player_id_map and i < len(player_ids):
                    player_id_map[player] = player_ids[i]
        
        return player_id_map
    
    def _extract_corporations(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract corporation assignments"""
        corporations = {}
        
        # Look for corporation mentions in the log
        log_entries = soup.find_all('div', class_='gamelogreview')
        for entry in log_entries:
            text = entry.get_text()
            if 'chooses corporation' in text:
                # Pattern: "PlayerName chooses corporation CorporationName"
                match = re.search(r'(\w+) chooses corporation (.+)', text)
                if match:
                    player_name = match.group(1)
                    corp_name = match.group(2).strip()
                    corporations[player_name] = corp_name
        
        return corporations
    
    def _determine_winner(self, players_info: Dict[str, Player]) -> str:
        """Determine the winner based on final VP"""
        if not players_info:
            return "Unknown"
        
        max_vp = max(player.final_vp for player in players_info.values())
        winners = [player.player_name for player in players_info.values() if player.final_vp == max_vp]
        
        return winners[0] if winners else "Unknown"
    
    def _extract_game_date(self, soup: BeautifulSoup) -> str:
        """Extract game date from HTML"""
        # Look for date information in the HTML
        # This would need to be customized based on BGA's HTML structure
        return datetime.now().strftime("%Y-%m-%d")
    
    def _calculate_game_duration(self, moves: List[Move]) -> str:
        """Calculate game duration from moves"""
        if not moves or len(moves) < 2:
            return "Unknown"
        
        try:
            start_time = moves[0].timestamp
            end_time = moves[-1].timestamp
            
            # Parse timestamps (assuming HH:MM:SS format)
            start_parts = start_time.split(':')
            end_parts = end_time.split(':')
            
            start_seconds = int(start_parts[0]) * 3600 + int(start_parts[1]) * 60 + int(start_parts[2])
            end_seconds = int(end_parts[0]) * 3600 + int(end_parts[1]) * 60 + int(end_parts[2])
            
            duration_seconds = end_seconds - start_seconds
            if duration_seconds < 0:  # Handle day rollover
                duration_seconds += 24 * 3600
            
            hours = duration_seconds // 3600
            minutes = (duration_seconds % 3600) // 60
            
            return f"{hours:02d}:{minutes:02d}"
            
        except (ValueError, IndexError):
            return "Unknown"
    
    def _extract_metadata(self, soup: BeautifulSoup, html_content: str, moves: List[Move]) -> Dict[str, Any]:
        """Extract metadata about the parsing process"""
        return {
            'parsed_at': datetime.now().isoformat(),
            'total_moves': len(moves),
            'html_length': len(html_content),
            'parser_version': '1.0.0',
            'features_extracted': [
                'moves', 'game_states', 'vp_progression', 
                'parameter_progression', 'player_data'
            ]
        }

    def export_to_json(self, game_data: UnifiedGameData, output_path: str):
        """Export unified game data to JSON"""
        # Convert dataclasses to dictionaries for JSON serialization
        def convert_to_dict(obj):
            if hasattr(obj, '__dict__'):
                return {k: convert_to_dict(v) for k, v in obj.__dict__.items()}
            elif isinstance(obj, list):
                return [convert_to_dict(item) for item in obj]
            elif isinstance(obj, dict):
                return {k: convert_to_dict(v) for k, v in obj.items()}
            else:
                return obj
        
        data_dict = convert_to_dict(game_data)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data_dict, f, indent=2, ensure_ascii=False)

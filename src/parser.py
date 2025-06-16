"""
Terraforming Mars game log parser for BoardGameArena replays
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
class ResourceChange:
    """Represents a change in resources"""
    resource_type: str  # 'M€', 'steel', 'titanium', 'plant', 'energy', 'heat', 'TR', etc.
    amount: int
    production: bool = False  # True if this is a production change
    
@dataclass
class CardPlay:
    """Represents a card being played"""
    card_name: str
    card_id: Optional[str] = None
    cost: Optional[int] = None
    cost_resources: List[ResourceChange] = None
    immediate_effects: List[ResourceChange] = None
    
    def __post_init__(self):
        if self.cost_resources is None:
            self.cost_resources = []
        if self.immediate_effects is None:
            self.immediate_effects = []

@dataclass
class TilePlace:
    """Represents a tile placement"""
    tile_type: str  # 'City', 'Forest', 'Ocean', etc.
    location: str   # e.g., 'Tharsis Hex 5,5'
    adjacency_bonus: List[ResourceChange] = None
    
    def __post_init__(self):
        if self.adjacency_bonus is None:
            self.adjacency_bonus = []

@dataclass
class TMMove:
    """Represents a single move in the game"""
    move_number: int
    timestamp: str
    player: str
    action_type: str  # 'play_card', 'place_tile', 'convert_resources', 'pass', etc.
    description: str
    
    # Specific action data
    card_play: Optional[CardPlay] = None
    tile_place: Optional[TilePlace] = None
    resource_changes: List[ResourceChange] = None
    parameter_changes: Dict[str, int] = None  # temperature, oxygen, oceans
    
    # Raw data for debugging
    raw_html: str = ""
    
    def __post_init__(self):
        if self.resource_changes is None:
            self.resource_changes = []
        if self.parameter_changes is None:
            self.parameter_changes = {}

@dataclass
class MilestoneAward:
    """Represents milestone or award information"""
    name: str
    claimed_by: Optional[str] = None
    funded_by: Optional[str] = None
    vp_value: int = 0
    standings: Dict[str, int] = None  # player -> position for awards
    
    def __post_init__(self):
        if self.standings is None:
            self.standings = {}

@dataclass
class VictoryPoints:
    """Represents victory point breakdown"""
    tr_rating: int = 20
    milestones: Dict[str, int] = None  # milestone_name -> VP
    awards: Dict[str, int] = None      # award_name -> VP
    cards: Dict[str, int] = None       # card_name -> VP
    board_tiles: int = 0               # forests + cities
    total: int = 0
    
    def __post_init__(self):
        if self.milestones is None:
            self.milestones = {}
        if self.awards is None:
            self.awards = {}
        if self.cards is None:
            self.cards = {}

@dataclass
class TMGameState:
    """Represents the current state of the game"""
    generation: int = 1
    current_player: str = ""
    temperature: int = -30
    oxygen: int = 0
    oceans: int = 0
    
    # Player resources (simplified - could be expanded)
    player_resources: Dict[str, Dict[str, int]] = None
    
    # VP tracking
    milestones: Dict[str, MilestoneAward] = None
    awards: Dict[str, MilestoneAward] = None
    player_vp: Dict[str, VictoryPoints] = None
    
    def __post_init__(self):
        if self.player_resources is None:
            self.player_resources = {}
        if self.milestones is None:
            self.milestones = {}
        if self.awards is None:
            self.awards = {}
        if self.player_vp is None:
            self.player_vp = {}

@dataclass
class TMGame:
    """Represents a complete Terraforming Mars game"""
    replay_id: str
    players: List[str]
    corporations: Dict[str, str]  # player -> corporation
    moves: List[TMMove]
    final_state: TMGameState
    metadata: Dict[str, Any]
    
    def __post_init__(self):
        if self.corporations is None:
            self.corporations = {}
        if self.moves is None:
            self.moves = []
        if self.metadata is None:
            self.metadata = {}

class TMGameParser:
    """Parser for Terraforming Mars game logs from BoardGameArena"""
    
    def __init__(self):
        self.resource_patterns = {
            'M€': r'<div class="token_img tracker_m"[^>]*title="M€"[^>]*></div>',
            'steel': r'<div class="token_img tracker_s"[^>]*title="Steel"[^>]*></div>',
            'titanium': r'<div class="token_img tracker_u"[^>]*title="Titanium"[^>]*></div>',
            'plant': r'<div class="token_img tracker_p"[^>]*title="Plant"[^>]*></div>',
            'energy': r'<div class="token_img tracker_e"[^>]*title="Energy"[^>]*></div>',
            'heat': r'<div class="token_img tracker_h"[^>]*title="Heat"[^>]*></div>',
            'TR': r'<div class="token_img tracker_tr"[^>]*title="TR"[^>]*></div>',
            'temperature': r'<div class="token_img tracker_t"[^>]*title="Temperature"[^>]*></div>',
            'oxygen': r'<div class="token_img tracker_o"[^>]*title="Oxygen Level"[^>]*></div>',
            'oceans': r'<div class="token_img tracker_w"[^>]*title="Oceans"[^>]*></div>',
        }
        
        self.production_patterns = {
            'M€_production': r'<div class="token_img tracker_pm"[^>]*title="M€ Production"[^>]*></div>',
            'steel_production': r'<div class="token_img tracker_ps"[^>]*title="Steel Production"[^>]*></div>',
            'titanium_production': r'<div class="token_img tracker_pu"[^>]*title="Titanium Production"[^>]*></div>',
            'plant_production': r'<div class="token_img tracker_pp"[^>]*title="Plant Production"[^>]*></div>',
            'energy_production': r'<div class="token_img tracker_pe"[^>]*title="Energy Production"[^>]*></div>',
            'heat_production': r'<div class="token_img tracker_ph"[^>]*title="Heat Production"[^>]*></div>',
        }
    
    def parse_game_from_html(self, html_content: str, replay_id: str) -> TMGame:
        """Parse a complete game from HTML content"""
        logger.info(f"Parsing game {replay_id}")
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract basic game info
        players = self._extract_players(soup)
        corporations = self._extract_corporations(soup)
        
        # Extract moves
        moves = self._extract_moves(soup)
        
        # Extract VP information
        milestones, awards = self._extract_milestones_and_awards(soup)
        
        # Build final game state with VP tracking
        final_state = self._build_final_state(moves, players, soup)
        final_state.milestones = milestones
        final_state.awards = awards
        
        # Calculate final VP for each player
        final_state.player_vp = self._calculate_victory_points(soup, players, moves, milestones, awards)
        
        # Create metadata
        metadata = {
            'parsed_at': datetime.now().isoformat(),
            'total_moves': len(moves),
            'html_length': len(html_content),
            'milestones_found': len(milestones),
            'awards_found': len(awards)
        }
        
        game = TMGame(
            replay_id=replay_id,
            players=players,
            corporations=corporations,
            moves=moves,
            final_state=final_state,
            metadata=metadata
        )
        
        logger.info(f"Parsed game {replay_id}: {len(moves)} moves, {len(players)} players, {len(milestones)} milestones, {len(awards)} awards")
        return game
    
    def _extract_players(self, soup: BeautifulSoup) -> List[str]:
        """Extract player names from the HTML"""
        players = []
        player_elements = soup.find_all('span', class_='playername')
        
        for elem in player_elements:
            player_name = elem.get_text().strip()
            if player_name and player_name not in players:
                players.append(player_name)
        
        return players
    
    def _extract_corporations(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract corporation choices for each player"""
        corporations = {}
        
        # Look for corporation choice messages
        move_divs = soup.find_all('div', class_='replaylogs_move')
        
        for move_div in move_divs:
            log_entries = move_div.find_all('div', class_='gamelogreview')
            for entry in log_entries:
                text = entry.get_text()
                if 'chooses corporation' in text or 'choose corporation' in text:
                    # Extract player and corporation name
                    if 'chooses corporation' in text:
                        parts = text.split('chooses corporation')
                        if len(parts) == 2:
                            player = parts[0].strip()
                            corporation = parts[1].strip()
                            corporations[player] = corporation
                    elif 'choose corporation' in text:
                        # Handle "You choose corporation X" format
                        parts = text.split('choose corporation')
                        if len(parts) == 2:
                            corporation = parts[1].strip()
                            # Need to determine which player this is - could be tricky
                            # For now, we'll handle this in a more sophisticated way later
        
        return corporations
    
    def _extract_moves(self, soup: BeautifulSoup) -> List[TMMove]:
        """Extract all moves from the game"""
        moves = []
        move_divs = soup.find_all('div', class_='replaylogs_move')
        
        for move_div in move_divs:
            move = self._parse_single_move(move_div)
            if move:
                moves.append(move)
        
        return moves
    
    def _parse_single_move(self, move_div: Tag) -> Optional[TMMove]:
        """Parse a single move from a replaylogs_move div"""
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
            
            # Extract all log entries for this move
            log_entries = move_div.find_all('div', class_='gamelogreview')
            if not log_entries:
                return None
            
            # Combine all log entries into description
            descriptions = []
            for entry in log_entries:
                descriptions.append(entry.get_text().strip())
            
            full_description = ' | '.join(descriptions)
            
            # Determine action type and extract specific data
            action_type, card_play, tile_place = self._classify_action(log_entries)
            
            # Extract resource changes
            resource_changes = self._extract_resource_changes(log_entries)
            
            # Extract parameter changes
            parameter_changes = self._extract_parameter_changes(log_entries)
            
            # Determine player (simplified - could be more sophisticated)
            player = self._determine_player(log_entries, full_description)
            
            move = TMMove(
                move_number=move_number,
                timestamp=timestamp,
                player=player,
                action_type=action_type,
                description=full_description,
                card_play=card_play,
                tile_place=tile_place,
                resource_changes=resource_changes,
                parameter_changes=parameter_changes,
                raw_html=str(move_div)
            )
            
            return move
            
        except Exception as e:
            logger.error(f"Error parsing move: {e}")
            return None
    
    def _classify_action(self, log_entries: List[Tag]) -> Tuple[str, Optional[CardPlay], Optional[TilePlace]]:
        """Classify the type of action and extract specific data"""
        action_type = "unknown"
        card_play = None
        tile_place = None
        
        for entry in log_entries:
            text = entry.get_text().strip()
            
            # Check for card plays
            if 'plays card' in text:
                action_type = "play_card"
                card_play = self._extract_card_play(entry, log_entries)
            
            # Check for tile placements
            elif any(phrase in text for phrase in ['places City', 'places Forest', 'places Ocean']):
                if action_type == "unknown":  # Don't override card plays that also place tiles
                    action_type = "place_tile"
                tile_place = self._extract_tile_placement(entry)
            
            # Check for other actions
            elif 'passes' in text:
                action_type = "pass"
            elif 'Convert heat into temperature' in text:
                action_type = "convert_heat"
            elif 'standard project' in text:
                action_type = "standard_project"
            elif 'claims milestone' in text:
                action_type = "claim_milestone"
            elif 'funds' in text and 'award' in text:
                action_type = "fund_award"
        
        return action_type, card_play, tile_place
    
    def _extract_card_play(self, entry: Tag, all_entries: List[Tag]) -> Optional[CardPlay]:
        """Extract card play information"""
        text = entry.get_text()
        
        # Extract card name
        card_link = entry.find('div', class_='card_hl_tt')
        if card_link:
            card_name = card_link.get_text().strip()
            card_id = card_link.get('data-clicktt', '')
        else:
            # Fallback: try to extract from text
            match = re.search(r'plays card (.+)', text)
            if match:
                card_name = match.group(1).strip()
                card_id = None
            else:
                return None
        
        # Extract costs and effects from surrounding entries
        cost_resources = []
        immediate_effects = []
        
        # Look for cost information in previous entries
        for prev_entry in all_entries:
            prev_text = prev_entry.get_text()
            if 'pays' in prev_text and any(resource in prev_text for resource in ['M€', 'steel', 'titanium']):
                cost_resources.extend(self._extract_resource_changes([prev_entry]))
        
        # Look for immediate effects in following entries
        for next_entry in all_entries:
            next_text = next_entry.get_text()
            if 'immediate effect' in next_text:
                immediate_effects.extend(self._extract_resource_changes([next_entry]))
        
        return CardPlay(
            card_name=card_name,
            card_id=card_id,
            cost_resources=cost_resources,
            immediate_effects=immediate_effects
        )
    
    def _extract_tile_placement(self, entry: Tag) -> Optional[TilePlace]:
        """Extract tile placement information"""
        text = entry.get_text()
        
        # Extract tile type and location
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
            return None
        
        location = location_match.group(1).strip() if location_match else "Unknown"
        
        return TilePlace(
            tile_type=tile_type,
            location=location
        )
    
    def _extract_resource_changes(self, log_entries: List[Tag]) -> List[ResourceChange]:
        """Extract resource changes from log entries"""
        changes = []
        
        for entry in log_entries:
            html_content = str(entry)
            text = entry.get_text()
            
            # Pattern 1: "gains X <resource>" or "pays X <resource>"
            gain_pattern = r'gains (\d+) <div class="token_img tracker_(\w+)"[^>]*title="([^"]*)"[^>]*></div>'
            pay_pattern = r'pays (\d+) <div class="token_img tracker_(\w+)"[^>]*title="([^"]*)"[^>]*></div>'
            
            # Pattern 2: "gains <resource>X" (number after the icon)
            gain_after_pattern = r'gains <div class="token_img tracker_(\w+)"[^>]*title="([^"]*)"[^>]*></div>(\d+)'
            pay_after_pattern = r'pays <div class="token_img tracker_(\w+)"[^>]*title="([^"]*)"[^>]*></div>(\d+)'
            
            # Pattern 3: Production changes
            increase_prod_pattern = r'increases <div class="token_img tracker_(\w+)"[^>]*title="([^"]*)"[^>]*></div> by (\d+)'
            reduce_prod_pattern = r'reduces <div class="token_img tracker_(\w+)"[^>]*title="([^"]*)"[^>]*></div> by (\d+)'
            
            # Apply patterns
            patterns = [
                (gain_pattern, 1),      # gains X resource
                (pay_pattern, -1),      # pays X resource  
                (gain_after_pattern, 1), # gains resource X
                (pay_after_pattern, -1), # pays resource X
                (increase_prod_pattern, 1), # increases production
                (reduce_prod_pattern, -1),  # reduces production
            ]
            
            for pattern, sign in patterns:
                matches = re.finditer(pattern, html_content)
                for match in matches:
                    if 'gains' in pattern or 'pays' in pattern:
                        if len(match.groups()) == 3:
                            if pattern in [gain_pattern, pay_pattern]:
                                amount = int(match.group(1)) * sign
                                tracker = match.group(2)
                                title = match.group(3)
                            else:  # gain_after_pattern, pay_after_pattern
                                tracker = match.group(1)
                                title = match.group(2)
                                amount = int(match.group(3)) * sign
                            
                            resource_name = self._map_tracker_to_resource(tracker, title)
                            is_production = 'Production' in title
                            changes.append(ResourceChange(resource_name, amount, production=is_production))
                    
                    else:  # production changes
                        tracker = match.group(1)
                        title = match.group(2)
                        amount = int(match.group(3)) * sign
                        
                        resource_name = self._map_tracker_to_resource(tracker, title)
                        changes.append(ResourceChange(resource_name, amount, production=True))
        
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
            't': 'Temperature',
            'o': 'Oxygen',
            'w': 'Oceans',
            'pm': 'M€',
            'ps': 'Steel',
            'pu': 'Titanium',
            'pp': 'Plant',
            'pe': 'Energy',
            'ph': 'Heat',
        }
        
        return mapping.get(tracker, title)
    
    def _extract_parameter_changes(self, log_entries: List[Tag]) -> Dict[str, int]:
        """Extract terraforming parameter changes"""
        changes = {}
        
        for entry in log_entries:
            text = entry.get_text()
            html_content = str(entry)
            
            # Look for parameter changes in the HTML content
            # Pattern: "increases <icon> by X step/s to a value of Y"
            
            # Temperature changes
            temp_patterns = [
                r'increases.*by (\d+) step.*to a value of (-?\d+).*Temperature',
                r'increases.*Temperature.*by (\d+) step.*to a value of (-?\d+)',
                r'increases <div class="token_img tracker_t"[^>]*title="Temperature"[^>]*></div> by (\d+) step.*to a value of (-?\d+)'
            ]
            
            for pattern in temp_patterns:
                temp_match = re.search(pattern, html_content)
                if temp_match:
                    changes['temperature'] = int(temp_match.group(2))
                    break
            
            # Oxygen changes  
            oxygen_patterns = [
                r'increases.*by (\d+) step.*to a value of (\d+).*Oxygen',
                r'increases.*Oxygen Level.*by (\d+) step.*to a value of (\d+)',
                r'increases <div class="token_img tracker_o"[^>]*title="Oxygen Level"[^>]*></div> by (\d+) step.*to a value of (\d+)'
            ]
            
            for pattern in oxygen_patterns:
                oxygen_match = re.search(pattern, html_content)
                if oxygen_match:
                    changes['oxygen'] = int(oxygen_match.group(2))
                    break
            
            # Ocean changes
            ocean_patterns = [
                r'increases.*by (\d+) step.*to a value of (\d+).*Ocean',
                r'increases.*Oceans.*by (\d+) step.*to a value of (\d+)',
                r'increases <div class="token_img tracker_w"[^>]*title="Oceans"[^>]*></div> by (\d+) step.*to a value of (\d+)'
            ]
            
            for pattern in ocean_patterns:
                ocean_match = re.search(pattern, html_content)
                if ocean_match:
                    changes['oceans'] = int(ocean_match.group(2))
                    break
        
        return changes
    
    def _determine_player(self, log_entries: List[Tag], description: str) -> str:
        """Determine which player made this move"""
        # Look for player names in the description
        # This is a simplified approach - could be more sophisticated
        
        for entry in log_entries:
            text = entry.get_text()
            
            # Look for explicit player mentions
            if ' plays ' in text or ' chooses ' in text or ' pays ' in text:
                words = text.split()
                if words:
                    potential_player = words[0]
                    if potential_player not in ['You', 'The', 'A', 'An']:
                        return potential_player
            
            # Handle "You" references - would need context to resolve
            if text.startswith('You '):
                return "You"  # Could be resolved with additional context
        
        return "Unknown"
    
    def _build_final_state(self, moves: List[TMMove], players: List[str], soup: BeautifulSoup = None) -> TMGameState:
        """Build the final game state from all moves"""
        state = TMGameState()
        
        # Initialize starting values
        state.temperature = -30
        state.oxygen = 0
        state.oceans = 0
        
        # Track final parameter values by going through all moves
        for move in moves:
            if move.parameter_changes:
                if 'temperature' in move.parameter_changes:
                    state.temperature = move.parameter_changes['temperature']
                if 'oxygen' in move.parameter_changes:
                    state.oxygen = move.parameter_changes['oxygen']
                if 'oceans' in move.parameter_changes:
                    state.oceans = move.parameter_changes['oceans']
        
        # Determine final generation
        generation_count = 1  # Start at generation 1
        for move in moves:
            if 'New generation' in move.description:
                generation_count += 1
        
        state.generation = generation_count
        
        # Set current player to last active player
        if moves:
            last_move = moves[-1]
            state.current_player = last_move.player
        
        return state
    
    def export_to_json(self, game: TMGame, filepath: str) -> None:
        """Export parsed game to JSON"""
        game_dict = asdict(game)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(game_dict, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported game to {filepath}")
    
    def export_moves_to_csv(self, game: TMGame, filepath: str) -> None:
        """Export moves to CSV for analysis"""
        import csv
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                'move_number', 'timestamp', 'player', 'action_type', 
                'description', 'card_name', 'tile_type', 'tile_location',
                'temperature', 'oxygen', 'oceans'
            ])
            
            # Data rows
            for move in game.moves:
                writer.writerow([
                    move.move_number,
                    move.timestamp,
                    move.player,
                    move.action_type,
                    move.description,
                    move.card_play.card_name if move.card_play else '',
                    move.tile_place.tile_type if move.tile_place else '',
                    move.tile_place.location if move.tile_place else '',
                    move.parameter_changes.get('temperature', ''),
                    move.parameter_changes.get('oxygen', ''),
                    move.parameter_changes.get('oceans', '')
                ])
        
        logger.info(f"Exported moves to {filepath}")
    
    def _extract_milestones_and_awards(self, soup: BeautifulSoup) -> Tuple[Dict[str, MilestoneAward], Dict[str, MilestoneAward]]:
        """Extract milestone and award information from the HTML"""
        milestones = {}
        awards = {}
        
        # Extract milestones
        milestone_section = soup.find('div', id='main_milestones')
        if milestone_section:
            milestone_elements = milestone_section.find_all('div', class_='milestone')
            for elem in milestone_elements:
                name = elem.get('data-name', '')
                if name:
                    milestone = MilestoneAward(
                        name=name,
                        vp_value=5  # Standard milestone VP value
                    )
                    
                    # Check if claimed (look for state changes in moves)
                    state = elem.get('data-state', '0')
                    if state != '0':
                        # Would need to cross-reference with moves to find who claimed it
                        pass
                    
                    milestones[name] = milestone
        
        # Extract awards
        award_section = soup.find('div', id='main_awards')
        if award_section:
            award_elements = award_section.find_all('div', class_='award')
            for elem in award_elements:
                name = elem.get('data-name', '')
                if name:
                    award = MilestoneAward(
                        name=name,
                        vp_value=5  # 1st place gets 5 VP, 2nd gets 2 VP
                    )
                    
                    # Check if funded (look for state changes in moves)
                    state = elem.get('data-state', '0')
                    if state != '0':
                        # Would need to cross-reference with moves to find who funded it
                        pass
                    
                    awards[name] = award
        
        return milestones, awards
    
    def _calculate_victory_points(self, soup: BeautifulSoup, players: List[str], moves: List[TMMove], 
                                 milestones: Dict[str, MilestoneAward], awards: Dict[str, MilestoneAward]) -> Dict[str, VictoryPoints]:
        """Extract accurate victory points from embedded game data"""
        # Extract VP data directly from the HTML content
        vp_data = self._extract_vp_data_from_html(str(soup))
        
        player_vp = {}
        
        # Try to extract proper player ID mapping from HTML first
        player_id_map = self._extract_player_id_mapping_from_html(str(soup), players)
        
        # If that fails, fall back to VP-based mapping
        if not player_id_map:
            player_id_map = self._map_players_to_ids(players, vp_data)
        
        for player in players:
            vp = VictoryPoints()
            
            # Get player ID for this player
            player_id = player_id_map.get(player)
            if player_id and player_id in vp_data:
                player_data = vp_data[player_id]
                total_details = player_data.get('total_details', {})
                
                # Extract accurate VP breakdown
                vp.tr_rating = total_details.get('tr', 20)
                vp.total = player_data.get('total', 0)
                
                # Extract milestone VP
                milestone_vp = total_details.get('milestones', 0)
                if milestone_vp > 0:
                    # Distribute milestone VP (simplified)
                    vp.milestones = {'milestones_total': milestone_vp}
                
                # Extract award VP
                award_vp = total_details.get('awards', 0)
                if award_vp > 0:
                    vp.awards = {'awards_total': award_vp}
                
                # Extract card VP
                card_vp = total_details.get('cards', 0)
                if card_vp > 0:
                    vp.cards = {'cards_total': card_vp}
                
                # Extract board tile VP
                cities_vp = total_details.get('cities', 0)
                greeneries_vp = total_details.get('greeneries', 0)
                vp.board_tiles = cities_vp + greeneries_vp
                
            else:
                # Fallback to old calculation method
                vp.tr_rating = self._extract_final_tr(soup, player, moves)
                vp.milestones = self._extract_milestone_vp(player, moves, milestones)
                vp.awards = self._extract_award_vp(player, moves, awards)
                vp.cards = self._extract_card_vp(player, moves)
                vp.board_tiles = self._extract_board_tile_vp(player, moves)
                
                vp.total = (vp.tr_rating + 
                           sum(vp.milestones.values()) + 
                           sum(vp.awards.values()) + 
                           sum(vp.cards.values()) + 
                           vp.board_tiles)
            
            player_vp[player] = vp
        
        return player_vp
    
    def _extract_final_tr(self, soup: BeautifulSoup, player: str, moves: List[TMMove]) -> int:
        """Extract final TR rating for a player"""
        # Look for TR changes in moves
        final_tr = 20  # Starting TR
        
        for move in moves:
            if move.player == player:
                for change in move.resource_changes:
                    if change.resource_type == 'TR':
                        final_tr += change.amount
        
        return final_tr
    
    def _extract_milestone_vp(self, player: str, moves: List[TMMove], milestones: Dict[str, MilestoneAward]) -> Dict[str, int]:
        """Extract milestone VP for a player"""
        milestone_vp = {}
        
        for move in moves:
            if move.player == player and move.action_type == "claim_milestone":
                # Extract milestone name from description
                for milestone_name in milestones.keys():
                    if milestone_name.lower() in move.description.lower():
                        milestone_vp[milestone_name] = 5
                        break
        
        return milestone_vp
    
    def _extract_award_vp(self, player: str, moves: List[TMMove], awards: Dict[str, MilestoneAward]) -> Dict[str, int]:
        """Extract award VP for a player"""
        award_vp = {}
        
        # This would require analyzing final standings for each award
        # For now, we'll look for award funding as a proxy
        for move in moves:
            if move.player == player and move.action_type == "fund_award":
                # Extract award name from description
                for award_name in awards.keys():
                    if award_name.lower() in move.description.lower():
                        # Simplified: assume funder gets some VP (would need final standings)
                        award_vp[award_name] = 2  # Placeholder
                        break
        
        return award_vp
    
    def _extract_card_vp(self, player: str, moves: List[TMMove]) -> Dict[str, int]:
        """Extract card VP for a player using comprehensive database"""
        from .card_vp_database import get_card_vp
        
        card_vp = {}
        
        for move in moves:
            if move.player == player and move.card_play:
                card_name = move.card_play.card_name
                vp_value = get_card_vp(card_name)
                if vp_value > 0:
                    card_vp[card_name] = vp_value
        
        return card_vp
    
    def _extract_board_tile_vp(self, player: str, moves: List[TMMove]) -> int:
        """Extract board tile VP for a player (forests + cities)"""
        tile_count = 0
        
        for move in moves:
            if move.player == player and move.tile_place:
                if move.tile_place.tile_type in ['Forest', 'City']:
                    tile_count += 1
        
        return tile_count  # Each forest/city is worth 1 VP
    
    def export_vp_breakdown_to_csv(self, game: TMGame, filepath: str) -> None:
        """Export VP breakdown to CSV for analysis"""
        import csv
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                'player', 'corporation', 'tr_rating', 'milestone_vp', 'award_vp', 
                'card_vp', 'board_tile_vp', 'total_vp'
            ])
            
            # Data rows
            for player in game.players:
                corp = game.corporations.get(player, 'Unknown')
                vp = game.final_state.player_vp.get(player, VictoryPoints())
                
                writer.writerow([
                    player,
                    corp,
                    vp.tr_rating,
                    sum(vp.milestones.values()),
                    sum(vp.awards.values()),
                    sum(vp.cards.values()),
                    vp.board_tiles,
                    vp.total
                ])
        
        logger.info(f"Exported VP breakdown to {filepath}")
    
    def _extract_vp_data_from_html(self, html_content: str) -> Dict[str, Any]:
        """Extract VP data directly from HTML content - completely generic"""
        # Use the exact same pattern that works in extract_complete_vp.py
        # This pattern should find both players in the VP data structure
        pattern = r'"data":\{("(\d+)":\{.*?"total":(\d+).*?\}.*?"(\d+)":\{.*?"total":(\d+).*?\})\}'
        
        matches = re.findall(pattern, html_content, re.DOTALL)
        
        if matches:
            # Find the match with highest combined total
            best_match = None
            best_total = 0
            
            for match_data, player1_id, total1, player2_id, total2 in matches:
                combined_total = int(total1) + int(total2)
                if combined_total > best_total:
                    best_total = combined_total
                    best_match = match_data
            
            if best_match:
                try:
                    # Add braces to make it valid JSON
                    json_str = "{" + best_match + "}"
                    
                    # Try to fix JSON structure if needed
                    brace_count = best_match.count('{') - best_match.count('}')
                    if brace_count > 0:
                        json_str = "{" + best_match + '}' * brace_count + "}"
                    
                    vp_data = json.loads(json_str)
                    return vp_data
                    
                except json.JSONDecodeError:
                    logger.warning("Failed to parse VP data from HTML")
        
        return {}
    
    def _map_players_to_ids(self, players: List[str], vp_data: Dict[str, Any]) -> Dict[str, str]:
        """Map player names to player IDs in VP data - completely generic fallback"""
        player_id_map = {}
        
        # This is a fallback method when HTML-based mapping fails
        # Since we can't reliably determine which player corresponds to which VP total
        # without additional context, we'll use a simple alphabetical mapping
        # This is not ideal but better than making incorrect assumptions about player order
        
        # Get all player IDs from VP data, sorted alphabetically for consistency
        player_ids = sorted(vp_data.keys())
        players_sorted = sorted(players)
        
        # Map players alphabetically to player IDs alphabetically
        # This avoids making assumptions about VP rankings
        for i, player in enumerate(players_sorted):
            if i < len(player_ids):
                player_id = player_ids[i]
                player_id_map[player] = player_id
        
        # Log a warning since this is not reliable
        logger.warning(f"Using fallback VP-based mapping (not reliable): {player_id_map}")
        
        return player_id_map
    
    def _extract_player_id_mapping_from_html(self, html_content: str, players: List[str]) -> Dict[str, str]:
        """Extract the actual mapping between player names and IDs from HTML"""
        player_id_map = {}
        
        # First, get the valid player IDs from VP data to filter against
        vp_data = self._extract_vp_data_from_html(html_content)
        valid_player_ids = set(vp_data.keys())
        
        # Look for player board elements that might contain the mapping
        for player in players:
            # Search for patterns where player name appears near a player ID
            patterns = [
                rf'{re.escape(player)}[^0-9]*(\d{{8,}})',  # name followed by ID
                rf'(\d{{8,}})[^a-zA-Z]*{re.escape(player)}',  # ID followed by name
                rf'player[^>]*{re.escape(player)}[^0-9]*(\d{{8,}})',  # player context
                rf'(\d{{8,}})[^>]*player[^>]*{re.escape(player)}',  # reverse
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                if matches:
                    # Filter matches to only include valid player IDs from VP data
                    for match in matches:
                        if len(match) >= 8 and match in valid_player_ids:
                            player_id_map[player] = match
                            break
                    
                    # If we found a valid mapping, break out of pattern loop
                    if player in player_id_map:
                        break
        
        return player_id_map
    
    def extract_vp_progression(self, html_content: str) -> List[Dict[str, Any]]:
        """Extract VP progression throughout the game - completely generic"""
        # Find all VP data structures with any player IDs
        pattern = r'"data":\{((?:"(\d+)":\{[^}]*"total":(\d+)[^}]*\}[,\s]*)+)\}'
        
        matches = re.findall(pattern, html_content, re.DOTALL)
        vp_progression = []
        
        for i, match_data in enumerate(matches):
            try:
                # Add braces to make it valid JSON
                json_str = "{" + match_data[0] + "}"
                
                # Try to fix JSON structure if needed
                brace_count = match_data[0].count('{') - match_data[0].count('}')
                if brace_count > 0:
                    json_str = "{" + match_data[0] + '}' * brace_count + "}"
                
                vp_data = json.loads(json_str)
                
                # Calculate combined total and extract player totals
                combined_total = 0
                player_totals = {}
                
                for player_id, data in vp_data.items():
                    total = data.get('total', 0)
                    combined_total += total
                    player_totals[player_id] = total
                
                # Add metadata
                vp_entry = {
                    'move_index': i,
                    'combined_total': combined_total,
                    'player_totals': player_totals,
                    'vp_data': vp_data
                }
                
                vp_progression.append(vp_entry)
                
            except json.JSONDecodeError:
                # Skip malformed entries
                continue
        
        return vp_progression
    
    def export_vp_progression_to_csv(self, game: TMGame, html_content: str, filepath: str) -> None:
        """Export VP progression to CSV for analysis - completely generic"""
        import csv
        
        vp_progression = self.extract_vp_progression(html_content)
        
        if not vp_progression:
            logger.warning("No VP progression data found")
            return
        
        # Get all player IDs from the first entry to build dynamic headers
        first_entry = vp_progression[0]
        player_ids = sorted(first_entry['vp_data'].keys())
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Build dynamic header
            header = ['move_index', 'combined_total']
            for player_id in player_ids:
                header.extend([
                    f'player_{player_id}_total',
                    f'player_{player_id}_tr',
                    f'player_{player_id}_awards',
                    f'player_{player_id}_milestones',
                    f'player_{player_id}_cities',
                    f'player_{player_id}_greeneries',
                    f'player_{player_id}_cards'
                ])
            
            writer.writerow(header)
            
            # Data rows
            for entry in vp_progression:
                vp_data = entry['vp_data']
                row = [entry['move_index'], entry['combined_total']]
                
                for player_id in player_ids:
                    player_data = vp_data.get(player_id, {})
                    player_details = player_data.get('total_details', {})
                    
                    row.extend([
                        player_data.get('total', 0),
                        player_details.get('tr', 0),
                        player_details.get('awards', 0),
                        player_details.get('milestones', 0),
                        player_details.get('cities', 0),
                        player_details.get('greeneries', 0),
                        player_details.get('cards', 0)
                    ])
                
                writer.writerow(row)
        
        logger.info(f"Exported VP progression to {filepath}")

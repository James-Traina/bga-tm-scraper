"""
Terraforming Mars game log parser for BoardGameArena replays
Comprehensive parser that extracts all game data into a structured format
"""
import re
import json
import os
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from bs4 import BeautifulSoup, Tag
import logging

logger = logging.getLogger(__name__)

@dataclass
class EloData:
    """Represents ELO information for a player"""
    arena_points: Optional[int] = None
    arena_points_change: Optional[int] = None
    game_rank: Optional[int] = None
    game_rank_change: Optional[int] = None

@dataclass
class GameState:
    """Represents the game state at a specific point in time"""
    move_index: int
    generation: int
    temperature: int
    oxygen: int
    oceans: int
    player_vp: Dict[str, Dict[str, Any]]  # player_id -> VP breakdown
    milestones: Dict[str, Dict[str, Any]]  # milestone_name -> details
    awards: Dict[str, Dict[str, Any]]  # award_name -> details
    
    def __post_init__(self):
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
    vp_breakdown: Dict[str, Any]
    cards_played: List[str]
    milestones_claimed: List[str]
    awards_funded: List[str]
    elo_data: Optional[EloData] = None

@dataclass
class GameData:
    """Complete game data structure"""
    # Game metadata
    replay_id: str
    game_date: str
    game_duration: str
    winner: str
    generations: int
    
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

class Parser:
    """Comprehensive Terraforming Mars game log parser for BoardGameArena replays"""
    
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
    
    def parse_complete_game(self, html_content: str, replay_id: str) -> GameData:
        """Parse a complete game and return comprehensive data structure"""
        logger.info(f"Starting parsing for game {replay_id}")
        
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
            player_vp={}, milestones={}, awards={}
        )
        
        # Determine winner
        winner = self._determine_winner(players_info)
        
        # Extract game metadata
        metadata = self._extract_metadata(soup, html_content, moves_with_states)
        
        # Calculate max generation from vp_progression or moves
        max_generation = self._calculate_max_generation(vp_progression, moves_with_states)
        
        # Create game data
        game_data = GameData(
            replay_id=replay_id,
            game_date=self._extract_game_date(soup),
            game_duration=self._calculate_game_duration(moves_with_states),
            winner=winner,
            generations=max_generation,
            players=players_info,
            moves=moves_with_states,
            final_state=final_state,
            vp_progression=vp_progression,
            parameter_progression=parameter_progression,
            metadata=metadata
        )
        
        logger.info(f"Parsing complete for game {replay_id}: {len(moves_with_states)} moves, {len(players_info)} players")
        return game_data
    
    def _extract_players_info(self, soup: BeautifulSoup, html_content: str) -> Dict[str, Player]:
        """Extract comprehensive player information"""
        # Get player names from span elements
        player_names = []
        player_elements = soup.find_all('span', class_='playername')
        for elem in player_elements:
            player_name = elem.get_text().strip()
            if player_name and player_name not in player_names:
                player_names.append(player_name)
        
        # Fallback: Extract player names from move descriptions if no playername spans found
        if not player_names:
            logger.info("No playername spans found, extracting from move descriptions")
            player_names = self._extract_player_names_from_moves(soup)
        
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
                vp_breakdown=vp_breakdown,
                cards_played=[],  # Will be populated from moves
                milestones_claimed=[],  # Will be populated from moves
                awards_funded=[]  # Will be populated from moves
            )
        
        logger.info(f"Extracted {len(players)} players: {list(players.keys())}")
        return players
    
    def _extract_player_names_from_moves(self, soup: BeautifulSoup) -> List[str]:
        """Extract player names from move descriptions as fallback"""
        player_names = set()
        
        # Look for player names in move descriptions
        log_entries = soup.find_all('div', class_='gamelogreview')
        for entry in log_entries:
            text = entry.get_text()
            
            # Look for patterns like "PlayerName plays card", "PlayerName chooses corporation", etc.
            patterns = [
                r'(\w+(?:\s+\w+)*) plays card',
                r'(\w+(?:\s+\w+)*) chooses corporation',
                r'(\w+(?:\s+\w+)*) gains',
                r'(\w+(?:\s+\w+)*) pays',
                r'(\w+(?:\s+\w+)*) increases',
                r'(\w+(?:\s+\w+)*) places',
                r'(\w+(?:\s+\w+)*) claims milestone',
                r'(\w+(?:\s+\w+)*) funds.*award'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    # Clean up the match and add if it looks like a player name
                    name = match.strip()
                    if name and len(name) > 1 and name not in ['You', 'Module', 'Map']:
                        player_names.add(name)
        
        result = list(player_names)
        logger.info(f"Extracted {len(result)} player names from moves: {result}")
        return result
    
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
    
    def _validate_resource_value(self, resource: str, value: int, is_production: bool = False) -> int:
        """Validate and clamp resource values to valid ranges"""
        if is_production:
            # Production minimums in Terraforming Mars
            minimums = {
                'M€': -5,  # Can go negative due to certain cards
                'Steel': 0,
                'Titanium': 0,
                'Plant': 0,
                'Energy': 0,
                'Heat': 0
            }
            min_val = minimums.get(resource, 0)
            return max(min_val, value)
        else:
            # Regular resources can't go below 0 (except M€ which can be negative)
            if resource == 'M€':
                return value  # M€ can be negative
            elif resource == 'TR':
                return max(20, min(63, value))  # TR range is 20-63
            else:
                return max(0, value)  # Other resources can't be negative

    def _build_game_states(self, moves: List[Move], vp_progression: List[Dict[str, Any]], players_info: Dict[str, Player]) -> List[Move]:
        """Build game states for each move with VP, milestone, and award tracking"""
        # Initialize tracking variables
        current_temp = -30
        current_oxygen = 0
        current_oceans = 0
        current_generation = 1
        
        # Track milestones and awards state throughout the game
        current_milestones = {}
        current_awards = {}
        
        # Create a mapping from move_id to VP data for proper correlation
        vp_by_move_id = {}
        for vp_entry in vp_progression:
            move_id = vp_entry.get('move_id')
            if move_id:
                # Convert move_id to string for consistent matching
                vp_by_move_id[str(move_id)] = vp_entry.get('vp_data', {})
        
        logger.info(f"Built VP mapping for {len(vp_by_move_id)} moves")
        
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
            
            # Update milestone and award tracking
            if move.action_type == 'claim_milestone':
                milestone_match = re.search(r'claims milestone (\w+)', move.description)
                if milestone_match:
                    milestone_name = milestone_match.group(1)
                    current_milestones[milestone_name] = {
                        'claimed_by': move.player_name,
                        'player_id': move.player_id,
                        'move_number': move.move_number,
                        'timestamp': move.timestamp
                    }
            
            if move.action_type == 'fund_award':
                award_match = re.search(r'funds (\w+) award', move.description)
                if award_match:
                    award_name = award_match.group(1)
                    current_awards[award_name] = {
                        'funded_by': move.player_name,
                        'player_id': move.player_id,
                        'move_number': move.move_number,
                        'timestamp': move.timestamp
                    }
            
            # Get VP data for this move by matching move_number with move_id
            move_vp_data = vp_by_move_id.get(str(move.move_number), {})
            
            # Log when we find VP data for debugging
            if move_vp_data:
                logger.debug(f"Found VP data for move {move.move_number}")
            else:
                logger.debug(f"No VP data found for move {move.move_number}")
            
            # Create game state (without resource/production tracking)
            game_state = GameState(
                move_index=move.move_number - 1,  # Use move_number - 1 for 0-based indexing
                generation=current_generation,
                temperature=current_temp,
                oxygen=current_oxygen,
                oceans=current_oceans,
                player_vp=move_vp_data,
                milestones=dict(current_milestones),
                awards=dict(current_awards)
            )
            
            move.game_state = game_state
        
        return moves
    
    def _extract_card_names(self, html_content: str) -> Dict[str, str]:
        """Extract card ID to name mappings from HTML"""
        card_names = {}
        
        try:
            # Pattern to match card elements with data-name attributes
            pattern = r'<div[^>]+id="(card_[^"]+)"[^>]+data-name="([^"]+)"'
            matches = re.findall(pattern, html_content)
            
            for card_id, card_name in matches:
                # Clean up the card ID (remove _help suffix if present)
                clean_id = card_id.replace('_help', '')
                card_names[clean_id] = card_name
            
            logger.info(f"Extracted {len(card_names)} card name mappings")
            return card_names
            
        except Exception as e:
            logger.error(f"Error extracting card names: {e}")
            return {}
    
    def _extract_milestone_names(self, html_content: str) -> Dict[str, str]:
        """Extract milestone ID to name mappings from HTML"""
        milestone_names = {}
        
        try:
            # Pattern to match milestone elements with data-name attributes
            pattern = r'<div[^>]+id="(milestone_\d+)"[^>]+data-name="([^"]+)"'
            matches = re.findall(pattern, html_content)
            
            for milestone_id, milestone_name in matches:
                milestone_names[milestone_id] = milestone_name
            
            logger.info(f"Extracted {len(milestone_names)} milestone name mappings")
            return milestone_names
            
        except Exception as e:
            logger.error(f"Error extracting milestone names: {e}")
            return {}
    
    def _extract_award_names(self, html_content: str) -> Dict[str, str]:
        """Extract award ID to name mappings from HTML"""
        award_names = {}
        
        try:
            # Pattern to match award elements with data-name attributes
            pattern = r'<div[^>]+id="(award_\d+)"[^>]+data-name="([^"]+)"'
            matches = re.findall(pattern, html_content)
            
            for award_id, award_name in matches:
                award_names[award_id] = award_name
            
            logger.info(f"Extracted {len(award_names)} award name mappings")
            return award_names
            
        except Exception as e:
            logger.error(f"Error extracting award names: {e}")
            return {}

    def _extract_g_gamelogs(self, html_content: str) -> Dict[str, Any]:
        """Extract g_gamelogs JSON with proper brace balancing"""
        try:
            # Find the start of g_gamelogs
            pattern = r'g_gamelogs\s*=\s*'
            match = re.search(pattern, html_content)
            
            if not match:
                logger.warning("g_gamelogs not found in HTML")
                return {}
            
            start_pos = match.end()
            
            # Find the complete JSON object by counting braces
            brace_count = 0
            in_string = False
            escape_next = False
            
            for i, char in enumerate(html_content[start_pos:], start_pos):
                if escape_next:
                    escape_next = False
                    continue
                    
                if char == '\\':
                    escape_next = True
                    continue
                    
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                    
                if not in_string:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            # Found the end of the JSON object
                            json_str = html_content[start_pos:i+1]
                            return json.loads(json_str)
                    elif char == ';' and brace_count == 0:
                        # Hit semicolon before closing brace - malformed
                        break
            
            logger.error("Could not find complete g_gamelogs JSON")
            return {}
            
        except (json.JSONDecodeError, AttributeError) as e:
            logger.error(f"Error extracting g_gamelogs: {e}")
            return {}
    
    def _replace_ids_with_names(self, vp_data: Dict[str, Any], card_names: Dict[str, str], 
                               milestone_names: Dict[str, str], award_names: Dict[str, str]) -> Dict[str, Any]:
        """Replace ID references with actual names in VP data"""
        if not isinstance(vp_data, dict):
            return vp_data
        
        updated_data = {}
        
        for player_id, player_vp in vp_data.items():
            if not isinstance(player_vp, dict):
                updated_data[player_id] = player_vp
                continue
            
            updated_player_vp = dict(player_vp)
            
            # Process the details section
            if 'details' in updated_player_vp and isinstance(updated_player_vp['details'], dict):
                details = updated_player_vp['details']
                updated_details = {}
                
                for category, items in details.items():
                    if not isinstance(items, dict):
                        updated_details[category] = items
                        continue
                    
                    updated_items = {}
                    
                    for item_id, item_data in items.items():
                        # Determine the actual name based on category and ID
                        actual_name = item_id  # Default to original ID
                        
                        if category == 'cards' and item_id in card_names:
                            actual_name = card_names[item_id]
                        elif category == 'milestones' and item_id in milestone_names:
                            actual_name = milestone_names[item_id]
                        elif category == 'awards' and item_id in award_names:
                            actual_name = award_names[item_id]
                        
                        updated_items[actual_name] = item_data
                    
                    updated_details[category] = updated_items
                
                updated_player_vp['details'] = updated_details
            
            updated_data[player_id] = updated_player_vp
        
        return updated_data

    def _parse_scoring_data_from_gamelogs(self, gamelogs: Dict[str, Any], card_names: Dict[str, str], 
                                        milestone_names: Dict[str, str], award_names: Dict[str, str]) -> List[Dict[str, Any]]:
        """Parse scoring data from g_gamelogs entries and replace IDs with names"""
        scoring_entries = []
        
        try:
            data_entries = gamelogs.get('data', {}).get('data', [])
            
            for entry in data_entries:
                if not isinstance(entry, dict):
                    continue
                
                # Look for data array within each entry
                entry_data = entry.get('data', [])
                if not isinstance(entry_data, list):
                    continue
                
                for data_item in entry_data:
                    if not isinstance(data_item, dict):
                        continue
                    
                    # Look for scoringTable type entries
                    if data_item.get('type') == 'scoringTable':
                        scoring_data = data_item.get('args', {}).get('data', {})
                        if scoring_data:
                            # Replace IDs with names in the scoring data
                            scoring_data_with_names = self._replace_ids_with_names(
                                scoring_data, card_names, milestone_names, award_names
                            )
                            
                            scoring_entry = {
                                'move_id': entry.get('move_id'),
                                'time': entry.get('time'),
                                'uid': data_item.get('uid'),
                                'scoring_data': scoring_data_with_names
                            }
                            scoring_entries.append(scoring_entry)
            
            logger.info(f"Extracted {len(scoring_entries)} scoring entries from g_gamelogs")
            return scoring_entries
            
        except Exception as e:
            logger.error(f"Error parsing scoring data from g_gamelogs: {e}")
            return []
    
    def _parse_milestone_award_data(self, gamelogs: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Parse milestone and award data from g_gamelogs"""
        milestones_data = {}
        awards_data = {}
        
        try:
            data_entries = gamelogs.get('data', {}).get('data', [])
            
            for entry in data_entries:
                if not isinstance(entry, dict):
                    continue
                
                entry_data = entry.get('data', [])
                if not isinstance(entry_data, list):
                    continue
                
                for data_item in entry_data:
                    if not isinstance(data_item, dict):
                        continue
                    
                    # Look for milestone claims
                    log_message = data_item.get('log', '')
                    if 'milestone' in log_message.lower():
                        args = data_item.get('args', {})
                        if 'player_name' in args:
                            milestone_info = {
                                'move_id': entry.get('move_id'),
                                'time': entry.get('time'),
                                'player_id': args.get('player_id'),
                                'player_name': args.get('player_name'),
                                'uid': data_item.get('uid')
                            }
                            milestone_key = f"milestone_{data_item.get('uid', 'unknown')}"
                            milestones_data[milestone_key] = milestone_info
                    
                    # Look for award funding
                    if 'award' in log_message.lower() and 'fund' in log_message.lower():
                        args = data_item.get('args', {})
                        if 'player_name' in args:
                            award_info = {
                                'move_id': entry.get('move_id'),
                                'time': entry.get('time'),
                                'player_id': args.get('player_id'),
                                'player_name': args.get('player_name'),
                                'uid': data_item.get('uid')
                            }
                            award_key = f"award_{data_item.get('uid', 'unknown')}"
                            awards_data[award_key] = award_info
            
            logger.info(f"Extracted {len(milestones_data)} milestone entries and {len(awards_data)} award entries")
            return milestones_data, awards_data
            
        except Exception as e:
            logger.error(f"Error parsing milestone/award data: {e}")
            return {}, {}
    
    def _extract_vp_progression(self, html_content: str) -> List[Dict[str, Any]]:
        """Extract VP progression throughout the game using g_gamelogs data"""
        # Extract g_gamelogs first
        gamelogs = self._extract_g_gamelogs(html_content)
        if not gamelogs:
            # Fallback to old method if g_gamelogs not found
            return self._extract_vp_progression_fallback(html_content)
        
        # Extract name mappings from HTML
        card_names = self._extract_card_names(html_content)
        milestone_names = self._extract_milestone_names(html_content)
        award_names = self._extract_award_names(html_content)
        
        # Parse scoring data from g_gamelogs with name replacement
        scoring_entries = self._parse_scoring_data_from_gamelogs(gamelogs, card_names, milestone_names, award_names)
        
        vp_progression = []
        for i, entry in enumerate(scoring_entries):
            scoring_data = entry['scoring_data']
            
            # Calculate combined total
            combined_total = sum(data.get('total', 0) for data in scoring_data.values())
            
            vp_entry = {
                'move_index': i,
                'move_id': entry.get('move_id'),
                'time': entry.get('time'),
                'combined_total': combined_total,
                'vp_data': scoring_data
            }
            
            vp_progression.append(vp_entry)
        
        logger.info(f"Extracted VP progression with {len(vp_progression)} entries")
        return vp_progression
    
    def _extract_vp_progression_fallback(self, html_content: str) -> List[Dict[str, Any]]:
        """Fallback VP progression extraction using the old regex method"""
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
                # Updated to handle multi-word player names
                match = re.search(r'([A-Za-z][A-Za-z0-9\s]+?) chooses corporation ([A-Za-z][A-Za-z0-9\s]+?)(?:\s*\||$)', text)
                if match:
                    player_name = match.group(1).strip()
                    corp_name = match.group(2).strip()
                    corporations[player_name] = corp_name
                    logger.info(f"Extracted corporation: {player_name} -> {corp_name}")
                else:
                    # Fallback pattern for simpler cases
                    fallback_match = re.search(r'(\w+(?:\s+\w+)*) chooses corporation (\w+)', text)
                    if fallback_match:
                        player_name = fallback_match.group(1).strip()
                        corp_name = fallback_match.group(2).strip()
                        corporations[player_name] = corp_name
                        logger.info(f"Extracted corporation (fallback): {player_name} -> {corp_name}")
        
        logger.info(f"Total corporations extracted: {corporations}")
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
    
    def _calculate_max_generation(self, vp_progression: List[Dict[str, Any]], moves: List[Move]) -> int:
        """Calculate the maximum generation from vp_progression or moves data"""
        max_generation = 1  # Default to generation 1
        
        try:
            # First, try to get max generation from moves with game states
            if moves:
                generations_from_moves = []
                for move in moves:
                    if move.game_state and move.game_state.generation:
                        generations_from_moves.append(move.game_state.generation)
                
                if generations_from_moves:
                    max_generation = max(generations_from_moves)
                    logger.info(f"Found max generation {max_generation} from moves")
                    return max_generation
            
            # Fallback: try to extract from vp_progression data
            # This is less reliable but can be used if moves don't have generation data
            if vp_progression:
                # VP progression entries might contain generation information
                # This would need to be implemented based on the actual structure
                logger.info("Attempting to extract generation from vp_progression (fallback)")
                # For now, we'll use a simple heuristic based on the number of VP entries
                # In Terraforming Mars, games typically last 8-12 generations
                estimated_generations = min(12, max(8, len(vp_progression) // 2))
                max_generation = estimated_generations
                logger.info(f"Estimated max generation {max_generation} from vp_progression length")
            
        except Exception as e:
            logger.error(f"Error calculating max generation: {e}")
            max_generation = 1
        
        logger.info(f"Calculated max generation: {max_generation}")
        return max_generation

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

    def parse_complete_game_with_elo(self, replay_html: str, table_html: str, table_id: str) -> GameData:
        """Parse a complete game with ELO data from both replay and table HTML"""
        logger.info(f"Starting parsing with ELO data for game {table_id}")
        
        # Parse ELO data from table HTML first to get player names
        elo_data = self.parse_elo_data(table_html)
        logger.info(f"Found ELO data for players: {list(elo_data.keys())}")
        
        # Parse the main game data from replay HTML
        game_data = self.parse_complete_game(replay_html, table_id)
        
        # If no players were found in replay HTML, create them from ELO data
        if not game_data.players and elo_data:
            logger.info("No players found in replay HTML, creating from ELO data")
            game_data.players = self._create_players_from_elo_data(elo_data, replay_html, table_id)
        
        # Merge ELO data into player information
        self._merge_elo_with_players(game_data.players, elo_data)
        
        # Update metadata to indicate ELO data was included
        game_data.metadata['elo_data_included'] = len(elo_data) > 0
        game_data.metadata['elo_players_found'] = len(elo_data)
        
        logger.info(f"Parsing with ELO complete for game {table_id}: ELO data found for {len(elo_data)} players")
        return game_data
    
    def parse_elo_data(self, table_html: str) -> Dict[str, EloData]:
        """
        Parse ELO data from table page HTML
        
        Args:
            table_html: HTML content of the table page
            
        Returns:
            dict: Player name -> EloData mapping
        """
        logger.info("Parsing ELO data from table HTML")
        
        soup = BeautifulSoup(table_html, 'html.parser')
        elo_data = {}
        
        try:
            # Use score-entry sections which contain complete player data
            score_entries = soup.find_all('div', class_='score-entry')
            logger.info(f"Found {len(score_entries)} score entries")
            
            for entry in score_entries:
                player_elo = self._parse_player_from_score_entry(entry)
                if player_elo and 'player_name' in player_elo:
                    player_name = player_elo.pop('player_name')
                    elo_data[player_name] = EloData(**player_elo)
                    logger.info(f"Parsed ELO data for {player_name}")
            
            # Fallback: try alternative parsing methods if score-entry method fails
            if not elo_data:
                logger.info("Fallback: trying alternative ELO parsing methods")
                elo_data = self._parse_elo_alternative_methods(soup, table_html)
            
            logger.info(f"Successfully parsed ELO data for {len(elo_data)} players")
            return elo_data
            
        except Exception as e:
            logger.error(f"Error parsing ELO data: {e}")
            return {}
    
    def _parse_player_from_score_entry(self, score_entry: Tag) -> Optional[Dict[str, Any]]:
        """Parse ELO data for a single player from their score entry section"""
        try:
            player_data = {}
            
            # Extract player name
            player_elem = score_entry.find('a', class_='playername')
            if not player_elem:
                return None
            
            player_name = player_elem.get_text().strip()
            if not player_name or player_name in ['Visitor']:
                return None
            
            player_data['player_name'] = player_name
            
            # Find all winpoints in this entry (there should be 2: arena and regular)
            winpoints = score_entry.find_all('div', class_='winpoints')
            
            # Find all newrank in this entry (there should be 2: arena and regular)
            newranks = score_entry.find_all('div', class_='newrank')
            
            # Parse Arena data (first winpoints/newrank pair)
            if len(winpoints) >= 1:
                arena_winpoints_text = winpoints[0].get_text().strip()
                # Extract arena points change
                arena_change_match = re.search(r'([+-]\d+)', arena_winpoints_text)
                if arena_change_match:
                    player_data['arena_points_change'] = int(arena_change_match.group(1))
            
            if len(newranks) >= 1:
                arena_newrank_text = newranks[0].get_text().strip()
                # Extract arena points (current)
                arena_points_match = re.search(r'(\d+)\s*pts', arena_newrank_text)
                if arena_points_match:
                    player_data['arena_points'] = int(arena_points_match.group(1))
            
            # Parse Game ELO data (second winpoints/newrank pair)
            if len(winpoints) >= 2:
                game_winpoints_text = winpoints[1].get_text().strip()
                # Extract game ELO change
                game_change_match = re.search(r'([+-]\d+)', game_winpoints_text)
                if game_change_match:
                    player_data['game_rank_change'] = int(game_change_match.group(1))
            
            if len(newranks) >= 2:
                game_newrank_text = newranks[1].get_text().strip()
                # Extract game rank (current)
                game_rank_match = re.search(r'(\d+)', game_newrank_text)
                if game_rank_match:
                    player_data['game_rank'] = int(game_rank_match.group(1))
            
            logger.info(f"Extracted ELO data for {player_name}: {player_data}")
            return player_data if len(player_data) > 1 else None  # Must have more than just player_name
            
        except Exception as e:
            logger.error(f"Error parsing player from score entry: {e}")
            return None

    def _parse_single_player_elo(self, rank_section: Tag, html_content: str) -> Optional[Dict[str, Any]]:
        """Parse ELO data for a single player from their rank section"""
        try:
            player_data = {}
            
            # Extract player name
            player_name_elem = rank_section.find('span', class_='playername')
            if not player_name_elem:
                return None
            
            player_data['player_name'] = player_name_elem.get_text().strip()
            
            # Extract Arena points (current season points)
            arena_points_elem = rank_section.find('div', id=lambda x: x and 'winpoints' in x)
            if arena_points_elem:
                # Look for the points value - typically a number like "1754"
                points_text = arena_points_elem.get_text()
                arena_points_match = re.search(r'(\d+)\s*pts', points_text)
                if arena_points_match:
                    player_data['arena_points'] = int(arena_points_match.group(1))
                else:
                    # Try to find just a number
                    number_match = re.search(r'(\d+)', points_text)
                    if number_match:
                        player_data['arena_points'] = int(number_match.group(1))
            
            # Extract Arena points change (gain/loss from this game)
            # Look for patterns like "+24" or "-5"
            change_pattern = r'([+-]\d+)'
            change_matches = re.findall(change_pattern, str(rank_section))
            if change_matches:
                # Take the first change value found
                player_data['arena_points_change'] = int(change_matches[0])
            
            # Extract Game rank (actual ELO rating)
            # Look for gamerank elements or patterns
            gamerank_elem = rank_section.find('div', class_='gamerank')
            if gamerank_elem:
                rank_text = gamerank_elem.get_text()
                rank_match = re.search(r'(\d+)', rank_text)
                if rank_match:
                    player_data['game_rank'] = int(rank_match.group(1))
            else:
                # Alternative: look for rank patterns in the HTML
                rank_pattern = r'gamerank[^>]*>.*?(\d+)'
                rank_match = re.search(rank_pattern, str(rank_section))
                if rank_match:
                    player_data['game_rank'] = int(rank_match.group(1))
            
            # Extract Game rank change
            # This might be in a separate element or combined with the rank
            rank_change_pattern = r'gamerank[^>]*>.*?([+-]\d+)'
            rank_change_match = re.search(rank_change_pattern, str(rank_section))
            if rank_change_match:
                player_data['game_rank_change'] = int(rank_change_match.group(1))
            
            return player_data if len(player_data) > 1 else None  # Must have more than just player_name
            
        except Exception as e:
            logger.error(f"Error parsing single player ELO: {e}")
            return None
    
    def _parse_elo_alternative_methods(self, soup: BeautifulSoup, html_content: str) -> Dict[str, EloData]:
        """Alternative methods to parse ELO data if standard method fails"""
        elo_data = {}
        
        try:
            # Method 1: Look for winpoints sections
            winpoints_sections = soup.find_all('div', id=lambda x: x and 'winpoints' in x)
            
            for section in winpoints_sections:
                # Try to find associated player name
                player_name = self._find_associated_player_name(section, soup)
                if player_name:
                    elo_info = {}
                    
                    # Extract points from this section
                    points_text = section.get_text()
                    points_match = re.search(r'(\d+)', points_text)
                    if points_match:
                        elo_info['arena_points'] = int(points_match.group(1))
                    
                    # Look for change indicators
                    change_match = re.search(r'([+-]\d+)', points_text)
                    if change_match:
                        elo_info['arena_points_change'] = int(change_match.group(1))
                    
                    if elo_info:
                        elo_data[player_name] = EloData(**elo_info)
            
            # Method 2: Parse from raw HTML patterns
            if not elo_data:
                elo_data = self._parse_elo_from_raw_patterns(html_content)
            
            return elo_data
            
        except Exception as e:
            logger.error(f"Error in alternative ELO parsing: {e}")
            return {}
    
    def _find_associated_player_name(self, element: Tag, soup: BeautifulSoup) -> Optional[str]:
        """Find the player name associated with an ELO element"""
        # Look for player name in parent elements
        current = element
        for _ in range(5):  # Search up to 5 levels up
            if current.parent:
                current = current.parent
                player_elem = current.find('span', class_='playername')
                if player_elem:
                    return player_elem.get_text().strip()
        
        # Look for player name in sibling elements
        siblings = element.find_next_siblings() + element.find_previous_siblings()
        for sibling in siblings:
            if hasattr(sibling, 'find'):
                player_elem = sibling.find('span', class_='playername')
                if player_elem:
                    return player_elem.get_text().strip()
        
        return None
    
    def _parse_elo_from_raw_patterns(self, html_content: str) -> Dict[str, EloData]:
        """Parse ELO data using raw HTML pattern matching"""
        elo_data = {}
        
        try:
            # Pattern to find player sections with ELO data
            # This is a more aggressive approach for when structured parsing fails
            
            # Find all player names first
            player_names = re.findall(r'<span[^>]*class="playername"[^>]*>([^<]+)</span>', html_content)
            
            for player_name in player_names:
                player_name = player_name.strip()
                if not player_name:
                    continue
                
                # Find the section of HTML around this player
                player_pattern = rf'<span[^>]*class="playername"[^>]*>{re.escape(player_name)}</span>'
                match = re.search(player_pattern, html_content)
                
                if match:
                    # Extract a reasonable chunk of HTML around the player name
                    start = max(0, match.start() - 1000)
                    end = min(len(html_content), match.end() + 1000)
                    player_section = html_content[start:end]
                    
                    elo_info = {}
                    
                    # Look for Arena points patterns
                    arena_points_patterns = [
                        r'winpoints[^>]*>.*?(\d+)',
                        r'(\d+)\s*pts',
                        r'points[^>]*>.*?(\d+)',
                    ]
                    
                    for pattern in arena_points_patterns:
                        match = re.search(pattern, player_section, re.IGNORECASE)
                        if match:
                            elo_info['arena_points'] = int(match.group(1))
                            break
                    
                    # Look for Arena points change
                    change_match = re.search(r'([+-]\d+)', player_section)
                    if change_match:
                        elo_info['arena_points_change'] = int(change_match.group(1))
                    
                    # Look for Game rank
                    rank_patterns = [
                        r'gamerank[^>]*>.*?(\d+)',
                        r'rank[^>]*>.*?(\d+)',
                    ]
                    
                    for pattern in rank_patterns:
                        match = re.search(pattern, player_section, re.IGNORECASE)
                        if match:
                            elo_info['game_rank'] = int(match.group(1))
                            break
                    
                    if elo_info:
                        elo_data[player_name] = EloData(**elo_info)
            
            return elo_data
            
        except Exception as e:
            logger.error(f"Error in raw pattern ELO parsing: {e}")
            return {}
    
    def _create_players_from_elo_data(self, elo_data: Dict[str, EloData], replay_html: str, table_id: str) -> Dict[str, Player]:
        """Create player objects from ELO data when replay HTML doesn't contain player info"""
        logger.info(f"Creating players from ELO data for {len(elo_data)} players")
        
        players = {}
        soup = BeautifulSoup(replay_html, 'html.parser')
        
        # Get VP data for final scores
        vp_data = self._extract_vp_data_from_html(replay_html)
        
        # Get corporations from replay HTML
        corporations = self._extract_corporations(soup)
        
        for i, (player_name, elo_info) in enumerate(elo_data.items()):
            # Create a player ID - try to find from VP data or use fallback
            player_id = None
            
            # Try to find player ID from VP data
            for vp_player_id, vp_player_data in vp_data.items():
                # This is a simple heuristic - could be improved
                if len(vp_data) == len(elo_data):
                    # If we have the same number of players in both, map by order
                    player_ids = sorted(vp_data.keys())
                    if i < len(player_ids):
                        player_id = player_ids[i]
                        break
            
            if not player_id:
                player_id = f"player_{i}"
            
            # Get final VP and breakdown
            final_vp = 0
            vp_breakdown = {}
            if player_id in vp_data:
                final_vp = vp_data[player_id].get('total', 0)
                vp_breakdown = vp_data[player_id].get('total_details', {})
            
            # Create player object
            player = Player(
                player_id=player_id,
                player_name=player_name,
                corporation=corporations.get(player_name, 'Unknown'),
                final_vp=final_vp,
                final_tr=vp_breakdown.get('tr', 20),
                vp_breakdown=vp_breakdown,
                cards_played=[],  # Will be populated from moves
                milestones_claimed=[],  # Will be populated from moves
                awards_funded=[],  # Will be populated from moves
                elo_data=elo_info
            )
            
            players[player_id] = player
            logger.info(f"Created player {player_name} with ID {player_id}")
        
        return players

    def _merge_elo_with_players(self, players: Dict[str, Player], elo_data: Dict[str, EloData]):
        """Merge ELO data into player objects"""
        logger.info(f"Merging ELO data for {len(elo_data)} players")
        
        for player_id, player in players.items():
            # Try to find ELO data by player name
            if player.player_name in elo_data:
                player.elo_data = elo_data[player.player_name]
                logger.info(f"Merged ELO data for player {player.player_name}")
            else:
                logger.warning(f"No ELO data found for player {player.player_name}")

    def export_to_json(self, game_data: GameData, output_path: str):
        """Export game data to JSON"""
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
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

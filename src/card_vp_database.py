"""
Terraforming Mars Card VP Database
Contains VP values for all cards in the base game and expansions
"""

# Base game cards with VP values
BASE_GAME_VP_CARDS = {
    # Green cards with VP
    "Artificial Lake": 1,
    "Artificial Photosynthesis": 1,
    "Asteroid Mining": 2,
    "Biomass Combustors": 2,
    "Birds": 1,  # 1 VP per animal on card
    "Breathing Filters": 2,
    "Cartel": 1,
    "Cattle": 1,  # 1 VP per animal on card
    "Commercial District": 1,
    "Cupola City": 1,
    "Decomposers": 1,  # 1 VP per animal on card
    "Ecological Zone": 1,  # 1 VP per 2 animals on card
    "Electro Catapult": 1,
    "Energy Tapping": 1,
    "Extreme-Cold Fungus": 1,
    "Fish": 1,  # 1 VP per animal on card
    "Food Factory": 1,
    "Fuel Factory": 1,
    "Ganymede Colony": 1,
    "Gene Repair": 2,
    "Grass": 1,
    "Greenhouses": 1,
    "Herbivores": 1,  # 1 VP per animal on card
    "Immigrant City": 1,
    "Insulation": 1,
    "Kelp Farming": 1,
    "Lagrange Observatory": 1,
    "Large Convoy": 2,
    "Livestock": 1,  # 1 VP per animal on card
    "Luna Governor": 2,
    "Magnetic Field Generators": 1,
    "Mars University": 1,
    "Medical Lab": 1,
    "Mineral Deposit": 2,
    "Mining Area": 1,
    "Mining Rights": 1,
    "Moss": 1,
    "Natural Preserve": 1,
    "Noctis City": 1,
    "Nuclear Zone": 2,
    "Olympus Conference": 1,
    "Optimal Aerobraking": 1,
    "Ore Processor": 1,
    "Peroxide Power": 1,
    "Pets": 1,  # 1 VP per animal on card
    "Phobos Space Haven": 1,
    "Physics Complex": 2,
    "Plantation": 1,
    "Predators": 1,  # 1 VP per animal on card
    "Protected Habitats": 2,
    "Protected Valley": 1,
    "Rad-Chem Factory": 1,
    "Research Outpost": 1,
    "Restricted Area": 2,
    "Rover Construction": 1,
    "Security Fleet": 1,
    "Small Animals": 1,  # 1 VP per animal on card
    "Solar Power": 1,
    "Space Mirrors": 1,
    "Space Station": 1,
    "Symbiotic Fungus": 1,
    "Tectonic Stress Power": 1,
    "Toll Station": 1,
    "Towing a Comet": 1,
    "Tropical Resort": 2,
    "Underground City": 2,
    "Urbanized Area": 1,
    "Viral Enhancers": 1,
    "Water Import from Europa": 1,
    "Wave Power": 1,
    "Windmills": 1,
    "Zeppelins": 1,
    
    # Blue cards with VP
    "Adaptation Technology": 1,
    "Advanced Ecosystems": 3,
    "AI Central": 1,
    "Anti-Gravity Technology": 3,
    "Aquifer Pumping": 2,
    "Asteroid": 2,
    "Atmospheric Processors": 3,
    "Bribed Committee": 2,
    "Business Contacts": 1,
    "Business Network": 1,
    "Capital": 1,
    "Carbonate Processing": 3,
    "Comet": 2,
    "Corporate Stronghold": 3,
    "Deimos Down": 3,
    "Designed Microorganisms": 2,
    "Development Center": 1,
    "Domed Crater": 1,
    "Earth Catapult": 2,
    "Eos Chasma National Park": 2,
    "Equatorial Magnetizer": 1,
    "Farming": 2,
    "Geothermal Power": 1,
    "Giant Ice Asteroid": 2,
    "Giant Solar Shade": 3,
    "Great Escarpment Consortium": 1,
    "Greenery": 1,
    "Heat Trappers": 1,
    "Heather": 1,
    "Hired Raiders": 2,
    "Ice Asteroid": 2,
    "Ice Cap Melting": 1,
    "Immigrant Ships": 1,
    "Import of Advanced GHG": 1,
    "Imported GHG": 1,
    "Imported Hydrogen": 1,
    "Imported Nitrogen": 1,
    "Industrial Center": 1,
    "Industrial Microbes": 1,
    "Insects": 1,
    "Interplanetary Cinematics": 1,
    "Interstellar Colony Ship": 4,
    "Invention Contest": 1,
    "Investment Loan": 1,
    "Io Mining Industries": 1,
    "Ironworks": 1,
    "Lava Flows": 2,
    "Lichen": 1,
    "Local Heat Trapping": 1,
    "Mangrove": 1,
    "Mass Converter": 3,
    "Methane from Titan": 2,
    "Microbes": 2,
    "Micromills": 1,
    "Miranda Resort": 1,
    "Nitrite Reducing Bacteria": 3,
    "Nitrogen-Rich Asteroid": 1,
    "Open City": 1,
    "Permafrost Extraction": 1,
    "Power Grid": 1,
    "Power Infrastructure": 1,
    "Power Plant": 1,
    "Power Supply Consortium": 1,
    "Quantum Extractor": 2,
    "Regolith Eaters": 1,
    "Release of Inert Gases": 2,
    "Research": 1,
    "Sabotage": 1,
    "Satellites": 1,
    "Shuttles": 1,
    "Sister Planet Support": 1,
    "Soletta": 1,
    "Space Elevator": 2,
    "Sponsors": 2,
    "Standard Technology": 1,
    "Steelworks": 1,
    "Strip Mine": 2,
    "Subterranean Reservoir": 2,
    "Terraforming Ganymede": 2,
    "Thermophiles": 1,
    "Titanium Mine": 1,
    "Trees": 1,
    "Tropical Resort": 2,
    "Unmi Crater": 1,
    "Venusian Animals": 1,
    "Venusian Insects": 1,
    "Worms": 1,
}

# Corporation VP bonuses
CORPORATION_VP_BONUSES = {
    "Aridor": 0,  # No direct VP bonus
    "Cheung Shing Mars": 0,  # No direct VP bonus
    "CrediCor": 0,  # No direct VP bonus
    "Ecoline": 0,  # No direct VP bonus
    "Helion": 0,  # No direct VP bonus
    "Interplanetary Cinematics": 1,  # 1 VP per event played
    "Inventrix": 0,  # No direct VP bonus
    "Mining Guild": 0,  # No direct VP bonus
    "Phobolog": 0,  # No direct VP bonus
    "PhoboLog": 0,  # No direct VP bonus (alternative spelling)
    "Robinson Industries": 0,  # No direct VP bonus
    "Saturn Systems": 0,  # No direct VP bonus
    "Teractor": 0,  # No direct VP bonus
    "Thorgate": 0,  # No direct VP bonus
    "UNMI": 0,  # No direct VP bonus
    "United Nations Mars Initiative": 0,  # No direct VP bonus (full name)
    "Vitor": 3,  # Gain 3 M€ when playing cards with non-negative VP
}

# Prelude cards with VP (if using Prelude expansion)
PRELUDE_VP_CARDS = {
    "Biofuels": 1,
    "Business Empire": 1,
    "Donation": 0,
    "Ecology Experts": 1,
    "Experimental Forest": 1,
    "Great Aquifer": 1,
    "Huge Asteroid": 3,
    "Loan": 0,
    "Metal Company": 1,
    "Mohole Area": 1,
    "Research Network": 1,
    "Self-Sufficient Settlement": 2,
    "Society Support": 1,
    "Space Hotels": 4,
    "Supplier": 1,
    "Supply Drop": 1,
    "Unmi Crater": 1,
}

def get_card_vp(card_name: str) -> int:
    """
    Get the VP value for a card
    
    Args:
        card_name: Name of the card
        
    Returns:
        VP value of the card (0 if not found)
    """
    # Check base game cards
    if card_name in BASE_GAME_VP_CARDS:
        return BASE_GAME_VP_CARDS[card_name]
    
    # Check prelude cards
    if card_name in PRELUDE_VP_CARDS:
        return PRELUDE_VP_CARDS[card_name]
    
    # Check for common VP patterns in card names
    vp_patterns = [
        ("VP", 1),
        ("Victory Point", 1),
        ("Point", 1),
    ]
    
    for pattern, vp in vp_patterns:
        if pattern.lower() in card_name.lower():
            return vp
    
    return 0

def get_corporation_vp_bonus(corporation_name: str) -> int:
    """
    Get the VP bonus for a corporation
    
    Args:
        corporation_name: Name of the corporation
        
    Returns:
        VP bonus value (0 if none)
    """
    return CORPORATION_VP_BONUSES.get(corporation_name, 0)

def is_animal_card(card_name: str) -> bool:
    """
    Check if a card gains VP from animals
    
    Args:
        card_name: Name of the card
        
    Returns:
        True if card gains VP from animals
    """
    animal_cards = [
        "Birds", "Cattle", "Decomposers", "Ecological Zone", "Fish", 
        "Herbivores", "Livestock", "Pets", "Predators", "Small Animals"
    ]
    return card_name in animal_cards

def is_resource_card(card_name: str) -> bool:
    """
    Check if a card gains VP from resources on it
    
    Args:
        card_name: Name of the card
        
    Returns:
        True if card gains VP from resources
    """
    resource_cards = [
        "Microbes", "Nitrite Reducing Bacteria", "Regolith Eaters",
        "Thermophiles", "Venusian Animals", "Venusian Insects", "Worms"
    ]
    return card_name in resource_cards

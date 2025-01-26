# core/location_data.py
import random

class LocationCommands:
    """Define available commands per location type"""
    COMMANDS = {
        "Planet": {
            "base_commands": [
                ('buy', 'b'), ('sell', 's'), ('upgrade', 'u'),
                ('travel', 't'), ('repair', 'r'), ('info', 'i'),
                ('build', 'bl'), ('cantina', 'c'), ('shop', 'sh'),
                ('action', 'a'), ('mine', 'm'), ('port', 'p'), ('end', 'e')
            ],
            "description": "Standard planetary commerce hub"
        },
        "AsteroidBase": {
            "base_commands": [
                ('buy', 'b'), ('sell', 's'), ('upgrade', 'u'),
                ('travel', 't'), ('repair', 'r'), ('info', 'i'),
                ('build', 'bl'), ('cantina', 'c'), ('shop', 'sh'),
                ('action', 'a'), ('mine', 'm'), ('port', 'p'), ('end', 'e')
            ],
            "description": "Mining and resource extraction facility"
        },
        "DeepSpaceOutpost": {
            "base_commands": [
                ('buy', 'b'), ('sell', 's'), ('upgrade', 'u'),
                ('travel', 't'), ('repair', 'r'), ('info', 'i'),
                ('build', 'bl'), ('cantina', 'c'), ('shop', 'sh'),
                ('action', 'a'), ('port', 'p'), ('end', 'e')
            ],
            "description": "Strategic trading outpost"
        },
        "ResearchColony": {
            "base_commands": [
                ('buy', 'b'), ('sell', 's'), ('upgrade', 'u'),
                ('travel', 't'), ('research', 'r'), ('info', 'i'),
                ('build', 'bl'), ('shop', 'sh'), ('action', 'a'),
                ('port', 'p'), ('end', 'e')
            ],
            "special_commands": {
                "research": {
                    "options": ["analyze", "experiment", "fundamental"],
                    "description": "Conduct research activities"
                }
            },
            "description": "Advanced scientific research facility. No repair facilities available."
        }
    }

    @staticmethod
    def get_available_commands(location_type):
        """Get available commands for location type"""
        commands = LocationCommands.COMMANDS.get(location_type, 
                                               LocationCommands.COMMANDS["Planet"])
        return commands["base_commands"]

    @staticmethod
    def get_special_commands(location_type):
        """Get special commands if any"""
        location_data = LocationCommands.COMMANDS.get(location_type, {})
        return location_data.get("special_commands", {})

    @staticmethod
    def get_commands_for_location(location):
        """Helper method to get all commands for a location instance"""
        return {
            "available": LocationCommands.get_available_commands(location.location_type),
            "special": LocationCommands.get_special_commands(location.location_type)
        }

class LocationCapabilities:
    """Centralized management of location type capabilities"""
    
    # Define capabilities for each location type
    CAPABILITIES = {
        "Planet": {
            "can_trade": ["tech", "agri", "salt", "fuel"],
            "can_build": [
                "stockmarket",
                "permaculture",
                "organic",
                "agrobot",
                "nanotech",
                "neuroengineering",
                "mining"
            ],
            "can_produce": ["tech", "agri"],
            "can_mine": ["salt", "fuel"],
            "has_cantina": True,
            "has_shop": True,
            "base_exogeology": 100,
            "research_multiplier": 1.0
        },
        "AsteroidBase": {
            "can_trade": ["salt", "fuel"],
            "can_build": ["mining", "stockmarket"],
            "can_produce": [],
            "can_mine": ["salt", "fuel"],
            "has_cantina": True,
            "has_shop": True,
            "base_exogeology": 150,  # Better at mining
            "research_multiplier": 0.8
        },
        "DeepSpaceOutpost": {
            "can_trade": ["tech", "agri"],
            "can_build": ["stockmarket", "nanotech"],
            "can_produce": ["tech"],
            "can_mine": [],
            "has_cantina": True,
            "has_shop": True,
            "base_exogeology": 0,
            "research_multiplier": 1.2
        },
        "ResearchColony": {
            "can_trade": ["tech"],
            "can_build": ["nanotech", "neuroengineering"],
            "can_produce": ["tech"],
            "can_mine": [],
            "has_cantina": False,
            "has_shop": True,
            "base_exogeology": 0,
            "research_multiplier": 2.0
        }
    }

class LocationTerminology:
    """Manages context-appropriate terminology for different location types"""
    
    TERMS = {
        "Planet": {
            "name": "planet",
            "here": "on this planet",
            "to": "to the planet",
            "at": "on",
            "from": "from the planet",
            "possessive": "planet's",
            "local": "planetary",
            "variants": ["world", "globe", "planetoid"]
        },
        "AsteroidBase": {
            "name": "base",
            "here": "at this base",
            "to": "to the base",
            "at": "at",
            "from": "from the base",
            "possessive": "base's",
            "local": "base",
            "variants": ["asteroid station", "mining post", "rock station"]
        },
        "DeepSpaceOutpost": {
            "name": "outpost",
            "here": "at this outpost",
            "to": "to the outpost",
            "at": "at",
            "from": "from the outpost",
            "possessive": "outpost's",
            "local": "outpost",
            "variants": ["station", "waypoint", "trading post"]
        },
        "ResearchColony": {
            "name": "colony",
            "here": "in this colony",
            "to": "to the colony",
            "at": "in",
            "from": "from the colony",
            "possessive": "colony's",
            "local": "colonial",
            "variants": ["research station", "science base", "research facility"]
        }
    }
    
    @staticmethod
    def get_term(location_type, term_type, use_variant=False):
        """Get appropriate terminology for a location type"""
        terms = LocationTerminology.TERMS.get(location_type, LocationTerminology.TERMS["Planet"])
        if use_variant and random.random() < 0.3:  # 30% chance to use variant
            if term_type == "name":
                return random.choice(terms["variants"])
        return terms.get(term_type, terms["name"])
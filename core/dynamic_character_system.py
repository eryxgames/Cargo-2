# core/dynamic_character_system.py
import random
from core.template import CharacterTemplate
from core.character_encounters import SpecialCharacterEncounters


class DynamicCharacterSystem:
    def __init__(self, game):
        self.game = game
        self.active_characters = {}
        self.character_generators = {
            "human": game.character_generators["human"],
            "synthetic": game.character_generators["synthetic"],
            "alien": game.character_generators["alien"],
             "special": game.character_generators["special"]  # Use SpecialCharacterGenerator for VIPs
        }
        self.character_triggers = {
            "neuroengineering_uprising": {
                "condition": lambda game: self.count_buildings(game, "Neuroengineering Guild") >= 4,
                "generator": "synthetic",
                "character_type": "neurodroid_leader",
                "event_chain": "neurodroid_uprising"
            },
            "agrobot_rebellion": {
                "condition": lambda game: self.count_buildings(game, "Agrobot Assembly Line") >= 4,
                "generator": "synthetic",
                "character_type": "agrobot_leader",
                "event_chain": "agrobot_collective"
            },
            "pirate_nemesis": {
                "condition": lambda game: game.ship.combat_victories.get('pirate', 0) >= 10,
                "generator": "human",
                "character_type": "pirate_captain",
                "event_chain": "pirate_vendetta"
            },
             # Add VIP passenger trigger with correct generator type
            "vip_passenger": {
                "condition": lambda game: (
                    game.ship.passenger_reputation >= 40 and
                    game.turn - game.reputation_manager.last_vip_spawn >= 5
                ),
                "generator": "special",
                "character_type": "vip_passenger",
                "event_chain": None
             },
             "galactic_alliance": {
                "condition": lambda game: (
                    game.ship.passenger_reputation >= 60 and 
                    game.story_manager.get_chapter_number() >= 2
                ),
                "generator": "special",
                "character_type": "vip_political",
                "event_chain": "galactic_alliance"
            },
            "system_rebellion": {
                "condition": lambda game: (
                    game.ship.passenger_reputation >= 70 and 
                    game.story_manager.get_chapter_number() >= 3 and
                    len([loc for loc in game.locations if hasattr(loc, 'controlled_by_player')]) >= 2
                ),
                "generator": "special",
                "character_type": "vip_corporate",
                "event_chain": "system_rebellion"
            },
            "ancient_mysteries": {
                "condition": lambda game: (
                    game.ship.passenger_reputation >= 80 and 
                    game.story_manager.get_chapter_number() >= 4 and
                    "alien_artifacts" in game.story_manager.completed_story_beats
                ),
                "generator": "special",
                "character_type": "vip_scientific",
                "event_chain": "ancient_mysteries"
            },
             "grand_commander_voxx": {
                "condition": lambda game: (
                    game.ship.passenger_reputation >= 70 and
                    game.story_manager.get_chapter_number() >= 3
                ),
                "generator": "human",
                "character_type": "grand_commander_voxx",
                "event_chain": None  # Will be handled by story
            }
        }
        self.event_chains = {}
        self.add_passenger_triggers()
        self.create_passenger_event_chains()
        self.character_encounters = SpecialCharacterEncounters(self.game)
        self.templates = CharacterTemplate.load_character_templates("data/characters.yml") #added here, template info is needed

    def create_character_box(self, character_content, style='round'):
        return self.game.ui.create_box(character_content, style)

    def check_character_triggers(self):
        """Check for new character appearances based on game state"""
        for trigger_id, trigger in self.character_triggers.items():
            if (trigger_id not in self.active_characters and 
                trigger['condition'](self.game)):
                self.spawn_character(trigger_id)

    def spawn_character(self, trigger_id):
        """Generate and introduce a new character"""
        trigger = self.character_triggers[trigger_id]
        generator = self.character_generators[trigger['generator']]
        character = generator.generate_character(trigger['character_type'])
        
        # Create a unique identifier for the character
        character_id = f"{trigger_id}_{self.game.turn}"
        
        # Store the character with its full details
        self.active_characters[character_id] = {
            "character": character,
            "trigger_id": trigger_id,
            "location": self.game.current_location,
        }
        
        # Initialize event chain if applicable
        if trigger['event_chain']:
            self.event_chains[character_id] = self.create_event_chain(trigger['event_chain'], character)
        
        # Announce character using the character_id
        self.announce_character(character_id)
        

    def announce_character(self, character_id):
        """Display character introduction using flexible character data"""
        # Retrieve the character entry
        character_entry = self.active_characters.get(character_id)
        if not character_entry:
            print(f"Error: No character found for ID {character_id}")
            return
        
        # Get character 
        character = character_entry["character"]
        
        # Prepare content based on character type
        content = {
            'title': str(getattr(character, 'full_name', str(character))),
            'introduction': "",
            'description': "",
            'options': ""
        }
        
        # Try to get introduction from different possible sources
        if hasattr(character, 'content'):
            # For CharacterTemplate-based characters
            intros = character.content['dialogue'].get('first_meeting', [])
            content['introduction'] = random.choice(intros) if intros else "A new encounter begins."
        elif hasattr(character, 'introduction'):
            # For SpecialCharacter objects
            content['introduction'] = str(character.introduction)
        else:
            # Fallback generic introduction
            content['introduction'] = "A mysterious figure approaches..."
        
        # Ensure all content values are strings
        for key in content:
            content[key] = str(content[key]) if content[key] is not None else ""
        
        # Handle interactions if they exist
        current_location = self.game.current_location.location_type.lower()
        
        # Determine options based on character type
        if hasattr(character, 'content') and 'interactions' in character.content:
            interactions = character.content['interactions'].get(current_location, [])
            content['options'] = ", ".join(str(opt) for opt in interactions) if interactions else ""
        
        # Display character box
        print(self.create_character_box(content, 'round'))
        
        # If options exist, allow interaction
        if content['options']:
            choice = self.game.validate_input(
                "Your response: ",
                [str(i) for i in range(1, len(content['options'].split(', ')) + 1)]
            )
            if choice:
                # Note: This might need further adjustment depending on your interaction handling
                return self.handle_character_interaction(character_id, int(choice) - 1, current_location)
        
        return True
    
    def add_passenger_triggers(self):
        """Add passenger-related triggers to character system"""
        self.character_triggers.update({
            "galactic_alliance": {
                "condition": lambda game: (
                    game.ship.passenger_reputation >= 60 and 
                    game.story_manager.get_chapter_number() >= 2
                ),
                "generator": "special",
                "character_type": "vip_political",
                "event_chain": "galactic_alliance"
            },
            "system_rebellion": {
                "condition": lambda game: (
                    game.ship.passenger_reputation >= 70 and 
                    game.story_manager.get_chapter_number() >= 3 and
                    len([loc for loc in game.locations if hasattr(loc, 'controlled_by_player')]) >= 2
                ),
                "generator": "special",
                "character_type": "vip_corporate",
                "event_chain": "system_rebellion"
            },
            "ancient_mysteries": {
                "condition": lambda game: (
                    game.ship.passenger_reputation >= 80 and 
                    game.story_manager.get_chapter_number() >= 4 and
                    "alien_artifacts" in game.story_manager.completed_story_beats
                ),
                "generator": "special",
                "character_type": "vip_scientific",
                "event_chain": "ancient_mysteries"
            },
            "vip_passenger": {
                "condition": lambda game: (
                    game.ship.passenger_reputation >= 40 and
                    game.turn - game.reputation_manager.last_vip_spawn >= 5
                ),
                "generator": "special",  # Will use SpecialCharacterGenerator
                "character_type": "vip_passenger",
                "event_chain": None  # VIPs don't need event chains
            },
            "grand_commander_voxx": {
                "condition": lambda game: (
                    game.ship.passenger_reputation >= 70 and
                    game.story_manager.get_chapter_number() >= 3
                ),
                "generator": "human",
                "character_type": "grand_commander_voxx",
                "event_chain": None  # Will be handled by story
            }
        })

    def create_passenger_event_chains(self):
        """Create event chains for passenger-related stories"""
        self.event_chains.update({
            "galactic_alliance": [
                {
                    "type": "dialogue",
                    "message": "Discuss galactic politics and potential alliances",
                    "choices": ["support_alliance", "remain_neutral", "oppose_alliance"],
                    "consequences": {
                        "support_alliance": {
                            "reputation": 15,
                            "plot_points": 5,
                            "unlock": "diplomatic_missions"
                        },
                        "remain_neutral": {
                            "reputation": 5,
                            "plot_points": 2
                        },
                        "oppose_alliance": {
                            "reputation": -10,
                            "plot_points": 3,
                            "unlock": "independent_contracts"
                        }
                    }
                },
                {
                    "type": "mission",
                    "message": "Transport diplomatic delegation",
                    "requirements": {
                        "destinations": 3,
                        "min_satisfaction": 90
                    },
                    "rewards": {
                        "money": 50000,
                        "reputation": 20,
                        "plot_points": 8
                    }
                }
            ],
            "system_rebellion": [
                {
                    "type": "covert_transport",
                    "message": "Transport rebel leaders without detection",
                    "risk": 0.3,
                    "rewards": {
                        "money": 75000,
                        "reputation": 25,
                        "plot_points": 10
                    },
                    "failure_consequences": {
                        "reputation": -30,
                        "banned_systems": ["Alpha", "Beta"]
                    }
                },
                {
                    "type": "supply_run",
                    "message": "Deliver crucial supplies to rebel bases",
                    "cargo_requirements": {
                        "tech": 100,
                        "agri": 150
                    },
                    "rewards": {
                        "money": 100000,
                        "reputation": 30,
                        "plot_points": 15
                    }
                }
            ],
            "ancient_mysteries": [
                {
                    "type": "exploration",
                    "message": "Visit ancient ruins with the scholar",
                    "locations": ["Ruins Alpha", "Ruins Beta"],
                    "discoveries": {
                        "artifacts": 3,
                        "research_points": 200
                    },
                    "rewards": {
                        "money": 150000,
                        "reputation": 40,
                        "plot_points": 20
                    }
                }
            ]
        })

    def handle_character_interaction(self, character_id, choice, location_type):
        """Handle player interaction with a special character"""
        character = self.active_characters[character_id]["character"]
        template = self.templates[character.template_id]
        
        # Get available interactions for location
        if 'interactions' in template and location_type in template['interactions']:
            interactions = template['interactions'][location_type]
            if not interactions or choice >= len(interactions):
                return False
            interaction = interactions[choice]
        
        # Process interaction
        return self.process_interaction_outcome(character_id, interaction)
    
    def process_interaction_outcome(self, character_id, interaction):
        """Process the result of a character interaction"""
        character = self.active_characters[character_id]["character"]
        template = self.templates[character.template_id]
        
        # Apply rewards if any
        if 'rewards' in template.content:
            if 'money' in template.content['rewards']:
                self.game.ship.money += template.content['rewards']['money']
            if 'reputation_gain' in template.content['rewards']:
                self.game.ship.passenger_reputation += template.content['rewards']['reputation_gain']
            if 'plot_points' in template.content['rewards']:
                self.game.story_manager.plot_points += template.content['rewards']['plot_points']
        
        return True
        
    @staticmethod
    def count_buildings(game, building_type):
        """Count total number of specific buildings across all locations"""
        return sum(
            location.buildings.count(building_type)
            for location in game.locations
        )
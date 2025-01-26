# core/location_manager.py
import random
from core.quest import Quest

class LocationManager:
    """Manages location interactions with story and quest systems"""
    def __init__(self, game):
        self.game = game
        self.location_quests = {
            "AsteroidBase": {
                "unlock_requirements": {
                    "mining_quests_completed": 3,
                    "research_points": 50
                },
                "unlock_quest": {
                    "name": "Mysterious Mining Signals",
                    "description": "Investigate unusual mining activity signals",
                    "reward_money": 10000,
                    "reward_rp": 100
                }
            },
            "DeepSpaceOutpost": {
                "unlock_requirements": {
                    "combat_victories": 5,
                    "research_points": 75
                },
                "unlock_quest": {
                    "name": "Frontier Defense",
                    "description": "Help establish a secure trading route",
                    "reward_money": 15000,
                    "reward_rp": 150
                }
            },
            "Planet": {
                "unlock_requirements": {
                    "research_points": 50,
                    "trades_completed": 5
                },
                "unlock_quest": {
                    "name": "Establish Trading Network",
                    "description": "Complete trades across multiple systems",
                    "reward_money": 5000,
                    "reward_rp": 50,
                    "completion_criteria": {
                        "trades_completed": 10,
                        "different_locations": 3
                    }
                }
            },
            "ResearchColony": {
                "unlock_requirements": {
                    "research_points": 100,
                    "discoveries": 3
                },
                "unlock_quest": {
                    "name": "Scientific Breakthrough",
                    "description": "Assist in a major research project",
                    "reward_money": 20000,
                    "reward_rp": 200,
                    "completion_criteria": {
                        "research_points_gained": 150,
                        "analysis_completed": 3,
                        "experiments_conducted": 2
                    }
                }
            }
        }
        
        self.location_story_events = {
            "AsteroidBase": [
                "mineral_discovery",
                "pirate_hideout",
                "ancient_technology"
            ],
            "DeepSpaceOutpost": [
                "smuggler_network",
                "alien_contact",
                "trade_revolution"
            ],
            "ResearchColony": [
                "breakthrough_discovery",
                "experiment_crisis",
                "alien_artifacts"
            ]
        }
        
    def handle_location_discovery(self, location):
        """Handle discovery of a new location"""
        if location.name not in self.game.discovered_locations:
            self.game.discovered_locations.add(location.name)
            
            # Award discovery rewards
            discovery_reward = 1000 * (self.game.story_manager.current_chapter + 1)
            research_reward = 20 * (self.game.story_manager.current_chapter + 1)
            
            self.game.ship.money += discovery_reward
            self.game.ship.research_points += research_reward
            
            # Check for story progression
            self.game.story_manager.check_discovery_milestone(location)
            
            # Check for quest updates
            self.game.quest_system.update_discovery_quests(location)
            
            self.game.display_story_message([
                f"Discovered new location: {location.name}!",
                f"Earned {self.game.format_money(discovery_reward)} credits",
                f"Gained {research_reward} research points"
            ])

            # Check for special location events
            if location.location_type in self.location_story_events:
                self.trigger_location_events(location)

    def trigger_location_events(self, location):
        """Trigger events specific to a location type"""
        if location.location_type in self.location_story_events:
            possible_events = self.location_story_events[location.location_type]
            if possible_events and random.random() < 0.3:  # 30% chance for event
                event = random.choice(possible_events)
                self.game.story_manager.trigger_story_event(event, 
                    {"location": location.name, "type": location.location_type})

    def check_location_unlock_progress(self, location_type):
        """Check if a location type can be unlocked based on player progress"""
        if location_type not in self.location_quests:
            return False
            
        requirements = self.location_quests[location_type]["unlock_requirements"]
        
        # Check mining quest requirement
        if "mining_quests_completed" in requirements:
            completed = len([q for q in self.game.quest_system.completed_quests 
                           if q.quest_type == "mining"])
            if completed < requirements["mining_quests_completed"]:
                return False
                
        # Check combat victories - now using total from dictionary
        if "combat_victories" in requirements:
            total_victories = self.game.ship.combat_victories['total']
            if total_victories < requirements["combat_victories"]:
                return False
                
        # Check research points
        if "research_points" in requirements:
            if self.game.ship.research_points < requirements["research_points"]:
                return False
                
        # Check discoveries
        if "discoveries" in requirements:
            if len(self.game.story_manager.completed_story_beats) < requirements["discoveries"]:
                return False
                
        return True

    def trigger_location_unlock_quest(self, location_type):
        """Create and trigger the unlock quest for a location type"""
        if location_type in self.location_quests:
            quest_data = self.location_quests[location_type]["unlock_quest"]
            
            # Create quest with unique type
            quest = Quest(
                name=quest_data["name"],
                description=quest_data["description"],
                reward_money=quest_data["reward_money"],
                reward_rp=quest_data["reward_rp"],
                quest_type=f"unlock_{location_type}",  # Make type unique
                requirements={"location_type": location_type},
                on_complete=lambda: self.complete_location_unlock(location_type)
            )
            
            # Use central quest addition method
            self.game.quest_system.add_quest(quest)

    def complete_location_unlock(self, location_type):
        """Handle the completion of a location unlock quest"""
        # Add location type to unlocked types
        if not hasattr(self.game, 'unlocked_location_types'):
            self.game.unlocked_location_types = set()
        self.game.unlocked_location_types.add(location_type)
        
        # Generate location-specific quests
        self.generate_location_quests(location_type)
        
        # Enable location-specific story events
        self.enable_location_story_events(location_type)

    def generate_location_quests(self, location_type):
        """Generate location-specific quests"""
        quest_templates = {
            "AsteroidBase": [
                {
                    "type": "mining",
                    "name": "Rich Mineral Deposits",
                    "description": "Extract valuable minerals",
                    "reward_multiplier": 1.5
                }
            ],
            "DeepSpaceOutpost": [
                {
                    "type": "combat",
                    "name": "Outpost Defense",
                    "description": "Protect the outpost from raiders",
                    "reward_multiplier": 1.4
                }
            ],
            "ResearchColony": [
                {
                    "type": "research",
                    "name": "Scientific Analysis",
                    "description": "Assist with research projects",
                    "reward_multiplier": 2.0
                }
            ]
        }
        
        if location_type in quest_templates:
            for template in quest_templates[location_type]:
                self.game.quest_system.generate_quest(template["type"], 
                    template["reward_multiplier"])

    def enable_location_story_events(self, location_type):
        """Enable story events specific to the location type"""
        if location_type in self.location_story_events:
            for event in self.location_story_events[location_type]:
                self.game.story_manager.enable_story_event(event)
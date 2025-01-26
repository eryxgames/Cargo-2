# core/location_manager.py
import random
from core.utils import format_money
from core.template import CharacterTemplate
from core.location import Location
from core.story_requirements import MilestoneRequirements
import csv
import json


class LocationManager:
    """Manages location interactions with story and quest systems"""
    def __init__(self, game):
        self.game = game
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

    def load_locations(self):
        """Load locations from data/locations.csv and use starting_locations"""
        locations = []
        try:
            with open("data/locations.csv", "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                   # Extract the requirements string and delete it from row
                   requirements = row.pop("requirements", "{}")
                   try:
                       if requirements and isinstance(requirements, str):
                         requirements = json.loads(requirements)
                       else:
                            requirements = {}
                   except json.JSONDecodeError:
                       print("Warning: Could not parse requirements JSON, skipping this location:", row.get('name'))
                       continue
                   
                   # Correct instantiation of location objects using the dictionary
                   location = Location(**row, requirements = requirements)

                    # Check if it's a starting location and if it needs to be unlocked
                   for start_loc in self.game.settings.get("starting_locations", []):
                       if start_loc.get("location_id") == location.name:
                            
                            # Check if unlocked or can be unlocked
                            if start_loc.get("unlocked", False):
                                locations.append(location)
                                continue # Load location

                            # Check if requirements are met
                            if "requirements" in start_loc:
                                requirements = start_loc["requirements"]
                                if MilestoneRequirements.check_requirements(requirements, self.game):
                                    locations.append(location)
                                    continue  # Load location
                   if hasattr(location, 'requirements') and location.requirements:
                       if MilestoneRequirements.check_requirements(location.requirements, self.game):
                            locations.append(location)
                   if not hasattr(location, "location_type"):
                    continue
        except FileNotFoundError:
            print("Error: locations.csv not found. Using default locations.")
        except Exception as e:
            print(f"Error loading locations from CSV: {e}")
        
        return locations

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
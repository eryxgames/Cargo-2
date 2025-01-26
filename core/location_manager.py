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
        
    def _parse_requirements(self, requirements_str):
        """Convert a string value from csv to a dictionary, if possible"""
        if not requirements_str or requirements_str == "{}":
            return {}
        try:
            # Attempt to parse the string as JSON
            return json.loads(requirements_str)
        except json.JSONDecodeError as e:
            print(f"Warning: Could not parse requirements: {requirements_str}, {e}")
            return {}  # Return empty dict if JSON parsing fails
        

    def load_locations(self):
            """Load locations from data/locations.csv and use starting_locations"""
            locations = []
            try:
                with open("data/locations.csv", "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                      
                        # Filter out non-location properties
                        valid_keys = ["name", "location_type", "tech_level", "agri_level", "research_points", "economy", "affiliation", "relation_to_player"]
                        location_data = {k: row[k] for k in valid_keys if k in row}

                        # Correct instantiation of location objects using the dictionary
                        location = Location(**location_data, requirements={}) #empty requirements object, for now

                        # Check if it's a starting location and if it needs to be unlocked
                        for start_loc in self.game.settings.get("starting_locations", []):
                            if start_loc.get("location_id") == location.name:
                                
                                # Check if unlocked or can be unlocked
                                if start_loc.get("unlocked", False):
                                    locations.append(location)
                                    continue # Load location

                                # Check if requirements are met
                                if "requirements" in start_loc:
                                    start_requirements = start_loc["requirements"]
                                    if MilestoneRequirements.check_requirements(start_requirements, self.game):
                                        locations.append(location)
                                        continue  # Load location
                                
                        locations.append(location)
                            
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
                
    def check_location_unlocks(self):
        """Check for new location type unlocks"""
        for location in self.game.locations: #check locations from all locations
           # Check if it's a starting location and if it needs to be unlocked
            for start_loc in self.game.settings.get("starting_locations", []):
                 if start_loc.get("location_id") == location.name:
                            
                    # Check if unlocked or can be unlocked
                    if start_loc.get("unlocked", False):
                        continue #skip if already unlocked

                    # Check if requirements are met
                    if "requirements" in start_loc:
                        start_requirements = start_loc["requirements"]
                        if MilestoneRequirements.check_requirements(start_requirements, self.game):
                            #trigger loading location
                            self.game.known_locations.append(location.name)
                            self.game.display_simple_message(f"New location available: {location.name}")
                            start_loc["unlocked"] = True
                            continue
            
            #check location unlock requirements using existing location data
            if hasattr(location, 'requirements') and location.requirements:
               if MilestoneRequirements.check_requirements(location.requirements, self.game):
                   if location.location_type not in self.game.unlocked_location_types:
                        self.game.unlocked_location_types.add(location.location_type)
                        self.game.display_simple_message(f"New location type unlocked: {location.location_type}")

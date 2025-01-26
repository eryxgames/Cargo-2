# core/reputation.py
import random
import json
import os
from core.ship import Passenger

class PassengerReputationManager:
    """Manages passenger reputation effects and related story/character events"""
    def __init__(self, game):
        self.game = game
        self.reputation_data = self.load_reputation_data()
        self.last_vip_spawn = 0
        self.spawned_characters = set()
        self.active_story_chains = {}
        # Add total_passengers tracking
        self.total_passengers = 0
        self.class_transports = {}
    
    def load_reputation_data(self):
        """Load reputation data from data/reputation.json"""
        try:
            with open("data/reputation.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            print("Error: reputation.json not found. Using default settings.")
            return {}
        except json.JSONDecodeError:
            print("Error: Could not parse reputation.json. Using default settings.")
            return {}

    def update_reputation(self, satisfaction, passenger=None):
        """Update passenger reputation based on satisfaction"""
        base_change = (satisfaction - 75) / 25  # -1 to +1 base change
        
        # Apply modifiers based on passenger class
        class_multipliers = self.reputation_data.get("class_multipliers", {
            "S": 1.5,  # Scientists
            "M": 1.3,  # Military
            "E": 1.4   # Engineers
        })
        
        # Get passenger's class if available
        if passenger and hasattr(passenger, 'classification'):
            passenger_class = passenger.classification.get('code', '')
            multiplier = class_multipliers.get(passenger_class, 1.0)
            if passenger_class not in self.class_transports:
                self.class_transports[passenger_class] = 0
            self.class_transports[passenger_class] += 1
        else:
            multiplier = 1.0
        
        reputation_change = base_change * multiplier
        
        # Apply final change and round to one decimal
        old_rep = self.game.ship.passenger_reputation
        self.game.ship.passenger_reputation = round(max(-100, min(100, 
            self.game.ship.passenger_reputation + reputation_change)), 1)
        
        # Check for threshold crossings
        self.check_reputation_thresholds(old_rep, self.game.ship.passenger_reputation)
        
        return round(reputation_change, 1)  # Also round the return value

    def check_reputation_thresholds(self, old_rep, new_rep):
        """Check if any reputation thresholds were crossed"""
        thresholds = self.reputation_data.get("thresholds", {})
        for threshold, title in thresholds.items():
            if old_rep < int(threshold) <= new_rep:
                self.game.display_simple_message([
                    f"Reputation Milestone Achieved: {title}!",
                    "Your excellent service is becoming legendary.",
                    f"Passenger Reputation: {int(new_rep)}"
                ])
                # Trigger appropriate events
                self.check_character_spawns()
                self.check_story_triggers()

    def check_character_spawns(self):
        """Check if it's time to spawn a VIP character"""
        current_turn = self.game.turn
        reputation = self.game.ship.passenger_reputation
        
        # Only spawn every 5 turns minimum
        if current_turn - self.last_vip_spawn < 5:
            return
            
        # Check VIP characters
        for char_type, data in self.reputation_data.get("vip_characters", {}).items():
            if (reputation >= data["rep_required"] and 
                char_type not in self.spawned_characters and
                random.random() < 0.3):  # 30% chance if all conditions met
                
                # Generate VIP character
                character = self.game.character_generators["human"].generate_character(
                    title=char_type,
                    specialization="VIP"
                )
                
                # Add to waiting passengers
                if self.game.current_location.name in self.game.port_system.waiting_passengers:
                    passenger = Passenger(
                        character.name,
                        random.choice(list(self.game.known_locations)),
                        wealth_level=5
                    )
                    passenger.is_vip = True
                    passenger.rewards = data["rewards"]
                    passenger.plot_points = data["plot_points"]
                    
                    self.game.port_system.waiting_passengers[
                        self.game.current_location.name].append(passenger)
                    
                    self.game.display_story_message([
                        f"VIP Passenger Available: {char_type} {character.name}",
                        "Your reputation has attracted important attention!",
                        f"Rewards: {self.game.format_money(data['rewards']['money'])} credits",
                        f"Plot Points: {data['plot_points']}"
                    ])
                    
                    self.spawned_characters.add(char_type)
                    self.last_vip_spawn = current_turn

    # Update to use enhanced systems of special passengers
    def spawn_special_passenger(self):
        """Spawn a special passenger using enhanced character systems"""
        # Check for story character triggers
        for trigger_id, trigger in self.game.character_system.character_triggers.items():
            if (trigger_id in ["galactic_alliance", "system_rebellion", "ancient_mysteries"] and
                trigger["condition"](self.game) and
                trigger_id not in self.game.character_system.active_characters):
                
                # Generate character and create event chain
                character = self.game.character_system.generate_character(trigger_id)
                event_chain = self.game.character_system.create_event_chain(
                    trigger["event_chain"],
                    character
                )
                
                # Add as special passenger
                self.add_special_passenger_to_port(character, event_chain)
                return True
                
        # Check for VIP passenger trigger
        if self.game.character_system.character_triggers["vip_passenger"]["condition"](self.game):
            vip_character = self.game.character_generators["special"].generate_vip_passenger()
            self.add_special_passenger_to_port(vip_character)
            return True
            
        return False

    def add_special_passenger_to_port(self, character, event_chain=None):
        """Add a special character as a passenger to the current port with full attributes

        Args:
            character: The special character to add
            event_chain: Optional event chain for story characters
        """
        if self.game.current_location.name in self.game.port_system.waiting_passengers:
            # Create base passenger with known destination
            available_destinations = [loc for loc in self.game.known_locations 
                                    if loc != self.game.current_location.name]
            if not available_destinations:
                return False  # Can't add passenger with no valid destinations
            
            passenger = Passenger(
                name=character.name,
                destination=random.choice(available_destinations),
                wealth_level=5  # Special characters are always high wealth
            )
            
            # Add base character attributes
            passenger.character = character
            passenger.is_special = True
            passenger.full_name = character.full_name
            passenger.title = character.title
            passenger.satisfaction = 100  # Start at max satisfaction
            
            # Handle different character types
            if event_chain:
                # Story character attributes
                passenger.is_story_character = True
                passenger.event_chain = event_chain
                passenger.specialization = character.specialization
                passenger.reputation_bonus = 20
                passenger.plot_points = 10
                message = [
                    f"Story Character Available: {character.title} {character.name}",
                    "This passenger seems to have an interesting story...",
                    f"Find them at the port in {self.game.current_location.name}",
                    "Their journey may unlock new story possibilities!"
                ]
                
            elif hasattr(character, 'rewards'):
                # VIP character attributes
                passenger.is_vip = True
                passenger.rewards = character.rewards
                passenger.special_abilities = getattr(character, 'special_abilities', [])
                passenger.reputation_bonus = 15
                passenger.classification = {
                    "code": "V",
                    "name": "VIP",
                    "type": character.specialization
                }
                message = [
                    f"VIP Passenger Available: {character.title} {character.name}",
                    f"Potential Reward: {self.game.format_money(character.rewards['base_money'])} credits",
                    f"Reputation Bonus: +{passenger.reputation_bonus}",
                    "Find them waiting at the port"
                ]
                if passenger.special_abilities:
                    message.append(f"Special Ability: {passenger.special_abilities[0]}")
                    
            elif character.title.startswith(("Neurodroid", "Agrobot")):
                # Synthetic character attributes
                passenger.is_synthetic = True
                passenger.uprising_chance = getattr(character, 'uprising_chance', 0.2)
                passenger.demands = getattr(character, 'demands', None)
                passenger.reputation_bonus = 25
                passenger.plot_points = 15
                message = [
                    f"Synthetic Entity Requesting Transport: {character.title}",
                    "This passenger represents significant risk and reward...",
                    f"Reputation Bonus: +{passenger.reputation_bonus}",
                    "Exercise caution in your decision"
                ]
            else:
                # Alien or other special character attributes
                passenger.is_alien = True
                passenger.culture = getattr(character, 'culture', 'Unknown')
                passenger.tech_bonus = getattr(character, 'tech_bonus', 0)
                passenger.trade_multiplier = getattr(character, 'trade_multiplier', 1.0)
                passenger.reputation_bonus = 18
                message = [
                    f"Alien Dignitary Available: {character.title} {character.name}",
                    f"Culture: {passenger.culture}",
                    f"Reputation Bonus: +{passenger.reputation_bonus}",
                    "This passenger may offer unique opportunities"
                ]
            
            # Add requirements for luxury accomodation
            passenger.minimum_comfort_level = 4  # Require high comfort level
            passenger.bonus_threshold = 90  # High satisfaction threshold for bonuses
            
            # Add to waiting passengers
            self.game.port_system.waiting_passengers[
                self.game.current_location.name].append(passenger)
            
            # Display announcement
            self.game.display_story_message(message)
            
            # Mark character as spawned
            self.spawned_characters.add(character.title)
            self.last_vip_spawn = self.game.turn
            
            return True
            
        return False

    def update_passenger_satisfaction(self):
        """Update passenger satisfaction during travel"""
        if not hasattr(self.game.ship, 'passenger_modules'):
            return
            
        for module in self.game.ship.passenger_modules:
            for passenger in module.passengers:
                # Base satisfaction change
                change = 0
                
                # Comfort level effect
                if module.comfort_level >= passenger.wealth_level:
                    change += 2  # Satisfied with comfort
                else:
                    change -= 3  # Dissatisfied with comfort
                    
                # Ship damage effect
                if self.game.ship.damage > 50:
                    change -= 5
                elif self.game.ship.damage > 25:
                    change -= 2
                    
                # Update satisfaction
                passenger.satisfaction = max(0, min(100, passenger.satisfaction + change))

    def get_fare_multiplier(self):
        """Get fare multiplier based on reputation"""
        reputation = self.game.ship.passenger_reputation
        if reputation >= 80:
            return 2.0
        elif reputation >= 60:
            return 1.5
        elif reputation >= 40:
            return 1.3
        elif reputation >= 20:
            return 1.1
        return 1.0
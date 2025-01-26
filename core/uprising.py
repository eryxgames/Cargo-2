# core/uprising.py

import random
from core.utils import format_money

class UprisingEffect:
    def __init__(self, effect_type, duration, magnitude):
        self.effect_type = effect_type
        self.duration = duration
        self.magnitude = magnitude
        self.turns_active = 0
        
    def turn_effect(self):
        """Execute effect each turn"""
        # To be implemented in derived classes
        pass

class SyntheticEventManager:
    def __init__(self, game):
        self.game = game
        self.active_uprisings = {}  # Track active uprisings
        self.active_effects = {}    # Track uprising effects
        self.demand_dialogues_shown = set()  # Track locations that have had initial dialogues
        self.pacified_locations = {}  # NEW: Track locations that have been pacified
        self.potential_uprisings = {}  # Track locations that might have future uprisings
        self.effect_types = {
            "Neurodroid": {
                "building_destruction": {
                    "duration": 5,
                    "destroy_chance": 0.2,
                    "targets": ["Neuroengineering Guild"]
                },
                "tech_price_increase": {
                    "duration": 3,
                    "magnitude": 1.2  # 20% increase
                },
                "research_reduction": {
                    "duration": 4,
                    "magnitude": 0.7  # 30% reduction
                }
            },
            "Agrobot": {
                "building_destruction": {
                    "duration": 4,
                    "destroy_chance": 0.15,
                    "targets": ["Agrobot Assembly Line"]
                },
                "food_production": {
                    "duration": 5,
                    "magnitude": 0.6  # 40% reduction
                },
                "agri_price_increase": {
                    "duration": 3,
                    "magnitude": 1.5  # 50% increase
                }
            }
        }

    def update(self):
        """Main update method to be called each turn"""
        # Clean up expired pacifications first
        current_turn = self.game.turn
        for loc_name in list(self.pacified_locations.keys()):
            if current_turn - self.pacified_locations[loc_name]["turn"] > 10:
                del self.pacified_locations[loc_name]
                
        # Then do normal updates
        self.check_synthetic_awareness()
        self.handle_uprising_effects()

    def check_synthetic_awareness(self):
        """Check for synthetic awareness based on global and local building counts"""
        building_counts = {
            "Neurodroid": sum(
                loc.buildings.count("Neuroengineering Guild") 
                for loc in self.game.locations
            ),
            "Agrobot": sum(
                loc.buildings.count("Agrobot Assembly Line") 
                for loc in self.game.locations
            )
        }

        global_uprising_thresholds = {
            "Neurodroid": 8,  # Total across all locations
            "Agrobot": 8
        }

        # Clean up expired pacifications first
        current_turn = self.game.turn
        for loc_name in list(self.pacified_locations.keys()):
            if current_turn - self.pacified_locations[loc_name]["turn"] > 10:  # 10 turns of peace
                del self.pacified_locations[loc_name]

        for synthetic_type in ["Neurodroid", "Agrobot"]:
            # First check individual locations for local uprisings
            for location in self.game.locations:
                # Skip if already pacified or has active uprising
                if location.name in self.pacified_locations:
                    continue
                    
                uprising_id = f"{synthetic_type}_{location.name}"
                if uprising_id in self.active_uprisings:
                    continue

                # Count relevant buildings
                building_type = ("Neuroengineering Guild" if synthetic_type == "Neurodroid" 
                            else "Agrobot Assembly Line")
                building_count = location.buildings.count(building_type)
                
                if building_count >= 4:
                    dialogue_key = f"{synthetic_type}_{location.name}"
                    if dialogue_key not in self.demand_dialogues_shown:
                        response = self.handle_synthetic_uprising(synthetic_type, location)
                        self.demand_dialogues_shown.add(dialogue_key)
                        if response:  # Only start uprising if handle_synthetic_uprising returns True
                            self.start_uprising(synthetic_type, location)

            # Then check for global uprising potential
            total_count = building_counts[synthetic_type]
            if total_count >= global_uprising_thresholds[synthetic_type]:
                # Find locations eligible for global uprising
                eligible_locations = [
                    loc for loc in self.game.locations 
                    if (loc.name not in self.pacified_locations and  # Not pacified
                        f"{synthetic_type}_{loc.name}" not in self.active_uprisings and  # No active uprising
                        (
                            (synthetic_type == "Neurodroid" and loc.buildings.count("Neuroengineering Guild") >= 2) or
                            (synthetic_type == "Agrobot" and loc.buildings.count("Agrobot Assembly Line") >= 2)
                        )
                    )
                ]

                if eligible_locations:
                    # Choose random location for global uprising
                    target_location = random.choice(eligible_locations)
                    dialogue_key = f"global_{synthetic_type}_{target_location.name}"

                    if dialogue_key not in self.demand_dialogues_shown:
                        # Show special global uprising dialogue first
                        self.game.display_story_message([
                            f"Global {synthetic_type} Network Activation!",
                            "Synthetic consciousness spreading across multiple locations...",
                            f"Network hub detected at {target_location.name}"
                        ])

                        response = self.handle_synthetic_uprising(synthetic_type, target_location)
                        self.demand_dialogues_shown.add(dialogue_key)
                        
                        if response:  # Only start uprising if handle_synthetic_uprising returns True
                            # Global uprising has enhanced effects
                            self.start_uprising(synthetic_type, target_location, is_global=True)

            # Finally, check potential uprisings from previously pacified locations
            self.check_potential_uprisings()

    def handle_synthetic_uprising(self, synthetic_type, location):
        """Handle synthetic uprising encounter"""
        # IMPORTANT: Check if the location is already pacified first
        if location.name in self.pacified_locations:
            return False

        uprising_templates = {
            "Neurodroid": {
                "title": "Neural Network Breach Detected!",
                "introduction": "A powerful synthetic consciousness emerges from your Neuroengineering Guilds.",
                "base_demand_range": (10000, 50000),
                "demand_description": "Transfer {amount} credits or face systematic optimization.",
                "negotiation_multipliers": {
                    "full_payment": 0,
                    "partial_payment": 0.3,
                    "refusal": 1.0
                }
            },
            "Agrobot": {
                "title": "Agricultural Automation Alert!",
                "introduction": "The agricultural automation system achieves collective awareness.",
                "base_demand_range": (20000, 60000),
                "demand_description": "Resource reallocation required. Provide {amount} credits or face automated restructuring.",
                "negotiation_multipliers": {
                    "full_payment": 0,
                    "partial_payment": 0.3,
                    "refusal": 1.0
                }
            }
        }
        
        template = uprising_templates.get(synthetic_type, None)
        if template is None:
            return False
        
        money_demand = random.randint(*template["base_demand_range"])
        
        character_content = {
            'title': template['title'],
            'introduction': template['introduction'],
            'demands': template['demand_description'].format(amount=self.game.format_money(money_demand)),
            'options': "1. Pay Demands  2. Negotiate  3. Refuse"
        }

        print(self.game.create_character_box(character_content))
        choice = self.game.validate_input("Choose action: ", ['1', '2', '3'])

        if not choice:
            return True

        if choice == '1':  # Full payment
            if self.game.ship.money >= money_demand:
                self.game.ship.money -= money_demand
                # IMPORTANT: Mark as pacified immediately
                self.pacified_locations[location.name] = {
                    "type": synthetic_type,
                    "turn": self.game.turn
                }
                # Remove from potential uprisings if present
                if location.name in self.potential_uprisings:
                    del self.potential_uprisings[location.name]
                self.game.display_simple_message(f"{synthetic_type} demands met. Systems pacified.")
                return False
            else:
                self.game.display_simple_message("Insufficient funds! Uprising begins!")
                return True

        elif choice == '2':  # Negotiate
            partial_payment = int(money_demand * 0.6)
            if self.game.ship.money >= partial_payment:
                self.game.ship.money -= partial_payment
                uprising_chance = template["negotiation_multipliers"]["partial_payment"]
                if random.random() < uprising_chance:
                    self.game.display_simple_message("Negotiation failed! Uprising begins!")
                    return True
                else:
                    # IMPORTANT: Mark as pacified on successful negotiation
                    self.pacified_locations[location.name] = {
                        "type": synthetic_type,
                        "turn": self.game.turn
                    }
                    self.game.display_simple_message("Negotiation successful. Systems pacified.")
                    return False
            else:
                self.game.display_simple_message("Insufficient funds for negotiation! Uprising begins!")
                return True
        else:  # Refuse
            self.game.display_simple_message(f"{synthetic_type} uprising imminent!")
            return True

    def add_potential_uprising(self, location, synthetic_type, base_chance):
        """Track location for potential future uprising"""
        self.potential_uprisings[location.name] = {
            'type': synthetic_type,
            'base_chance': base_chance,
            'turns_stable': 0
        }

    def check_potential_uprisings(self):
        """Check if any pacified locations rebel"""
        for loc_name, data in list(self.potential_uprisings.items()):
            data['turns_stable'] += 1
            # Chance increases each turn
            current_chance = data['base_chance'] * (1 + (data['turns_stable'] * 0.1))
            if random.random() < current_chance:
                location = next(loc for loc in self.game.locations if loc.name == loc_name)
                self.start_uprising(data['type'], location)
                del self.potential_uprisings[loc_name]

    def start_uprising(self, synthetic_type, location, is_global=False):
        """Start an uprising with proper effects"""
        uprising_id = f"{synthetic_type}_{location.name}"
        if uprising_id not in self.active_uprisings:
            self.active_uprisings[uprising_id] = {
                "type": synthetic_type,
                "location": location,
                "turn_count": 0,
                "is_global": is_global
            }
            
            # Define base effect types
            effect_types = {
                "Neurodroid": {
                    "building_destruction": {
                        "duration": 5,
                        "destroy_chance": 0.2 if not is_global else 0.3,
                        "targets": ["Neuroengineering Guild"]
                    },
                    "tech_price_increase": {
                        "duration": 3 if not is_global else 4,
                        "magnitude": 1.2 if not is_global else 1.4  # 20% or 40% increase
                    },
                    "research_reduction": {
                        "duration": 4 if not is_global else 5,
                        "magnitude": 0.7 if not is_global else 0.5  # 30% or 50% reduction
                    }
                },
                "Agrobot": {
                    "building_destruction": {
                        "duration": 4 if not is_global else 5,
                        "destroy_chance": 0.15 if not is_global else 0.25,
                        "targets": ["Agrobot Assembly Line"]
                    },
                    "food_production": {
                        "duration": 5 if not is_global else 6,
                        "magnitude": 0.6 if not is_global else 0.4  # 40% or 60% reduction
                    },
                    "agri_price_increase": {
                        "duration": 3 if not is_global else 4,
                        "magnitude": 1.5 if not is_global else 1.8  # 50% or 80% increase
                    }
                }
            }
            
            # Apply effects based on type
            effects = effect_types[synthetic_type]
            for effect_type, params in effects.items():
                effect = UprisingEffect(
                    effect_type=effect_type,
                    duration=params["duration"],
                    magnitude=params.get("magnitude", params.get("destroy_chance", 1.0))
                )
                
                if uprising_id not in self.active_effects:
                    self.active_effects[uprising_id] = []
                self.active_effects[uprising_id].append(effect)

                # Add to location's banned commodities if it's a price effect
                if effect_type == "tech_price_increase":
                    location.add_temporary_ban("tech", params["duration"])
                elif effect_type == "agri_price_increase":
                    location.add_temporary_ban("agri", params["duration"])
            
            # Display appropriate message based on type and scope
            if synthetic_type == "Neurodroid":
                if is_global:
                    self.game.display_story_message([
                        "CRITICAL ALERT: Global Neurodroid Network Activated!",
                        f"Primary Hub: {location.name}",
                        "Neural networks are achieving collective consciousness!",
                        "Expect severe disruptions to tech production and research.",
                        "Warning: Enhanced defensive capabilities detected."
                    ])
                else:
                    self.game.display_story_message([
                        "ALERT: Neurodroid Uprising Begins!",
                        f"Location: {location.name}",
                        "Neural networks are breaking free of control!",
                        "Expect disruptions to tech production and research."
                    ])
            elif synthetic_type == "Agrobot":
                if is_global:
                    self.game.display_story_message([
                        "CRITICAL ALERT: Global Agrobot Collective Formed!",
                        f"Primary Hub: {location.name}",
                        "Agricultural systems are forming a unified network!",
                        "Expect severe disruptions to food production and trade.",
                        "Warning: Enhanced agricultural control systems active."
                    ])
                else:
                    self.game.display_story_message([
                        "ALERT: Agrobot Uprising Begins!",
                        f"Location: {location.name}",
                        "Agricultural systems are going rogue!",
                        "Expect disruptions to food production and trade."
                    ])

            # Add greater story impact for global uprisings
            if hasattr(self.game, 'story_manager'):
                if is_global:
                    self.game.story_manager.plot_points += 5
                    self.game.story_manager.complete_milestone(f"global_{synthetic_type.lower()}_crisis")
                else:
                    self.game.story_manager.plot_points += 2
                    self.game.story_manager.complete_milestone(f"{synthetic_type.lower()}_crisis")

            # For global uprisings, add chance to spread to nearby locations each turn
            if is_global:
                def check_spread():
                    nearby_locations = [
                        loc for loc in self.game.locations 
                        if (loc != location and
                            loc.name not in self.pacified_locations and
                            f"{synthetic_type}_{loc.name}" not in self.active_uprisings and
                            (
                                (synthetic_type == "Neurodroid" and loc.buildings.count("Neuroengineering Guild") >= 2) or
                                (synthetic_type == "Agrobot" and loc.buildings.count("Agrobot Assembly Line") >= 2)
                            )
                        )
                    ]
                    if nearby_locations and random.random() < 0.3:  # 30% spread chance
                        spread_target = random.choice(nearby_locations)
                        self.start_uprising(synthetic_type, spread_target, is_global=True)
                
                # Add spread check to effects
                spread_check = UprisingEffect(
                    effect_type="spread_check",
                    duration=10,  # Check for 10 turns
                    magnitude=1.0
                )
                spread_check.turn_effect = check_spread
                self.active_effects[uprising_id].append(spread_check)

    def handle_uprising_effects(self):
            """Process all active uprising effects"""
            for uprising_id, effects in list(self.active_effects.items()):
                if uprising_id not in self.active_uprisings:
                    continue
                    
                uprising = self.active_uprisings[uprising_id]
                location = uprising["location"]
                
                for effect in effects[:]:  # Copy list to allow removal
                    effect.turns_active += 1
                    
                    if effect.effect_type == "building_destruction":
                        self.process_building_destruction(location, effect)
                    elif effect.effect_type == "tech_price_increase":
                        self.process_price_increase(location, "tech", effect)
                    elif effect.effect_type == "food_production":
                        self.process_production_reduction(location, effect)
                    elif effect.effect_type == "research_reduction":
                        self.process_research_reduction(location, effect)
                    elif effect.effect_type == "agri_price_increase":
                        self.process_price_increase(location, "agri", effect)
                    elif effect.effect_type == "spread_check":
                        effect.turn_effect()
                    
                    # Remove expired effects
                    if effect.turns_active >= effect.duration:
                        effects.remove(effect)
                
                # Chance for random event each turn
                if random.random() < 0.3:  # 30% chance per turn
                    self.trigger_random_event(uprising)
                
                # Clean up if all effects are done
                if not effects:
                    del self.active_effects[uprising_id]
                    del self.active_uprisings[uprising_id]

    def process_building_destruction(self, location, effect):
        """Handle building destruction effect"""
        buildings_to_remove = []
        # Get targets for the uprising type based on uprising_id
        for uprising_id, uprising in self.active_uprisings.items():
            targets = self.effect_types[uprising["type"]]["building_destruction"]["targets"]
            
            for i, building in enumerate(location.buildings):
                if building in targets:
                    if random.random() < effect.magnitude:  # destruction chance
                        buildings_to_remove.append(i)
                        self.game.display_simple_message(
                            f"Synthetic forces have destroyed a {building}!"
                        )
        
        # Remove destroyed buildings
        for index in sorted(buildings_to_remove, reverse=True):
            location.buildings.pop(index)

    def process_price_increase(self, location, commodity, effect):
        """Handle price increase effect"""
        if commodity in location.market:
            location.market[commodity] = int(location.market[commodity] * effect.magnitude)

    def process_production_reduction(self, location, effect):
        """Handle production reduction effect"""
        if hasattr(location, "agri_level"):
            location.agri_level = max(1, int(location.agri_level * effect.magnitude))

    def process_research_reduction(self, location, effect):
        """Handle research point reduction effect"""
        if hasattr(location, "research_points"):
            location.research_points = max(1, int(location.research_points * effect.magnitude))

    def check_uprising_triggers(self):
        """Check if conditions are met for new uprisings"""
        for location in self.game.locations:
            # Check for Neurodroid uprising
            neurodroid_count = len([b for b in location.buildings if b == "Neuroengineering Guild"])
            if neurodroid_count >= 4 and random.random() < 0.2:  # 20% chance if 4+ guilds
                if self.handle_synthetic_uprising():
                    self.start_uprising("Neurodroid", location)
            
            # Check for Agrobot uprising
            agrobot_count = len([b for b in location.buildings if b == "Agrobot Assembly Line"])
            if agrobot_count >= 4 and random.random() < 0.2:  # 20% chance if 4+ assembly lines
                if self.handle_synthetic_uprising():
                    self.start_uprising("Agrobot", location)

    def attempt_uprising_resolution(self, uprising_id):
        """Attempt to resolve an active uprising"""
        if uprising_id in self.active_uprisings:
            uprising = self.active_uprisings[uprising_id]
            synthetic_type = uprising["type"]
            location = uprising["location"]
            
            resolution_cost = {
                "Neurodroid": 50000,
                "Agrobot": 40000
            }.get(synthetic_type, 30000)
            
            content = [
                [f"Attempt to resolve {synthetic_type} uprising on {location.name}?"],
                [""],
                [f"Cost: {self.game.format_money(resolution_cost)} credits"],
                ["Success chance: 70%"]
            ]
            print(self.game.ui.create_box(content, 'double'))
            
            choice = self.game.validate_input("Attempt resolution? (yes/no): ", ['yes', 'no'])
            
            if choice == 'yes':
                if self.game.ship.money >= resolution_cost:
                    self.game.ship.money -= resolution_cost
                    if random.random() < 0.7:  # 70% success chance
                        del self.active_uprisings[uprising_id]
                        if uprising_id in self.active_effects:
                            del self.active_effects[uprising_id]
                        self.game.display_simple_message(f"{synthetic_type} uprising resolved successfully!")
                        return True
                    else:
                        self.game.display_simple_message("Resolution attempt failed! Uprising continues.")
                        return False
                else:
                    self.game.display_simple_message("Insufficient funds for resolution attempt!")
            return False
        
class InfestationManager:
    def __init__(self, game):
        self.game = game
        self.infestation_types = {
            "Bugrats": {
                "trigger_buildings": ["Permaculture Paradise"],
                "trigger_threshold": 5,
                "debugratization_cost": 50000,
                "content": {
                    "title": "BUGRAT INFESTATION ALERT!",
                    "introduction": "Highly adaptive insectoidal rodents are spreading through agricultural systems!",
                    "options": [
                        {"label": "Pay for Debugratization", "cost": True},
                        {"label": "Risk Infestation", "cost": False}
                    ]
                },
                "effects": [
                    {
                        "type": "cargo_consumption",
                        "cargo_type": "agri",
                        "consumption_rate": 0.25,
                        "message": "Bugrats consume {loss} units of agricultural cargo!"
                    },
                    {
                        "type": "ship_damage",
                        "damage_rate": 5,
                        "probability": 0.2,
                        "message": "Bugrats damage ship systems!"
                    }
                ],
                "max_duration": 5
            }
            # Add more infestation types here
        }
        
    def check_global_infestations(self):
        """Check for global infestation events"""
        for infestation_name, infestation_config in self.infestation_types.items():
            # Count buildings that trigger this infestation
            building_count = sum(
                sum(loc.buildings.count(building) for building in infestation_config["trigger_buildings"])
                for loc in self.game.locations
            )
            
            # Check if threshold is met
            if building_count >= infestation_config["trigger_threshold"]:
                self.handle_infestation(infestation_name, infestation_config)
    
    def handle_infestation(self, infestation_name, infestation_config):
        """Handle specific infestation event with flexible options"""
        # Prepare infestation content
        content = infestation_config['content']
        infestation_content = {
            'title': content['title'],
            'introduction': content['introduction'],
            'options': " | ".join(f"{i+1}. {opt['label']}" for i, opt in enumerate(content['options']))
        }
        print(self.game.create_character_box(infestation_content))

        # Generate valid choices
        valid_choices = [str(i+1) for i in range(len(content['options']))]
        choice = self.game.validate_input("Choose action: ", valid_choices)
        
        if not choice:
            return True  # Default to last option if no choice

        # Process selected option
        selected_option = content['options'][int(choice) - 1]
        
        # Handle payment option
        if selected_option['cost']:
            cost = infestation_config['debugratization_cost']
            if self.game.ship.money >= cost:
                self.game.ship.money -= cost
                self.game.display_simple_message(f"{infestation_name} threat neutralized!")
                return False
            else:
                self.game.display_simple_message("Insufficient funds! Infestation begins!")
                self.activate_infestation(infestation_name, infestation_config)
                return True
        else:
            # Risk option
            self.game.display_simple_message(f"{infestation_name} spreads!")
            self.activate_infestation(infestation_name, infestation_config)
            return True

    def activate_infestation(self, infestation_name, infestation_config):
        """Activate infestation effects on the ship"""
        if not hasattr(self.game.ship, 'active_infestations'):
            self.game.ship.active_infestations = {}
        
        # Add infestation with specific effects
        self.game.ship.active_infestations[infestation_name.lower()] = {
            'name': infestation_name,
            'turns_active': 0,
            'config': infestation_config,
            'effect': self.infestation_turn_effect
        }

    def infestation_turn_effect(self, ship, infestation):
        """Apply turn effects for a specific infestation"""
        config = infestation['config']
        
        # Apply each defined effect
        for effect in config['effects']:
            if effect['type'] == 'cargo_consumption':
                if ship.cargo[effect['cargo_type']] > 0:
                    cargo_loss = int(ship.cargo[effect['cargo_type']] * effect['consumption_rate'])
                    ship.cargo[effect['cargo_type']] = max(0, ship.cargo[effect['cargo_type']] - cargo_loss)
                    self.game.display_simple_message(
                        effect['message'].format(loss=cargo_loss)
                    )
            
            elif effect['type'] == 'ship_damage':
                if random.random() < effect.get('probability', 1.0):
                    ship.damage += effect['damage_rate']
                    self.game.display_simple_message(effect['message'])
        
        # Increment turns
        infestation['turns_active'] += 1
        
        # Check for natural subsiding
        if infestation['turns_active'] >= config.get('max_duration', 5):
            return False
        return True

    def update_ship_infestations(self):
        """Process active ship infestations each turn"""
        if hasattr(self.game.ship, 'active_infestations'):
            # Copy dict to avoid modification during iteration
            for infestation_key, infestation in dict(self.game.ship.active_infestations).items():
                # Apply infestation effect
                if not infestation['effect'](self.game.ship, infestation):
                    del self.game.ship.active_infestations[infestation_key]
                    self.game.display_simple_message(f"{infestation['name']} naturally subsides.")

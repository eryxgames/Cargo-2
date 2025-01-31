# core/ship.py
import random
import csv
import json
import os

class PassengerModule:
    def __init__(self, name, capacity, comfort_level, cost):
        self.name = name
        self.capacity = capacity  # How many passengers it can hold
        self.comfort_level = comfort_level  # 1-5, affects passenger satisfaction and payment
        self.cost = cost
        self.passengers = []

class Passenger:
    def __init__(self, name, destination, wealth_level):
        self.name = name
        self.destination = destination
        self.wealth_level = wealth_level  # 1-5
        self.satisfaction = 100
        self.turns_waiting = 0
        # Add passenger classification
        self.classification = self.generate_classification()
    
    def generate_classification(self):
        classifications = [
            ("S", "Scientist", "science"),
            ("M", "Military", "military"),
            ("E", "Engineer", "engineering"),
            ("T", "Trader", "trade"),
            ("D", "Diplomat", "diplomacy"),
             ("R", "Researcher", "research")
        ]
        class_code, class_name, class_type = random.choice(classifications)
        return {
            "code": class_code,
            "name": class_name,
            "type": class_type
        }

class Ship:
    def __init__(self, game=None):
        self.game = game
        # Basic cargo and resources
        self.cargo = {
            'tech': 0,
            'agri': 0,
            'salt': 0,
            'fuel': 0
        }
        self.money = 1000
        self.damage = 0
        self.research_points = 0

        # Ship stats
        self.attack = 1
        self.defense = 1
        self.speed = 1
         # Tracking total modifiers
        self.total_attack_modifier = 0
        self.total_defense_modifier = 0
        self.total_speed_modifier = 0
        
        # Equipment and upgrades
        self.upgrades = [] # Track applied upgrades
        self.items = {}
        
        # Removed upgrade_costs - no longer used
        # self.upgrade_costs = {
        #   'attack': 2000,
        #   'defense': 2000,
        #   'speed': 2000
        # }
        
        # Item tracking
        self.item_purchase_count = {}
        
        # Combat statistics
        self.combat_victories = {
            'total': 0,
            'pirate': 0,
            'raider': 0,
            'militia': 0,
            'alien': 0
        }
        self.combat_defeats = {
            'total': 0,
            'pirate': 0,
            'raider': 0,
            'militia': 0,
            'alien': 0
        }
        self.combat_stats = {
            'pirates_defeated': 0,
            'raiders_defeated': 0,
            'militia_defeated': 0,
            'defeats_by_type': {}
        }
        
        # Trade statistics
        self.trade_profits = {}
        
        # Enemy-specific victories
        self.enemy_victories = {
            'pirate': 0,
            'raider': 0,
            'militia': 0,
            'alien': 0
        }

                 # Initialize passenger-related attributes
        self.passenger_modules = []
        self.passenger_reputation = 0
        
        # Load items
        self.load_items()

    def load_items(self):
        """Load item data from the CSV file and store for later use"""
        self.item_data = {}
        try:
            with open("data/items.csv", 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.item_data[row['item_id']] = row
        except FileNotFoundError:
            print("Error: items.csv not found. Using default item data.")
            self.item_data = {}
            
    def get_item_effects(self, item_id):
         """Get the effects for a specific item and parse them"""
         item_data = self.item_data.get(item_id)
         if not item_data or 'effects' not in item_data:
             return {}
         
         effects = {}
         effect_str = item_data['effects']
         if effect_str:
             for effect_pair in effect_str.split(','):
                 if ':' in effect_pair:
                     effect_name, effect_value = effect_pair.split(':')
                     try:
                         effects[effect_name] = float(effect_value)
                     except ValueError:
                         effects[effect_name] = effect_value  # Allow strings if parsing fails
                         
         return effects

    def add_starting_items(self, starting_items):
        """Add starting items to the player inventory"""
        for item, quantity in starting_items.items():
            if item in self.items:
              self.items[item] += quantity
            else:
              self.items[item] = quantity

    def acquire_item(self, item_name):
        if item_name in self.items:
            self.items[item_name] += 1
        else:
            self.items[item_name] = 1
            
        # Apply effects immediately on purchase
        effects = self.get_item_effects(item_name)
        for effect_name, effect_value in effects.items():
            if effect_name == 'damage_reduction':
                self.defense += effect_value
            elif effect_name == 'auto_defense_chance':
                if not hasattr(self, 'auto_defense_chance'):
                    self.auto_defense_chance = 0
                self.auto_defense_chance += effect_value
            elif effect_name == 'scout_bonus':
                if not hasattr(self, 'scout_bonus'):
                    self.scout_bonus = 0
                self.scout_bonus += effect_value
            elif effect_name == 'explore_bonus':
                if not hasattr(self, 'explore_bonus'):
                    self.explore_bonus = 0
                self.explore_bonus += effect_value
            elif effect_name == 'repair':
                if not hasattr(self, 'repair_bonus'):
                    self.repair_bonus = 0
                self.repair_bonus += effect_value
            elif effect_name in ['cargo_capacity', 'cargo_capacity_salt_fuel', 'cargo_capacity_mining', 'cargo_capacity_special']:
                setattr(self, effect_name, getattr(self, effect_name, 1) + effect_value)
            elif effect_name == "threat_detection":
                if not hasattr(self, 'threat_detection'):
                    self.threat_detection = 0
                self.threat_detection += effect_value
            elif effect_name == "combat_bonus":
                self.attack += effect_value
            elif effect_name == "trade_time_reduction":
                if not hasattr(self, 'trade_time_reduction'):
                    self.trade_time_reduction = 0
                self.trade_time_reduction += int(effect_value)
            elif effect_name == "mining_efficiency":
                if not hasattr(self, 'mining_efficiency'):
                    self.mining_efficiency = 0
                self.mining_efficiency += effect_value
            elif effect_name == "mining_detection":
                if not hasattr(self, 'mining_detection'):
                   self.mining_detection = 0
                self.mining_detection += effect_value
            elif effect_name == "defense_bonus_asteroid":
                if not hasattr(self, 'defense_bonus_asteroid'):
                    self.defense_bonus_asteroid = 0
                self.defense_bonus_asteroid += effect_value
            elif effect_name == "auto_repair":
                if not hasattr(self, 'auto_repair'):
                    self.auto_repair = 0
                self.auto_repair += effect_value    
            elif effect_name == "escape_chance":
                if not hasattr(self, 'escape_chance'):
                    self.escape_chance = 0
                self.escape_chance += effect_value
            elif effect_name == "research_bonus":
                if not hasattr(self, 'research_bonus'):
                    self.research_bonus = 0
                self.research_bonus += effect_value
            elif effect_name == "research_success":
                if not hasattr(self, 'research_success'):
                    self.research_success = 0
                self.research_success += effect_value
            elif effect_name == "anomalies_chance":
                if not hasattr(self, 'anomalies_chance'):
                    self.anomalies_chance = 0
                self.anomalies_chance += effect_value
            elif effect_name == "quantum_bonus":
                if not hasattr(self, 'quantum_bonus'):
                    self.quantum_bonus = 0
                self.quantum_bonus += effect_value
            elif effect_name == "stealth_ability":
                 if not hasattr(self, 'stealth_ability'):
                    self.stealth_ability = 0
                 self.stealth_ability += effect_value
         
    def repair(self, cost):
        if self.money >= cost:
            self.money -= cost
            self.damage = 0
            return True
        return False

    def apply_upgrade(self, upgrade_data):
        """Apply ship upgrades using data structure"""
        if upgrade_data["type"] == "ship_upgrade":
            if upgrade_data["name"] in self.upgrades:
                return False  # Return false, if upgrade already purchased.
            if "effects" in upgrade_data:
               for stat, value in upgrade_data["effects"].items():
                    if stat in ['attack', 'defense', 'speed']:
                        setattr(self, stat, max(1, int(getattr(self, stat, 0) + value))) # Prevent it to go below 1, and cast to int.
                        if stat == 'attack':
                            self.total_attack_modifier += value
                        if stat == 'defense':
                            self.total_defense_modifier += value
                        if stat == 'speed':
                            self.total_speed_modifier += value

            self.upgrades.append(upgrade_data['name'])
            return True
        return False

    def record_combat_victory(self, enemy_type=None):
            """Record a combat victory with proper type tracking"""
            self.combat_victories['total'] += 1
            if enemy_type:
                if enemy_type in self.combat_victories:
                    self.combat_victories[enemy_type] += 1

    def record_combat_defeat(self, enemy_type=None):
         """Record a combat defeat with proper type tracking"""
         self.combat_defeats['total'] += 1
         if enemy_type:
             if enemy_type in self.combat_defeats:
                 self.combat_defeats[enemy_type] += 1
    
    # Existing methods for buying and selling items

    def buy(self, item, quantity, price, planet, player_rank):
        if not planet.can_trade(item):
            return False

        if item in ['salt', 'fuel']:
            has_platform = any(p['type'] == item for p in planet.mining_platforms)
            if not has_platform:
                return False

        cost = quantity * price
        if self.money >= cost:
            #tax_rate = planet.calculate_tax_rate(player_rank, cost)
            tax_rate = planet.calculate_tax_rate(player_rank, cost, self.game)
            tax_amount = cost * tax_rate
            total_cost = cost + tax_amount
            
            if self.money >= total_cost:
                self.money -= total_cost
                self.cargo[item] += quantity
                
                # Add contract progress tracking for buy events
                if hasattr(self, 'game') and hasattr(self.game, 'contract_manager'):
                    event_data = {
                        "action": "buy",
                        "commodity": item,
                        "amount": quantity,
                        "location": planet.name,
                        "turn": self.game.turn
                    }
                    self.game.contract_manager.update_contract_progress(event_data)
                
                return True
            return False
        return False

    def sell(self, item, quantity, price, planet, player_rank):
        if not planet.can_trade(item):
            return False

        if item in ['salt', 'fuel']:
            has_platform = any(p['type'] == item for p in planet.mining_platforms)
            if not has_platform:
                return False
                
        if self.cargo[item] >= quantity:
            revenue = quantity * price
            #tax_rate = planet.calculate_tax_rate(player_rank, revenue)
            tax_rate = planet.calculate_tax_rate(player_rank, revenue, self.game)
            tax_amount = revenue * tax_rate
            net_revenue = revenue - tax_amount
            
            self.money += net_revenue
            self.cargo[item] -= quantity
            
            # Track trade profits
            if item not in self.trade_profits:
                self.trade_profits[item] = 0
            self.trade_profits[item] += net_revenue
            
            # Add contract progress tracking for sell events
            if hasattr(self, 'game') and hasattr(self.game, 'contract_manager'):
                event_data = {
                    "action": "sell",
                    "commodity": item,
                    "amount": quantity,
                    "location": planet.name,
                    "turn": self.game.turn
                }
                self.game.contract_manager.update_contract_progress(event_data)
            
            return True
        return False

    def is_empty_cargo(self):
        return all(amount == 0 for amount in self.cargo.values())
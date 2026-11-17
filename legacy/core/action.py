# core/action.py
import random

class ActionResult:
    def __init__(self, success, type_=None, value=None, message=""):
        self.success = success
        self.type = type_
        self.value = value
        self.message = message

    def get_message(self):
        return self.message
    
    def is_success(self):
        return self.success

    def get_type(self):
         return self.type
    
    def get_value(self):
        return self.value
    

class Action:
    def __init__(self, game):
        self.game = game
        self.action_data = self.load_action_data() #load from file
    
    def load_action_data(self):
         """Load action data from data/actions.yml"""
         try:
            with open("data/actions.yml", 'r') as f:
                import yaml
                data = yaml.safe_load(f)
                return data.get("action_options", {})
         except FileNotFoundError:
             print("Error: actions.yml not found. Using default action data.")
             return {}
         except yaml.YAMLError as e:
             print(f"Error loading actions from YAML: {e}")
             return {}
    
    def get_action_cost(self, action_key):
          """Get action cost"""
          return self.action_data.get(action_key, {}).get('cost', 0)
    
    def get_action_requirements(self, action_key):
        """Get tech level and plot point requirements for a research option"""
        action = self.action_data.get(action_key, {})
        return {
            "plot_points": int(action.get("plot_points", 0)),
            "requires": action.get("requires", [])
        }

    def check_location_requirements(self, action_key, location):
        """Check location requirements"""
        action = self.action_data.get(action_key, {})
        
        # Check if action is available at any location, if `location_types` is not specified
        location_types = action.get("location_types", [])
        if location_types and location.location_type not in location_types:
           return False
           
        # Check for economy requirements
        economy_requirements = action.get("location_requirements", {}).get("economy", [])
        if economy_requirements and location.economy not in economy_requirements:
            return False
        
        # Check affiliation requirements
        affiliation_requirements = action.get("location_requirements", {}).get("affiliation", [])
        if affiliation_requirements and location.affiliation not in affiliation_requirements:
           return False
        
        # Check for min relation to player
        relation_requirement = action.get("location_requirements", {}).get("min_relation_to_player", 0)
        try:
           if isinstance(location.relation_to_player, str):
               relation_map = {
                    "Hostile": -2,
                    "Enemy": -1,
                    "Neutral": 0,
                    "Calm": 1,
                    "Friendly": 2,
                    "Ally": 3
                 }
               relation_value = relation_map.get(location.relation_to_player, None)
               if relation_value is not None:
                  if relation_value < relation_requirement:
                      return False
           elif isinstance(location.relation_to_player, int):
              if location.relation_to_player < relation_requirement:
                 return False
           else:
             print(f"Warning: Could not convert location.relation_to_player {location.relation_to_player} to int, or find it in relation map")
             return False
        except ValueError:
             print(f"Warning: Could not convert location.relation_to_player {location.relation_to_player} to int")
             return False
            
        return True

    def scout_area(self, location):
        """
        Scout the area for resources or items
        Returns: (bool success, str type, any value, str message)
        """
        action = self.action_data.get('scout', {})
        success_chance = action.get("effects",{}).get('scout_success', 0.65)
        if 'telemetry' in self.game.research.unlocked_options:
            success_chance += self.game.research.research_benefits.get('telemetry', {}).get('scout_success', 0)
            
        if random.random() < success_chance:
            discovery_type = random.choice(['tech', 'agri', 'item'])
            
            if discovery_type == 'item':
                item = random.choice(['scanner', 'probe', 'turrets', 'shield'])
                return ActionResult(True, 'item', item, f"Found a {item}!")
            else:
                amount = random.randint(10, 30)
                return ActionResult(True, discovery_type, amount, f"Found {amount} units of {discovery_type}!")
        
        return ActionResult(False, message="Scouting attempt failed!")

    def geoscan(self, location):
        """
        Scan for mineral deposits
        Returns: (bool success, str deposit_type, int amount, str message)
        """
        action = self.action_data.get('geoscan', {})
        success_chance = action.get("effects",{}).get('geoscan_success', 0.70)
        
        if 'geophysics' in self.game.research.unlocked_options:
            success_chance += self.game.research.research_benefits.get('geophysics', {}).get('exogeology', 0)
            
        if random.random() < success_chance:
            deposit_type = random.choice(['salt', 'fuel'])
            amount = random.randint(1000, 5000)
            
            if deposit_type not in location.mineral_deposits:
                location.mineral_deposits[deposit_type] = amount
                return ActionResult(True, deposit_type, amount, f"Found {amount} units of {deposit_type} deposits!")
            else:
                bonus = random.randint(500, 1000)
                location.mineral_deposits[deposit_type] += bonus
                return ActionResult(True, deposit_type, bonus, f"Found additional {bonus} units of {deposit_type} deposits!")
                
        return ActionResult(False, message="Geoscan failed to find any deposits!")

    def incite_revolution(self, location):
      """
      Attempt to change planet's economy and remove trade bans.
      Returns: (bool success, str new_economy, str message)
      """
      action = self.action_data.get('revolution', {})
      success_chance = action.get("effects",{}).get('revolution_success', 0.50)
      if 'chronopolitics' in self.game.research.unlocked_options:
            success_chance += self.game.research.research_benefits.get('chronopolitics', {}).get('revolution_success', 0)
            
      if random.random() < success_chance:
          current_economy = location.economy
          possible_economies = ['Booming', 'Stable', 'Declining', 'Formative']
          possible_economies.remove(current_economy)
          new_economy = random.choice(possible_economies)
          location.economy = new_economy
          # Clear trade bans
          location.banned_commodities = []
          location.ban_duration.clear()
          return ActionResult(True, new_economy, message=f"Revolution successful! Economy changed to {new_economy} and trade bans removed!")
      
      return ActionResult(False, message="Revolution attempt failed!")
    
    def manipulate_market(self, location, commodity):
        """
        Attempt to manipulate market prices
        Returns: (bool success, float price_change, str message)
        """
        action = self.action_data.get('market_manipulation', {})
        success_chance = action.get("effects",{}).get('manipulation_success', 0.60)
        
        research_system = self.game.research
        if random.random() < success_chance:
            manipulation_power = research_system.research_benefits.get('psychodynamics', {}).get('price_control',0)
            current_price = location.market[commodity]
            
            # Determine direction of manipulation (increase/decrease)
            direction = random.choice([-1, 1])
            change = direction * random.uniform(0.1, manipulation_power) * current_price
            
            # Apply change with bounds checking
            new_price = max(1, current_price + change)
            if commodity == 'salt':
                new_price = min(new_price, 150)
            elif commodity == 'fuel':
                new_price = min(new_price, 250)
            else:
                new_price = min(new_price, 200)
                
            location.market[commodity] = new_price
            price_change = new_price - current_price
            return ActionResult(True, value=price_change, message=f"Successfully manipulated {commodity} price by {abs(price_change):.1f}!")
            
        return ActionResult(False, message="Market manipulation attempt failed!")

    def build_mining_platform(self, location, deposit_type):
         """Build a new mining platform"""
         cost = 10000
         if self.game.ship.money >= cost:
            if location.build_mining_platform(deposit_type, cost):
                 self.game.ship.money -= cost
                 return ActionResult(True, message=f"Mining platform for {deposit_type} built!")
         return ActionResult(False, message="Not enough money to build mining platform")

    def establish_trade_route(self, location):
         """Establish a new trade route on location"""
         action = self.action_data.get('establish_trade_route', {})
         bonus = action.get("effects",{}).get('trade_bonus', 0.1)

         location.trade_bonus = bonus
         return ActionResult(True, message=f"Trade route established at {location.name} - trade bonus {bonus}!")
    
    def destabilize_economy(self, location):
        """Attempt to destabilize economy, which lowers tax revenue"""
        action = self.action_data.get('destabilize', {})
        success_chance = action.get("effects",{}).get('revolution_success', 0.50)
        
        if random.random() < success_chance:
            current_economy = location.economy
            possible_economies = ['Booming', 'Stable', 'Declining', 'Formative']
            possible_economies.remove(current_economy)
            new_economy = random.choice(possible_economies)
            location.economy = new_economy
            
            return ActionResult(True, new_economy, message=f"Destabilization successful! Economy changed to {new_economy}!")
        return ActionResult(False, message="Destabilization attempt failed!")
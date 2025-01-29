# core/action.py
import random

class Action:
    def __init__(self, game):
        self.game = game
        self.action_data = self.load_action_data() #load from file
        
        self.base_success_rates = {
            'scout': 0.65,
            'geoscan': 0.70,
            'revolution': 0.50,
            'psychodynamics': 0.60
        }
    
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

    def research(self, location, option):
        """
        Attempt to research a new technology
        Returns: (bool success, str message)
        """
        research_system = self.game.research
        if option in research_system.unlocked_options:
            return False, "This research has already been completed."
            
        # Apply immediate benefits based on research type
        if option == 'exogeology':
            location.exogeology = min(100, 
                int(location.exogeology * (1 + research_system.research_benefits.get(option,{}).get('output_bonus', 0))))
        
        self.game.handle_research_gain(research_system.research_costs.get(option, 0))  # Track research, using get to avoid error if key not found
        return True, f"Successfully researched {option}!"

    def scout_area(self, location):
        """
        Scout the area for resources or items
        Returns: (bool success, str type, any value, str message)
        """
        research_system = self.game.research
        # Calculate success chance
        success_chance = self.base_success_rates['scout']
        if 'telemetry' in research_system.unlocked_options:
            success_chance += research_system.research_benefits.get('telemetry', {}).get('scout_success', 0)
            
        if random.random() < success_chance:
            discovery_type = random.choice(['tech', 'agri', 'item'])
            
            if discovery_type == 'item':
                item = random.choice(['scanner', 'probe', 'turrets', 'shield'])
                return True, 'item', item, f"Found a {item}!"
            else:
                amount = random.randint(10, 30)
                return True, discovery_type, amount, f"Found {amount} units of {discovery_type}!"
        
        return False, None, None, "Scouting attempt failed!"

    def geoscan(self, location):
        """
        Scan for mineral deposits
        Returns: (bool success, str deposit_type, int amount, str message)
        """
        research_system = self.game.research
        # Calculate success chance
        success_chance = self.base_success_rates['geoscan']
        if 'geophysics' in research_system.unlocked_options:
            success_chance += research_system.research_benefits.get('geophysics', {}).get('exogeology', 0)
            
        if random.random() < success_chance:
            deposit_type = random.choice(['salt', 'fuel'])
            amount = random.randint(1000, 5000)
            
            if deposit_type not in location.mineral_deposits:
                location.mineral_deposits[deposit_type] = amount
                return True, deposit_type, amount, f"Found {amount} units of {deposit_type} deposits!"
            else:
                bonus = random.randint(500, 1000)
                location.mineral_deposits[deposit_type] += bonus
                return True, deposit_type, bonus, f"Found additional {bonus} units of {deposit_type} deposits!"
                
        return False, None, None, "Geoscan failed to find any deposits!"

    def incite_revolution(self, location):
      """
      Attempt to change planet's economy and remove trade bans.
      Returns: (bool success, str new_economy, str message)
      """
      research_system = self.game.research
      success_chance = self.base_success_rates['revolution']
      if 'chronopolitics' in research_system.unlocked_options:
            success_chance += research_system.research_benefits.get('chronopolitics', {}).get('revolution_success', 0)
            
      if random.random() < success_chance:
          current_economy = location.economy
          possible_economies = ['Booming', 'Stable', 'Declining', 'Formative']
          possible_economies.remove(current_economy)
          new_economy = random.choice(possible_economies)
          location.economy = new_economy
          # Clear trade bans
          location.banned_commodities = []
          location.ban_duration.clear()
          return True, new_economy, f"Revolution successful! Economy changed to {new_economy} and trade bans removed!"
      
      return False, None, "Revolution attempt failed!"
    
    def manipulate_market(self, location, commodity):
        """
        Attempt to manipulate market prices
        Returns: (bool success, float price_change, str message)
        """
        research_system = self.game.research
        if random.random() < self.base_success_rates['psychodynamics']:
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
            return True, price_change, f"Successfully manipulated {commodity} price by {abs(price_change):.1f}!"
            
        return False, 0, "Market manipulation attempt failed!"

    def build_mining_platform(self, location, deposit_type):
         """Build a new mining platform"""
         cost = 10000
         if self.game.ship.money >= cost:
            if location.build_mining_platform(deposit_type, cost):
                 self.game.ship.money -= cost
                 return True, f"Mining platform for {deposit_type} built!"
         return False, "Not enough money to build mining platform"

    def research_exogeology(self, location):
         """Research exogeology and enhance mining efficiency"""
         research_system = self.game.research
         if self.game.ship.research_points >= research_system.research_costs.get("exogeology", 0):
            self.game.ship.research_points -= research_system.research_costs.get("exogeology", 0)
            success, message = self.research(location, "exogeology")
            if success:
                 self.game.ui.display_simple_message(message)
            return success
         else:
            self.game.ui.display_simple_message("Not enough research points!")
            return False
    
    def conduct_analysis(self, location, specialization):
        """Safe research analysis with guaranteed small rewards and chance for items"""
        cost = 20
        if self.game.ship.research_points < cost:
            self.game.ui.display_simple_message(f"Not enough research points! Need: {cost}")
            return
        self.game.ship.research_points -= cost
        
        # Base rewards
        tech_bonus = random.randint(5, 15)
        money_bonus = random.randint(500, 1500)
        
        # Specialization bonuses
        if specialization == 'quantum':
            tech_bonus *= 1.5
        elif specialization == 'engineering':
            money_bonus *= 1.5
        
        # Chance for bonus item or ship stat
        if random.random() < 0.2:  # 20% chance for bonus
            bonus_type = random.choice(['item', 'stat'])
            if bonus_type == 'item':
                research_items = {
                    'quantum': ['quantum_analyzer', 'entanglement_core', 'quantum_shield'],
                    'xenology': ['xeno_scanner', 'translation_matrix', 'alien_artifact'],
                    'engineering': ['efficiency_module', 'repair_nanites', 'power_core'],
                    'temporal': ['time_dilator', 'causality_shield', 'temporal_lens']
                }
                item = random.choice(research_items[specialization])
                self.game.ship.acquire_item(item)
                self.game.ui.display_simple_message(f"Bonus research item acquired: {item}!")
            else:
                stat = random.choice(['attack', 'defense', 'speed'])
                bonus = 1
                if stat == 'attack':
                    self.game.ship.attack += bonus
                elif stat == 'defense':
                    self.game.ship.defense += bonus
                else:
                    self.game.ship.speed += bonus
                self.game.ui.display_simple_message(f"Ship {stat} improved by {bonus}!")

        # Generate research findings
        findings = {
            'quantum': [
                "Quantum field fluctuations mapped",
                "Superposition states stabilized",
                "Entanglement patterns documented",
                "Wave function variations recorded"
            ],
            'xenology': [
                "Alien artifact patterns analyzed",
                "Bio-signatures catalogued",
                "Cultural markers identified",
                "Xenotechnology principles documented"
            ],
            'engineering': [
                "Efficiency algorithms optimized",
                "Material stress patterns mapped",
                "Power distribution improved",
                "Systems integration enhanced"
            ],
            'temporal': [
                "Temporal anomalies measured",
                "Causality patterns documented",
                "Time dilation effects mapped",
                "Chronological variations recorded"
            ]
        }
        
        result = random.choice(findings[specialization])
        
        self.game.ship.money += money_bonus
        self.game.ship.research_points += tech_bonus
        
        self.game.ui.display_simple_message([
            f"Analysis Complete: {result}",
            f"Gained {tech_bonus} research points",
            f"Earned {self.game.format_money(money_bonus)} credits"
        ])

    def conduct_experiment(self, specialization):
        """Risky research with variable outcomes and enhanced rewards"""
        cost = 40
        if self.game.ship.research_points < cost:
            self.game.ui.display_simple_message(f"Not enough research points! Need: {cost}")
            return

        self.game.ship.research_points -= cost
        
        # Success chance based on specialization
        base_chance = 0.7
        if specialization == 'engineering':
            base_chance += 0.1
        
        if random.random() < base_chance:
            # Successful experiment
            reward_mult = random.uniform(1.5, 3.0)
            tech_bonus = int(cost * reward_mult)
            money_bonus = int(1000 * reward_mult)
            
            # Enhanced rewards
            if random.random() < 0.4:  # 40% chance for significant bonus
                advanced_items = {
                    'quantum': {
                        'items': ['quantum_core_v2', 'phase_shifter', 'quantum_capacitor'],
                        'stat_bonus': {'attack': 2, 'defense': 1, 'speed': 2}
                    },
                    'xenology': {
                        'items': ['alien_reactor', 'xeno_shield', 'biotech_enhancer'],
                        'stat_bonus': {'attack': 1, 'defense': 2, 'speed': 1}
                    },
                    'engineering': {
                        'items': ['fusion_drive', 'nanotech_armor', 'power_amplifier'],
                        'stat_bonus': {'attack': 2, 'defense': 2, 'speed': 1}
                    },
                    'temporal': {
                        'items': ['time_dilation_core', 'temporal_shield', 'causality_engine'],
                        'stat_bonus': {'attack': 1, 'defense': 1, 'speed': 3}
                    }
                }
                
                # Either get an advanced item or stat bonus
                if random.random() < 0.5:
                    item = random.choice(advanced_items[specialization]['items'])
                    self.game.ship.acquire_item(item)
                    self.game.ui.display_simple_message(f"Advanced research item acquired: {item}!")
                else:
                    stat_bonuses = advanced_items[specialization]['stat_bonus']
                    for stat, bonus in stat_bonuses.items():
                        if random.random() < 0.5:  # 50% chance for each stat
                            if stat == 'attack':
                                self.game.ship.attack += bonus
                            elif stat == 'defense':
                                self.game.ship.defense += bonus
                            else:
                                self.game.ship.speed += bonus
                            self.game.ui.display_simple_message(f"Ship {stat} improved by {bonus}!")

            # Special bonuses based on specialization
            special_outcomes = {
                'quantum': ["Quantum Computing Breakthrough", 
                        lambda: setattr(self.game.ship, 'quantum_bonus', True)],
                'xenology': ["Alien Technology Integration", 
                            lambda: setattr(self.game.ship, 'alien_tech', True)],
                'engineering': ["Advanced Engineering Insights", 
                            lambda: setattr(self.game.ship, 'engineering_bonus', True)],
                'temporal': ["Temporal Mechanics Discovery", 
                            lambda: setattr(self.game.ship, 'temporal_bonus', True)]
            }
            
            outcome, effect = special_outcomes[specialization]
            effect()  # Apply the special effect
            
            self.game.ui.display_simple_message([
                f"Experiment Success: {outcome}!",
                f"Gained {tech_bonus} research points",
                f"Earned {self.game.format_money(money_bonus)} credits",
                "Special ability unlocked!"
            ])
            
            self.game.ship.money += money_bonus
            self.game.ship.research_points += tech_bonus
            
        else:
            # Failed experiment
            damage = random.randint(5, 15)
            self.game.ship.damage = min(99, self.game.ship.damage + damage)
            lost_points = random.randint(5, 15)
            self.game.ship.research_points = max(0, self.game.ship.research_points - lost_points)
            
            self.game.ui.display_simple_message([
                "Experiment Failed!",
                f"Ship took {damage}% damage",
                f"Lost {lost_points} research points"
            ])

    def attempt_breakthrough(self, location, specialization):
        """Attempt a major research breakthrough"""
        cost = 100
        if self.game.ship.research_points < cost:
            self.game.ui.display_simple_message(f"Not enough research points! Need: {cost}")
            return

        self.game.ship.research_points -= cost
        
        # Breakthrough chance increases with more research points spent
        breakthrough_chance = min(0.8, 0.3 + (self.game.ship.research_points / 1000))
        
        if random.random() < breakthrough_chance:
            # Major breakthrough
            breakthrough_rewards = {
                'quantum': {
                    'name': "Quantum Tunneling Drive",
                    'effect': lambda: setattr(self.game.ship, 'speed', self.game.ship.speed + 2),
                    'bonus_rp': 300,
                    'bonus_money': 50000
                },
                'xenology': {
                    'name': "Xenomorph Shield Matrix",
                    'effect': lambda: setattr(self.game.ship, 'defense', self.game.ship.defense + 2),
                    'bonus_rp': 250,
                    'bonus_money': 40000
                },
                'engineering': {
                    'name': "Nano-fabrication System",
                    'effect': lambda: setattr(self.game.ship, 'engineering_level', 
                                            getattr(self.game.ship, 'engineering_level', 0) + 1),
                    'bonus_rp': 200,
                    'bonus_money': 60000
                },
                'temporal': {
                    'name': "Temporal Compression Field",
                    'effect': lambda: setattr(self.game.ship, 'temporal_compression', True),
                    'bonus_rp': 400,
                    'bonus_money': 45000
                }
            }
            
            reward = breakthrough_rewards[specialization]
            reward['effect']()  # Apply the special effect
            
            self.game.ship.research_points += reward['bonus_rp']
            self.game.ship.money += reward['bonus_money']
            
            self.game.ui.display_simple_message([
                f"Major Breakthrough: {reward['name']}!",
                f"Gained {reward['bonus_rp']} research points",
                f"Earned {self.game.format_money(reward['bonus_money'])} credits",
                "Revolutionary technology acquired!"
            ])
            
        else:
            # Minor breakthrough
            bonus_rp = random.randint(50, 150)
            bonus_money = random.randint(5000, 15000)
            
            self.game.ship.research_points += bonus_rp
            self.game.ship.money += bonus_money
            
            self.game.ui.display_simple_message([
                "Minor Breakthrough Achieved",
                f"Gained {bonus_rp} research points",
                f"Earned {self.game.format_money(bonus_money)} credits"
            ])

    def collaborate_research(self, location, specialization):
        """Collaborate with colony scientists"""
        cost = 30
        if self.game.ship.research_points < cost:
            self.game.ui.display_simple_message(f"Not enough research points! Need: {cost}")
            return

        self.game.ship.research_points -= cost
        
        # Collaboration projects
        projects = {
            'quantum': [
                ("Quantum Encryption", 1.2),
                ("Entanglement Network", 1.3),
                ("Quantum Computing", 1.4)
            ],
            'xenology': [
                ("Alien Languages", 1.2),
                ("Xenobiology", 1.3),
                ("First Contact Protocols", 1.4)
            ],
            'engineering': [
                ("Power Systems", 1.2),
                ("Shield Technology", 1.3),
                ("Propulsion Theory", 1.4)
            ],
            'temporal': [
                ("Time Dilation", 1.2),
                ("Causality Mechanics", 1.3),
                ("Temporal Physics", 1.4)
            ]
        }
        
        project, multiplier = random.choice(projects[specialization])
        
        # Calculate rewards
        research_gain = int(cost * multiplier)
        money_gain = int(2000 * multiplier)
        
        # Colony gains permanent bonus to future research
        colony_bonus = random.uniform(0.05, 0.15)  # 5-15% bonus
        current_multiplier = getattr(location, 'research_multiplier', 1.0)
        location.research_multiplier = current_multiplier + colony_bonus
        
        self.game.ship.research_points += research_gain
        self.game.ship.money += money_gain
        
        self.game.ui.display_simple_message([
            f"Collaboration Project: {project}",
            f"Gained {research_gain} research points",
            f"Earned {self.game.format_money(money_gain)} credits",
            f"Colony research efficiency increased by {int(colony_bonus * 100)}%"
        ])
# core/research.py
import yaml
import os
import random
from core.action import ActionResult


class Research:
    def __init__(self):
        self.unlocked_options = set()
        self.active_research = None # Track active research
        self.research_data = self.load_research_data()
        self.research_progress = {} # Store research progress per track (analysis/experiment count and other data)
    def load_research_data(self):
         """Load research data from data/research.yml"""
         try:
            with open("data/research.yml", 'r') as f:
                data = yaml.safe_load(f)
                return data.get("research_options", {})
         except FileNotFoundError:
             print("Error: research.yml not found. Using default research data.")
             return {}
         except yaml.YAMLError as e:
             print(f"Error loading research from YAML: {e}")
             return {}
    
    def get_research_data(self, option):
         """Get research data for a specific option"""
         return self.research_data.get(option, {})

    @property
    def research_costs(self):
        """Dynamically retrieve research costs"""
        return {
            key: item['cost']
            for key, item in self.research_data.items() if item["type"] == "tech"
        }
    
    @property
    def research_benefits(self):
        """Dynamically retrieve research benefits"""
        return {
            key: item.get('effects', {})
            for key, item in self.research_data.items() if item["type"] == "tech"
        }
    
    def get_research_requirements(self, option):
         """Get tech level and plot point requirements for a research option"""
         research = self.research_data.get(option, {})
         return {
             "tech_level": int(research.get("tech_level", 0)),
             "plot_points": int(research.get("plot_points", 0))
         }

    def get_research_type(self, option):
        """Get type of research"""
        research = self.research_data.get(option, {})
        return research.get('type')

    def can_unlock(self, option, research_points):
        """Check if a research option can be unlocked given available research points"""
        research_info = self.research_data.get(option)
        return research_points >= research_info.get('cost', float('inf')) if research_info else False
        #return research_points >= self.research_costs.get(option, float('inf')) #old method

    def unlock(self, option):
        """Unlock a research option"""
        self.unlocked_options.add(option)

    def start_research(self, option):
         """Start a new research project."""
         if option not in self.unlocked_options:
             self.active_research = option
             self.research_progress[option] = {
                 "analysis_count": 0,
                 "experiment_count": 0,
                 "breakthrough_bonus": 0,
                 "rp_reduction": 0
             }
             return True
         return False

    def perform_analysis(self, game, option):
        """Perform analysis on active research."""
        if self.active_research is None or option != self.active_research:
            return ActionResult(False, message="No active research or invalid option selected!")
            
        research_info = self.research_data.get(option)
        if not research_info:
            return ActionResult(False, message="Invalid research option.")
        
        progress = self.research_progress[option]
        analysis_bonus = research_info.get("analysis_bonus", 0)
        
        # Deduct research points
        cost = 20
        if game.ship.research_points < cost:
              return ActionResult(False, message=f"Not enough research points! Required: {cost}")
        game.ship.research_points -= cost
        
        # Apply diminishing returns
        bonus = analysis_bonus - (progress["analysis_count"] * analysis_bonus / 3)
        bonus = max(bonus, 0)

        # Add bonus to progress
        progress["breakthrough_bonus"] += bonus
        progress["analysis_count"] +=1

        # RP cost reduction
        reduction = research_info.get("cost", 0) * (0.05)  # 5% reduction each time
        if progress["rp_reduction"] < 0.2:
            progress["rp_reduction"] = min(0.2, progress["rp_reduction"] + reduction)
            

        message = [
           f"Analysis performed for {research_info.get('name', 'Unknown')}!",
           f"Breakthrough chance increased! Current bonus: {progress['breakthrough_bonus']:.2f}",
           f"Research Points cost reduced! Current reduction: {progress['rp_reduction']:.2f}"
        ]
        game.ui.display_simple_message(message)
        return ActionResult(True, message="Analysis complete")
    
    def perform_experiment(self, game, option):
        """Perform experiment on active research with risks and rewards."""
        if self.active_research is None or option != self.active_research:
            return ActionResult(False, message="No active research or invalid option selected!")
        
        research_info = self.research_data.get(option)
        if not research_info:
            return ActionResult(False, message="Invalid research option.")
        
        progress = self.research_progress[option]
        experiment_bonus = research_info.get("experiment_bonus", 0)
        
        # Deduct research points
        cost = 40
        if game.ship.research_points < cost:
            return ActionResult(False, message=f"Not enough research points! Required: {cost}")
        game.ship.research_points -= cost

        # Apply diminishing returns
        bonus = experiment_bonus - (progress["experiment_count"] * experiment_bonus / 3)
        bonus = max(bonus, 0)
            
        progress["breakthrough_bonus"] += bonus
        progress["experiment_count"] += 1
        
        # RP cost reduction
        reduction = research_info.get("cost", 0) * (0.1) # 10 %
        if progress["rp_reduction"] < 0.3:
            progress["rp_reduction"] = min(0.3, progress["rp_reduction"] + reduction)
        
        # Add variable effects with random outcome (chance for research point gain, lose or damage ship)
        if random.random() < 0.6:
             rp_change = random.randint(-10, 20)
             game.ship.research_points = max(0, game.ship.research_points + rp_change)
             if rp_change > 0:
                message = f"Experiment success! Gained {rp_change} research points."
             else:
                message = f"Experiment unstable! Lost {abs(rp_change)} research points."
        elif random.random() < 0.3:
            game.ship.damage = min(99, game.ship.damage + random.randint(5, 10))
            message = f"Experiment failed! Ship took damage."
        else:
            message = "Experiment successful! No new effects."
            
        message = [
           f"Experiment performed for {research_info.get('name', 'Unknown')}!",
           message,
            f"Breakthrough chance increased! Current bonus: {progress['breakthrough_bonus']:.2f}",
            f"Research Points cost reduced! Current reduction: {progress['rp_reduction']:.2f}"
        ]
        game.ui.display_simple_message(message)
        return ActionResult(True, message="Experiment complete")

    def attempt_breakthrough(self, game, option):
        """Attempt a research breakthrough"""
        if self.active_research is None or option != self.active_research:
            return ActionResult(False, message="No active research or invalid option selected!")
        
        research_info = self.research_data.get(option)
        if not research_info:
             return ActionResult(False, message="Invalid research option")
        
        progress = self.research_progress[option]
        base_chance = research_info.get("base_breakthrough_chance", 0)
        
        # Calculate success with the modifiers from analysis and experiment actions
        total_chance = min(1.0, base_chance + progress["breakthrough_bonus"])
        
        # Calculate cost reduction
        cost = research_info.get("cost", 0) * (1 - progress["rp_reduction"]) #Apply reduction to the base cost
        cost = max(0, int(cost * (1 + research_info.get("breakthrough_cost_mult", 0))))  # apply cost multiplier

        if game.ship.research_points < cost:
              return ActionResult(False, message=f"Not enough research points to attempt breakthrough! Required: {cost}")
        
        game.ship.research_points -= cost
        
        if random.random() < total_chance:
            # Unlock the technology if successful and complete the research progress
            self.unlock(option)
            del self.research_progress[option] # clean the record for new research
            self.active_research = None # remove active research

            # Get unlocks to be returned to Game for processing
            unlocks = []
            if research_info.get("unlocks", []):
                 for unlock in research_info["unlocks"]:
                     unlock_data = self.get_research_data(unlock)
                     unlocks.append({
                       "type": unlock_data.get("type"),
                       "id": unlock,
                       "name": unlock_data.get("name")
                    })
            # Return that the research was completed successfully, and with the unlocks
            return ActionResult(True, message=f"Successfully researched {research_info.get('name', 'Unknown')}! ", value=unlocks)
        else:
            # Failure result with potential side effects from data file
            failure_effects = research_info.get("failure_effects", [])
            
            # apply effects
            if failure_effects:
              for effect in failure_effects:
                   if effect == "damage":
                       damage = random.randint(5, 15)
                       game.ship.damage = min(99, game.ship.damage + damage)
                       self.game.ui.display_simple_message(f"Breakthrough failed! Ship took {damage}% damage")
                   elif effect == "loss":
                       lost = random.randint(10, 25)
                       game.ship.research_points = max(0, game.ship.research_points - lost)
                       self.game.ui.display_simple_message(f"Breakthrough failed! Lost {lost} research points")
            
            return ActionResult(False, message="Research breakthrough failed!")

    def apply_research_effects(self, game, option):
      """Apply the research effect from the data"""
      research = self.research_data.get(option, {})
      
      if not research.get('effects', {}):
          return
      for effect_name, effect_value in research['effects'].items():
        if effect_name == 'output_bonus':
            for location in game.locations:
                if location.location_type == 'AsteroidBase':
                    location.exogeology += int(location.exogeology * effect_value)
        elif effect_name == "scout_success":
            if not hasattr(game.ship, 'scout_bonus'):
                game.ship.scout_bonus = 0
            game.ship.scout_bonus += effect_value
        elif effect_name == "exogeology":
            for location in game.locations:
              if location.location_type == 'AsteroidBase':
                location.exogeology = min(100, location.exogeology + int(location.exogeology * effect_value))
        elif effect_name == "revolution_success":
            if not hasattr(game.action, 'revolution_success'):
                game.action.revolution_success = 0
            game.action.revolution_success += effect_value
        elif effect_name == "price_control":
            if not hasattr(game.action, 'price_control'):
                game.action.price_control = 0
            game.action.price_control += effect_value
        elif effect_name == 'tech_boost':
            game.ship.research_points = int(game.ship.research_points * (1 + effect_value))
        elif effect_name == "shield_bonus":
            game.ship.defense += effect_value
        elif effect_name == 'attack_bonus':
            game.ship.attack += effect_value
        elif effect_name == "tax_reduction":
             if not hasattr(game, 'trade_bonus'):
                game.trade_bonus = 0
             game.trade_bonus += effect_value
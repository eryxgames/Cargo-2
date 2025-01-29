# core/game.py
import os
import json
import random
import shutil
import time
from core.location import Location #Now only base class
from core.ship import Ship
from core.port import Port 
from core.research import Research
from core.action import Action
from core.contract import ContractManager
from core.story import StoryManager
from core.location_manager import LocationManager
from core.dynamic_character_system import DynamicCharacterSystem, SpecialCharacterEncounters
from core.uprising import SyntheticEventManager, InfestationManager #Fixed imports
from core.utils import display_logo, logo_data, print_centered_text, format_money #removed word_wrap
from ui.text_ui import TextUI
from ui.theme_manager import ThemeManager
from core.character import CharacterManager, SpecialCharacterGenerator, SyntheticCharacterGenerator, AlienCharacterGenerator
import csv
from core.gameplay import play_turn
from core.template import CharacterTemplate
from core.audio import AudioManager
from core.game_events import GameEvents
from core.quest import QuestSystem, ResourceTransportQuest
from math import floor
from core.shop import Shop # Import here
from core.location_data import LocationCommands, LocationCapabilities, LocationTerminology
from core.reputation import PassengerReputationManager #added import here
from core.captain import Captain #added import here
from core.cantina import Cantina #added import here
from ui import UI_Interface #added import here
from core.location_data import LocationTerminology

class Game:
    def __init__(self, settings=None, ui=None):
        self.settings = settings if settings else self.load_settings()
        self.ui = ui if ui else TextUI()  # Default UI if none passed
        self.term_width = self.get_terminal_width()
        self.term_height = self.get_terminal_height()
        self.difficulty = self.choose_difficulty()
        
        self.location_manager = LocationManager(self)
        self.locations = self.location_manager.load_locations()
        
        if not self.locations or not any(loc.location_type == "Planet" for loc in self.locations):
            raise ValueError("No planets available! Check your locations.csv data and ensure that there is at least one location with location type as Planet.")

        self.current_location = random.choice([loc for loc in self.locations if loc.location_type == "Planet"])
        self.shop = Shop(self) #Modified here
        self.ship = Ship(self)
        self.turn = 0
        self.known_locations = [self.current_location.name]
        self.event_log = []
        self.player_name = self.get_player_name()
        self.rank = "Explorer"
        self.reputation = 0
        self.story_manager = StoryManager(self)
        self.quest_system = QuestSystem(self)
        self.unlocked_location_types = {"Planet"}
        
        self.secret_quest_available = False
        self.stellar_portal_available = False
        self.research = Research()
        self.action = Action(self) # Modified this line to pass self
        # Add new tracking attributes for story milestones
        self.trades_completed = 0
        self.combat_difficulty = 1.0
        self.pirate_frequency = 1.0
        self.event_risk = 1.0
        self.event_probability = 0.2
        self.crisis_active = False
        self.endgame_active = False
        self.enable_stellar_portal = False
        self.legendary_items_available = False
        self.final_crisis_events = False
        self.trade_bonus = 0
        self.repair_discount = 0
        self.combat_bonus = 0
        # Initialize character generators
        self.templates = CharacterTemplate.load_character_templates("data/characters.yml")
        self.character_generators = {
            "human": SpecialCharacterGenerator(self),
            "synthetic": SyntheticCharacterGenerator(self),
            "alien": AlienCharacterGenerator(self),
            "special" : SpecialCharacterGenerator(self)
        }
        # Add systems
        self.port_system = Port(self)
        self.contract_manager = ContractManager(self)
        self.resource_transport = ResourceTransportQuest(self)
        self.reputation_manager = PassengerReputationManager(self)
        self.synthetic_events = SyntheticEventManager(self)
        self.character_system = DynamicCharacterSystem(self)
        self.character_encounters = SpecialCharacterEncounters(self)
        self.discovered_locations = set()
        self.cooldowns = {}
        self.story_events = {}
        self.character_manager = CharacterManager(self)
        self.infestation_manager = InfestationManager(self)
        self.game_events = GameEvents(self)
         # Load building data from csv
        self.building_data, self.building_costs, self.valid_building_options = self.load_building_data()
        
        # Load rank data from JSON
        self.rank_data = self.load_rank_data()
        # Add variable for total research
        self.total_research_points = 0
        
        # Initialize Captain Class
        self.captain = Captain(self, name=self.player_name) #modified here

        # Initialize the story
        self.story_manager.start_game()
        self.music_data = self.load_music_data()
        self.sound_data = self.load_sound_data()
        self.audio_manager = AudioManager(self, settings=self.settings) # Modified here to pass self
        self.play_music(self.settings.get("menu_theme", "menu_theme"))
        self.display_starting_info()

        # Initialize cantina
        self.cantina = Cantina(self)

    def handle_actions(self):
        """Handle actions based on the current location and type"""
        available_actions = {
            "scout": ("Scout Area", self.action.scout_area),
            "geoscan": ("Geoscan Deposits", self.action.geoscan),
            "revolution": ("Incite Revolution", self.action.incite_revolution),
             "psychodynamics": ("Manipulate Market", self.action.manipulate_market),
            "exogeology": ("Research Mining", self.action.research_exogeology),
            "build_mining_platform": ("Build Mining Platform", self.build_mining_platform)
        }
        
        action_list = []
        action_names = []
        for key, (name, func) in available_actions.items():
            if key in self.current_location.commands.get("special", {}).get("action", {}).get("options", []) or key in ['exogeology', 'build_mining_platform'] :
              action_list.append(key)
              action_names.append(name)
        
        if not action_list:
            self.ui.display_simple_message("No actions available here!")
            return
            
        # Display available actions
        action_content = [["Actions:"]]
        for i, action_name in enumerate(action_names):
              action_content.append([f"{i+1}. {action_name}"])
        print(self.ui.create_box(action_content, 'single'))

        action_choice = self.validate_input(
            "Choose action: ",
            [str(i+1) for i in range(len(action_names))] + ['research']
        )
        
        if action_choice is None:
            return
                
        if action_choice == 'research':
            self.handle_research_options()
            return
        
        try:
          chosen_index = int(action_choice) -1
          if chosen_index >=0 and chosen_index < len(action_list):
             action_key = action_list[chosen_index]
             name, func = available_actions[action_key]

             # Perform action from action.py file
             if action_key == "manipulate_market":
                 commodity = self.validate_input("Choose commodity (tech/agri/salt/fuel):", ['tech', 'agri', 'salt', 'fuel'])
                 if not commodity:
                    return
                 success, price_change, message = func(self.current_location, commodity)
                 self.ui.display_simple_message(message)
             elif action_key == 'build_mining_platform':
                 if not self.current_location.mineral_deposits:
                     self.ui.display_simple_message("No mineral deposits found! Use geoscan first.")
                     return
                     
                 available_deposits = list(self.current_location.mineral_deposits.keys())
                 deposit_type = self.validate_input(
                        f"Choose deposit type to mine ({', '.join(available_deposits)}): ",
                        available_deposits
                 )
                 if deposit_type:
                     success, message = func(self.current_location, deposit_type)
                     self.ui.display_simple_message(message)
             else:
                 result = func(self.current_location)
                 # Check if returned result was a tuple for more complex data returns
                 if isinstance(result, tuple):
                     success, type, value, message = result
                     self.ui.display_simple_message(message)
                     if success:
                        if type == "tech" or type == "agri":
                             self.ship.cargo[type] += value
                        elif type == 'item':
                            self.ship.acquire_item(value)
                 else:
                     # Check if returned boolean
                     if result:
                         self.ui.display_simple_message(f"Action {name} successful!")
                     else:
                         self.ui.display_simple_message(f"Action {name} failed!")

        except (ValueError, KeyError):
          self.ui.display_simple_message("Invalid action selected!")

    def handle_research_options(self):
        """Enhanced research options system"""
        if self.current_location.location_type != "ResearchColony":
            self.ui.display_simple_message("Research options only available at Research Colonies!")
            return

        # Show current research points and colony specialization
        specialization = getattr(self.current_location, 'research_specialization', 
                            random.choice(['quantum', 'xenology', 'engineering', 'temporal']))
        self.current_location.research_specialization = specialization
        
        research_content = [
            ["Research Laboratory Options"],
            [f"Available Research Points: {self.ship.research_points}"],
            [f"Colony Specialization: {specialization.title()}"],
            [""],
            ["1. Analyze (20 RP) - Safe, steady progress"],
            ["2. Experiment (40 RP) - Risky, higher rewards"],
            ["3. Breakthrough (100 RP) - Major discovery attempt"]
        ]
        
        # Show available research options
        available_research = self.research.research_data
        available_options = []
        for key, value in available_research.items():
             requirements = self.research.get_research_requirements(key)
             if self.current_location.tech_level >= requirements["tech_level"] and self.story_manager.plot_points >= requirements["plot_points"] and key not in self.research.unlocked_options:
                 available_options.append(f"{key}: {value['name']} ({value['cost']} RP)")
        
        for i, item in enumerate(available_options):
              research_content.append([f"{i + 4}. {item}"])
        
        print(self.ui.create_box(research_content, 'double'))
        
        valid_options = [str(i) for i in range(1, len(available_options) + 4)] + ['back']
        choice = self.validate_input(
            "Choose research action (1-4 or research number, or 'back'): ",
            valid_options
        )
        
        if choice == 'back':
            return
        
        if choice == '1':
            self.conduct_analysis(specialization)
        elif choice == '2':
            self.conduct_experiment(specialization)
        elif choice == '3':
            self.attempt_breakthrough(specialization)
        elif int(choice) >= 4:
             chosen_option = available_options[int(choice)-4].split(':')[0] # Get key from string
             if chosen_option in self.research.research_data:
               if self.research.can_unlock(chosen_option, self.ship.research_points):
                   self.research.unlock(chosen_option)
                   success, message = self.action.research(self.current_location, chosen_option)
                   if success:
                        self.ui.display_simple_message(message)
               else:
                    self.ui.display_simple_message(
                        f"Not enough research points! Required: {self.research.research_costs.get(chosen_option,0)}"
                    )
            
    def display_mining_status(self):
        self.ui.display_mining_status(self.current_location)
        
    def build_mining_platform(self, deposit_type):
        """Build a new mining platform using Action class"""
        success, message = self.action.build_mining_platform(self.current_location, deposit_type)
        if success:
            self.ui.display_simple_message(message)
        else:
            self.ui.display_simple_message(message)

    def handle_theme_change(self):
         """Handle changing the theme in the game."""
         theme_names = list(self.ui.theme_manager.themes.keys())
         
         theme_content = [["Choose Theme:"]]
         for i, theme in enumerate(theme_names, 1):
              theme_content.append([f"{i}. {theme}"])
        
         print(self.ui.create_box(theme_content, 'single'))
        
         choice = self.validate_input("Choose a theme by number (or '/' for next theme): ", [str(i) for i in range(1, len(theme_names) + 1)] + ['/'])
         if choice:
              if choice == '/':
                self.ui.current_theme_index = (self.ui.current_theme_index + 1) % len(self.ui.available_themes)
                selected_theme = self.ui.available_themes[self.ui.current_theme_index]
              else:
                  selected_theme = theme_names[int(choice) - 1]
                  
              self.ui.theme_manager.load_theme(selected_theme)
              self.ui.display_simple_message(f"Theme switched to {selected_theme}")
    
    def handle_trade(self, action, item, quantity, price):
          """Handle trade actions with update and contract tracking"""
          if hasattr(self, 'contract_manager'):
            event_data = {
                "action": action,
                "commodity": item,
                "amount": quantity,
                "location": self.current_location.name,
                "turn": self.turn
            }
            self.contract_manager.update_contract_progress(event_data)

          self.quest_system.update_from_trade(
              {
                "action": action,
                "commodity": item,
                "amount": quantity,
            }
          )
    
    def handle_travel(self):
        """Handle travelling to a new location"""
        
        available_planets = [loc for loc in self.locations
                            if loc.name != self.current_location.name and 
                               loc.location_type in self.unlocked_location_types]

        if not available_planets:
            self.ui.display_simple_message("No other locations available to travel!", 1)
            return False
        
        available_names = [loc.name.lower() for loc in available_planets]
        location_choice = self.validate_input( #modified here
            f"Choose location to travel to: ",
            available_names
        )
        if not location_choice:
            return False

        # Find actual Location object with chosen name
        chosen_location = next((loc for loc in self.locations if loc.name.lower() == location_choice), None)
        if chosen_location:
            self.current_location = chosen_location
            self.ui.display_simple_message(f"Traveling to: {self.current_location.name}!", 1)
            self.record_activity('travel') #record travel activity
            self.location_manager.handle_location_discovery(self.current_location)
            return True
        else:
            self.ui.display_simple_message("Invalid location selected!")
            return False
        
    def handle_building_construction(self, building_name, building_costs):
        """Handle building construction with proper capability checking and building process"""
        # Map short commands to full building names and their base types
        building_mapping = {}
        for key, value in self.building_data.items():
            building_mapping[value['name'].lower()] = value
            building_mapping[value['short_name'].lower()] = value

        if building_name.lower() not in building_mapping:
            self.ui.display_simple_message("Invalid building type.")
            return False
        
        building_data = building_mapping[building_name.lower()]
        full_building_name = building_data['name']
        base_type = building_data['building_id']
        
        # Get base cost and calculate final cost
        base_cost = int(building_data.get('cost', 3000))
        cost_multiplier = self.current_location.buildings.count(full_building_name) + 1
        final_cost = base_cost * cost_multiplier

        # Check if we can afford it
        if self.ship.money < final_cost:
            self.ui.display_simple_message(f"Not enough money. Cost: {self.format_money(final_cost)}")
            return False

        # Deduct money first (will be refunded if build fails)
        self.ship.money -= final_cost

        # Add building directly to location's building list
        self.current_location.buildings.append(full_building_name)
        # Apply building effects, by calling building methods from location class
        self.current_location.build_building(full_building_name) #modified this line
        
        self.ui.display_simple_message(f"Built {full_building_name} for {self.format_money(final_cost)} credits.")
        return True

    def load_building_data(self):
        """Load building data from data/buildings.csv"""
        building_data = {}
        building_costs = {}
        valid_options = []
        try:
            with open("data/buildings.csv", 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    building_id = row['building_id']
                    building_data[row['name']] = row
                    building_costs[row['name']] = int(row['cost'])
                    valid_options.append(row['name'].lower())
                    valid_options.append(building_id)
            return building_data, building_costs, valid_options
        except FileNotFoundError:
            print("Error: buildings.csv not found. Using default buildings.")
            return {}, {}, []
        except Exception as e:
            print(f"Error loading buildings from CSV: {e}")
            return {}, {}, []
        
    def load_rank_data(self):
        """Load rank data from data/ranks.json"""
        try:
            with open("data/ranks.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            print("Error: ranks.json not found. Using default settings.")
            return {}
        except json.JSONDecodeError:
            print("Error: Could not parse ranks.json. Using default settings.")
            return {}

    def update_rank(self):
         self.captain.update_rank() # now calls update_rank from Captain class
         self.rank = self.captain.rank # rank is defined from captain
    
    def rank_multiplier(self):
       """Returns rank multiplier for calculations"""
       return self.captain.rank_multiplier("multiplier") # now calls rank_multiplier from Captain class
    
    def get_tax_multiplier(self):
        """Returns tax multiplier for tax calculations"""
        return self.captain.rank_multiplier("tax_multiplier") # Get specific multiplier type
       
    def record_activity(self, activity_type, amount=1):
        """Record player activity for calculating rank."""
        self.captain.record_activity(activity_type, amount)
    
    def get_recent_activity(self):
        """Get a summary of player activities for the last few turns."""
        return self.captain.get_recent_activity()

    def handle_research_gain(self, points):
         self.total_research_points += points
         self.record_activity("research", points)
        
    def load_settings(self):
        """Load settings from data/settings.json"""
        try:
            with open("data/settings.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            print("Error: settings.json not found. Using default settings.")
            return {}
        except json.JSONDecodeError:
            print("Error: Could not parse settings.json. Using default settings.")
            return {}


    
    def load_music_data(self):
        """Load music data from data/music.json"""
        try:
           with open("data/music.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            print("Error: music.json not found. Music will be disabled.")
            return {"tracks": []}
        except json.JSONDecodeError:
            print("Error: could not parse music.json. Music will be disabled.")
            return {"tracks": []}
            
    def load_sound_data(self):
        """Load sound data from data/sound.json"""
        try:
            with open("data/sound.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            print("Error: sound.json not found. Sounds will be disabled.")
            return {"effects": []}
        except json.JSONDecodeError:
            print("Error: could not parse sound.json. Sounds will be disabled.")
            return {"effects": []}
            
    def play_music(self, track_id):
        """Plays a specific music track"""
        self.audio_manager.play_music(track_id, fade_time=2000)

    def play_sound(self, effect_id):
       """Plays a specific sound effect"""
       self.audio_manager.play_sound(effect_id)


    
# core/game.py
    def get_terminal_width(self):
        return shutil.get_terminal_size().columns

    def get_terminal_height(self):
        return shutil.get_terminal_size().lines

    def format_money(self, amount):
        if amount >= 1_000_000_000:
            return f"{amount/1_000_000_000:.1f}B"
        elif amount >= 1_000_000:
            return f"{amount/1_000_000:.1f}M"
        elif amount >= 1_000:
            return f"{amount/1_000:.1f}K"
        return str(floor(amount))

    def validate_input(self, prompt, valid_options):
        """
        Validate user input against a list of valid options
        default_prompt: Default prompt text
        valid_options: List of valid input options
        prompt: Optional custom prompt to override default
        """
        term_width = shutil.get_terminal_size().columns

        while True:
            wrapped_prompt = self.word_wrap(prompt, term_width - 4)
            self.ui.display_simple_message(wrapped_prompt, 0)

            try:
                user_input = input(">>> ").strip().lower()
                if not user_input:
                    self.ui.display_simple_message("Command cancelled.")
                    return None
                if user_input in [opt.lower() for opt in valid_options]: #modified here
                    return user_input
                self.ui.display_simple_message(f"Invalid input, try: {', '.join(valid_options)}", 1)
            except KeyboardInterrupt:
                print(f"Do you want to exit? (yes/no):")
                confirm = input(">>> ").strip().lower()
                if confirm == 'yes':
                    self.ui.display_simple_message("Goodbye!", 1)
                    exit()

    def validate_quantity_input(self, prompt):
        while True:
            self.ui.display_simple_message(prompt, 0)
            try:
                user_input = input(">>> ").strip().lower()
                if not user_input:
                    self.ui.display_simple_message("Command cancelled.")
                    return None
                if user_input in ['max', 'm']:
                    return 'max'
                if user_input in ['half', 'h']:
                    return 'half'
                quantity = int(user_input)
                if quantity > 0:
                    return quantity
                self.ui.display_simple_message("Please enter a positive number, 'max/m', or 'half/h'", 1)
            except ValueError:
                self.ui.display_simple_message("Invalid input. Please enter a number, 'max/m', or 'half/h'", 1)

    def validate_planet_input(self, prompt):
        while True:
            self.ui.display_simple_message(prompt, 0)
            try:
                user_input = input(">>> ").strip().lower()
                if not user_input:
                    self.ui.display_simple_message("Command cancelled.")
                    return None
                if user_input.isdigit():
                    index = int(user_input) - 1
                    if 0 <= index < len(self.known_planets):
                        return self.known_planets[index]
                for planet in self.planets:
                    if planet.name.lower() == user_input:
                        return planet.name
                self.ui.display_simple_message(f"Invalid input. Valid options: {', '.join([planet.name for planet in self.planets])}", 1)
            except KeyboardInterrupt:
                print(f"Do you want to exit? (yes/no):")
#                self.display_message("Do you want to exit? (yes/no)", 0)
                confirm = input(">>> ").strip().lower()
                if confirm == 'yes':
                    self.ui.display_simple_message("Goodbye!", 1)
                    exit()

    def calculate_quest_reward(self, base_reward):
        """Calculate quest reward based on rank and research"""
        multiplier = self.rank_multiplier()
        if 'xenoeconomy' in self.research.unlocked_options:
            multiplier *= 1.2  # 20% bonus from research
        return int(base_reward * multiplier)

    def validate_price(self, commodity, price):
        """Validate if a price is reasonable for a commodity"""
        if commodity == 'salt':
            return 60 <= price <= 150
        elif commodity == 'fuel':
            return 120 <= price <= 250
        return True  # Default for other commodities

    def update_market_prices(self):
        """Update market prices with new logic"""
        for planet in self.locations:
            # Update basic commodities
            planet.update_market(self.difficulty)
            
            # Update mining commodities
            planet.produce_resources()
            
            # Apply market manipulation if researched
            if 'psychodynamics' in self.research.unlocked_options:
                for commodity in ['tech', 'agri', 'salt', 'fuel']:
                    if random.random() < 0.2:  # 20% chance for each commodity
                        self.action.manipulate_market(planet, commodity, self.research)
    
# core/game.py
    def display_turn_info(self):
        self.clear_screen()

        # Calculate passenger stats
        total_passengers = 0
        total_capacity = 0
        if hasattr(self.ship, 'passenger_modules'):
            for module in self.ship.passenger_modules:
                total_passengers += len(module.passengers)
                total_capacity += module.capacity

        status_content = [
            ["CΔRGΩ", "Ship", f"{self.current_location.location_type}"],
            [f"Turn: {self.turn}", f"ATK: {self.ship.attack}", f"Name: {self.current_location.name}"],
            [f"¤: {self.format_money(self.ship.money)}", f"DEF: {self.ship.defense}", f"Tech LVL: {self.current_location.tech_level}"],
            [f"Tech: {self.format_money(self.ship.cargo['tech'])}", f"SPD: {self.ship.speed}", f"Agri LVL: {self.current_location.agri_level}"],
            [f"Agri: {self.format_money(self.ship.cargo['agri'])}", f"DMG: {self.ship.damage}%", f"ECO: {self.current_location.economy}"],
            [f"Salt: {self.format_money(self.ship.cargo['salt'])}", f"RP: {self.ship.research_points}", f"EFF: {self.current_location.exogeology}%"],
            [f"Fuel: {self.format_money(self.ship.cargo['fuel'])}", f"★ {self.rank}", f"NET: {len(self.current_location.buildings)}"],
            [f"PAX: {total_passengers}/{total_capacity}", f"REP: {self.ship.passenger_reputation}", ""]
        ]
        
        # Add story progress if available
        if hasattr(self, 'story_manager'):
            current_chapter = self.story_manager.chapters[self.story_manager.current_chapter]
            status_content.append([
                f"Chapter {self.story_manager.get_chapter_number_roman()}",
                f"Plot Points: {self.story_manager.plot_points}",
                current_chapter.title
            ])

        status_box = self.ui.create_box(status_content, 'double')
        print(status_box)

        # Market prices with banned commodities indicator
        tech_status = "BANNED" if 'tech' in self.current_location.banned_commodities else str(self.format_money(self.current_location.market['tech']))
        agri_status = "BANNED" if 'agri' in self.current_location.banned_commodities else str(self.format_money(self.current_location.market['agri']))
        salt_status = "BANNED" if 'salt' in self.current_location.banned_commodities else str(self.format_money(self.current_location.market['salt']))
        fuel_status = "BANNED" if 'fuel' in self.current_location.banned_commodities else str(self.format_money(self.current_location.market['fuel']))

        # Market content with two columns
        market_content = [
            [f"Tech: {tech_status}", f"Salt: {salt_status if any(p['type'] == 'salt' for p in self.current_location.mining_platforms) else '——'}"],
            [f"Agri: {agri_status}", f"Fuel: {fuel_status if any(p['type'] == 'fuel' for p in self.current_location.mining_platforms) else '——'}"]
        ]

        # Add ban duration if any commodities are banned
        if self.current_location.banned_commodities:
            market_content.append(["", ""])  # Empty line for spacing
            market_content.append(["Trade Bans:", "Duration:"])
            for commodity in self.current_location.banned_commodities:
                duration = self.current_location.ban_duration.get(commodity, "Permanent")
                market_content.append([f"{commodity.capitalize()}", f"{duration} turns"])
        print(self.ui.create_box(market_content, 'single'))

        # Display commands including port
        commands = [
            ["Commands: buy/b, sell/s, travel/t, port/p, cantina/c, shop/sh, upgrade/u, repair/r, action/a, mine/m, build/bl, log/l, info/i..."],
        
        ]
    #    print(self.create_box(commands, 'round'))
        self.ui.display_simple_message(f"Commands: buy/b, sell/s, travel/t, port/p, cantina/c, shop/sh, upgrade/u, repair/r, action/a, mine/m, build/bl, log/l, info/i...", 1)

        # Display active effects
        if self.research.unlocked_options:
            effects = [["Active Research Effects"]]
            for research in self.research.unlocked_options:
                effects.append([f"- {research.replace('_', ' ').title()}"])
            print(self.ui.create_box(effects, 'round'))

    def display_location_info(self):
        # Ship section
        # Get total locations
        total_locations = len(self.locations) if hasattr(self, 'locations') else 0
        # Add 1 to discovered count for starting location if not already included
        discovered = (len(self.discovered_locations) if hasattr(self, 'discovered_locations') else 0)

        ship_info = [
            ["Ship Information"],
            [f"Stats: {self.ship.attack}|{self.ship.defense}|{self.ship.speed}"],
            [f"Locations Discovered: {discovered + 1}/{total_locations}"],
            [f"Trades Completed: {self.trades_completed}"],
            [f"PAX Delivered: {self.reputation_manager.total_passengers}"],
#            [f"Locations Discovered: {len(self.discovered_locations) if hasattr(self, 'discovered_locations') else 0}"]
#            [f"Hull Damage: {self.ship.damage}%"],
            [f"Money: {self.format_money(self.ship.money)}"],
            [f"Research Points: {self.ship.research_points}"],
    #        ["Cargo:"],
    #        [f"  Tech: {self.format_money(self.ship.cargo['tech'])}"],
    #        [f"  Agri: {self.format_money(self.ship.cargo['agri'])}"],
    #        [f"  Salt: {self.format_money(self.ship.cargo['salt'])}"],
    #        [f"  Fuel: {self.format_money(self.ship.cargo['fuel'])}"],
            ["Items:"]
        ]

      
                
        # Add items if any exist
        if self.ship.items:
            for item, count in self.ship.items.items():
                ship_info.append([f"  {item.capitalize()}: {count}"])
        else:
            ship_info.append(["  No items"])

        # Add combat statistics if they exist
        if hasattr(self.ship, 'combat_victories'):
                    ship_info.append(["Combat Record:"])
                    # Format victories
                    ship_info.extend([
                        [f"Victories/Defeats Summary"],
                        [f"  Pirates: {self.ship.combat_victories.get('pirate', 0)}/{self.ship.combat_defeats.get('pirate', 0)}"],
                        [f"  Raiders: {self.ship.combat_victories.get('raider', 0)}/{self.ship.combat_defeats.get('raider', 0)}"],
                        [f"  Militia: {self.ship.combat_victories.get('militia', 0)}/{self.ship.combat_defeats.get('militia', 0)}"],
                        [f"  Aliens: {self.ship.combat_victories.get('alien', 0)}/{self.ship.combat_defeats.get('alien', 0)}"],
                        [f"  Total: {self.ship.combat_victories.get('total', 0)}/{self.ship.combat_defeats.get('total', 0)}"]
                    ])

        if hasattr(self.ship, 'active_infestations') and self.ship.active_infestations:
            content.append(["Active Infestations:"])
            for name, infestation in self.ship.active_infestations.items():
                content.append([
                    f"{infestation['name']} - Turn {infestation['turns_active']}"
                ])

        # Location section
        location_info = [
            ["Location"],
            [f"Name: {self.current_location.name}"],
            [f"Type: {self.current_location.location_type}"],
            [f"Tech Level: {self.current_location.tech_level}"],
            [f"Agri Level: {self.current_location.agri_level}"],
            [f"Research Points: {self.current_location.research_points}"],
            [f"Economy: {self.current_location.economy}"],
            [f"Mining Efficiency: {self.current_location.exogeology}%"],
            ["Current Market:"],
            [f"  Tech: {self.format_money(self.current_location.market['tech'])}"],
            [f"  Agri: {self.format_money(self.current_location.market['agri'])}"],
            [f"  Salt: {self.format_money(self.current_location.market['salt'])}"],
            [f"  Fuel: {self.format_money(self.current_location.market['fuel'])}"]
        ]

        # Add banned commodities if any
        if self.current_location.banned_commodities:
            location_info.append(["Banned Commodities:"])
            for commodity in self.current_location.banned_commodities:
                duration = self.current_location.ban_duration.get(commodity, "Permanent")
                location_info.append([f"  {commodity.capitalize()}: {duration} turns"])

        # Add buildings
        location_info.append(["Networks (Built):"])
        if self.current_location.buildings:
            building_counts = {}
            for building in self.current_location.buildings:
                building_counts[building] = building_counts.get(building, 0) + 1
            for building, count in building_counts.items():
                location_info.append([f"  {building} x{count}"])
        else:
            location_info.append(["  No buildings"])

        # Add mining information
        location_info.append(["Mining Operations:"])
        if self.current_location.mining_platforms:
            for platform in self.current_location.mining_platforms:
                location_info.append([
                    f"  {platform['type'].capitalize()} Platform",
                    f"  (Efficiency: {platform['efficiency']}%",
                    f"  Capacity: {platform['capacity']})"
                ])
        else:
            location_info.append(["  No mining platforms"])

        # Add mineral deposits if any
        if self.current_location.mineral_deposits:
            location_info.append(["Mineral Deposits:"])
            for deposit_type, amount in self.current_location.mineral_deposits.items():
                location_info.append([f"  {deposit_type.capitalize()}: {amount} units"])
        
        # Create content by combining ship and location info
        content = []
        max_length = max(len(ship_info), len(location_info))
        
        for i in range(max_length):
            ship_line = ship_info[i][0] if i < len(ship_info) else ""
            location_line = location_info[i][0] if i < len(location_info) else ""
            content.append([ship_line, location_line])

        print(self.ui.create_box(content, 'double'))
        input("Press Enter to continue...")

    def build_mining_platform(self):
        """Build a new mining platform on the current planet"""
        if not self.current_location.mineral_deposits:
            self.ui.display_simple_message("No mineral deposits found! Use geoscan first.")
            return
            
        available_deposits = list(self.current_location.mineral_deposits.keys())
        deposit_type = self.validate_input(
            f"Choose deposit type to mine ({', '.join(available_deposits)}): ",
            available_deposits
        )
        
        if deposit_type is None:
            return
            
        cost = 10000
        if self.ship.money >= cost:
            self.ship.money -= cost
            self.current_location.mining_platforms.append({
                'type': deposit_type,
                'efficiency': self.current_location.exogeology,
                'capacity': random.randint(100, 200)
            })
            self.ui.display_simple_message(f"Mining platform for {deposit_type} built!")
        else:
            self.ui.display_simple_message("Not enough money to build mining platform.")

    def format_buildings(self):
        building_counts = {}
        for building in self.current_location.buildings:
            if building in building_counts:
                building_counts[building] += 1
            else:
                building_counts[building] = 1
        return [f"{building} {count}" for building, count in building_counts.items()]

    def choose_difficulty(self):
        self.clear_screen()
        display_logo(logo_data, centered=True)
        difficulty_info = [
#            ["DIFFICULTY SELECTION"],
            [""],
            ["  1. EASY"],
            ["  2. NORMAL"],
            ["  3. EXPERT"],
            ["     "]
            
        ]
        
        for line in difficulty_info:
            print(line[0])
            time.sleep(0.1)
        
        while True:
            self.ui.display_simple_message("Select difficulty (1-3):", 0)
            choice = input(">>> ").strip()
            
            if choice in ['1', '2', '3']:
                difficulty_names = ['EASY', 'NORMAL', 'EXPERT']
                selected = difficulty_names[int(choice) - 1]
                self.ui.display_simple_message(f"Setting difficulty: {selected}")
                return int(choice) - 1
            else:
                self.ui.display_simple_message("Please select 1, 2, or 3.", 1)

    def enable_psychodynamics(self):
        """Enable market manipulation capabilities"""
        if 'psychodynamics' not in self.research.research_costs:
            self.research.research_costs['psychodynamics'] = 300
            self.research.research_benefits['psychodynamics'] = {'price_control': 0.15}

    def enable_trade_empire_features(self):
        """Enable advanced trading features"""
        self.trade_bonus = 0.2  # 20% better trade prices
        self.stockmarket_cost *= 0.8  # 20% cheaper stockmarkets
        self.ship.trade_reputation = True

    def enable_ancient_research(self):
        """Enable ancient technology research"""
        self.research.research_costs['ancient_tech'] = 500
        self.research.research_benefits['ancient_tech'] = {'tech_boost': 0.3}
        self.story_manager.story_states['ancient_research'] = True

    def enable_crisis_mastery(self):
        """Enable crisis management bonuses"""
        self.ship.crisis_bonus = True
        self.combat_bonus = 0.25  # 25% combat effectiveness
        self.repair_discount = 0.3  # 30% cheaper repairs

    def increase_threat_level(self):
        """Increase general threat level"""
        self.combat_difficulty *= 1.5
        self.pirate_frequency *= 1.5
        self.event_risk *= 1.25

    def activate_crisis_events(self):
        """Enable crisis-specific events"""
        self.crisis_active = True
        self.crisis_events = [
            "anomaly_surge",
            "system_instability",
            "mass_migration"
        ]
        self.event_probability *= 1.5

    def activate_endgame_events(self):
        """Enable endgame content"""
        self.endgame_active = True
        self.enable_stellar_portal = True
        self.legendary_items_available = True
        self.final_crisis_events = True
        
    def unlock_advanced_equipment(self):
        """Unlock advanced equipment in shop"""
        new_equipment = {
            "quantum_drive": 50000,
            "neutron_shield": 40000,
            "warp_core": 75000
        }
        self.shop.base_equipment.update(new_equipment)

    def get_trade_volume(self, location):
        """Calculate total trade volume at location"""
        if not hasattr(location, 'trade_history'):
            location.trade_history = []
        return sum(trade['value'] for trade in location.trade_history)

    def record_trade(self, location, value):
        """Record trade for statistics"""
        if not hasattr(location, 'trade_history'):
            location.trade_history = []
        location.trade_history.append({
            'turn': self.turn,
            'value': value
        })
        self.trades_completed += 1

    def check_controlled_locations(self):
        """Count player-controlled locations"""
        return len([loc for loc in self.locations if getattr(loc, 'controlled_by_player', False)])

    def get_chapter_statistics(self):
        """Get current chapter performance stats"""
        return {
            'trades': self.trades_completed,
            'combat': self.ship.combat_victories,
            'discoveries': len(self.known_locations),
            'research': self.ship.research_points,
            'wealth': self.ship.money
        }

    def trigger_crisis_event(self):
        """Handle crisis event generation"""
        if not self.crisis_active:
            return
        
        events = {
            "anomaly_surge": self.handle_anomaly,
            "system_instability": self.handle_instability,
            "mass_migration": self.handle_migration
        }
        
        event = random.choice(list(events.keys()))
        events[event]()

    def handle_anomaly(self):
        damage = random.randint(10, 30)
        self.ship.damage += damage
        self.ui.display_simple_message(f"Anomaly surge! Ship took {damage}% damage!")

    def handle_instability(self):
        loss = int(self.ship.money * 0.1)
        self.ship.money -= loss
        self.ui.display_simple_message(f"System instability! Lost {self.format_money(loss)} credits!")

    def handle_migration(self):
        for location in self.locations:
            location.market['tech'] *= 1.2
            location.market['agri'] *= 1.2
        self.ui.display_simple_message("Mass migration affecting market prices!")

    def handle_research_breakthrough(self):
        tech_boost = 0.2
        self.ship.research_points *= (1 + tech_boost)
        self.story_manager.trigger_milestone("tech_breakthrough")

    def handle_alien_artifact(self):
        reward = 10000 * (1 + self.story_manager.current_chapter)
        self.ship.money += reward
        self.story_manager.trigger_milestone("first_artifact")
        
    def check_final_crisis(self):
        return (self.story_manager.get_chapter_number() >= 5 and 
                self.check_controlled_locations() >= 3 and
                self.ship.research_points >= 1000)
    
    def update_story_progress(self):
        for location in self.locations:
            # Update story states based on world state
            if self.get_trade_volume(location) > 50000:
                self.story_manager.story_states["trade_empire"] = True
            if len([p for p in location.mining_platforms]) > 2:
                self.story_manager.story_states["resource_empire"] = True

    def check_story_requirements(self):
        """Check and update story progression each turn"""
        self.update_story_progress()
        if self.crisis_active:
            self.trigger_crisis_event()
        if self.check_final_crisis():
            self.activate_endgame_events()                    

    def get_player_name(self):
        self.clear_screen()
        
        display_logo(logo_data, centered=True) #modified here
        
        self.ui.display_simple_message([
            "Enter your pilot name",
            "Press Enter for random"
        ], 0)
        
        name = input(">>> ").strip()
        
        if not name:
            titles = ["Captain", "Commander", "Pilot", "Hauler", "Trucker", "Starfarer", "Operator", "Rigger","Freerunner","Navigator", "Doc", "Docker" ]
            surnames = ["Aen Stark", "Orr-Slagg", "Dragg Voxx", "Swigg", "Doc Brainac", "Json", "Nova", "Drake", "Phoenix", "Wolf", "Kayo Wu", "Lyra Nyx", "Elerra Solis", "Bryce", "Q'Ella", "Cael Yaro", "Q'Orin"]
            name = f"{random.choice(titles)} {random.choice(surnames)}"
            self.ui.display_simple_message(f"Neural Signature Verified: {name}")
        
        self.ui.display_simple_message(f"Welcome aboard, {name}!")    
        return name

    def display_starting_info(self):
        """Display initial game information with location context"""
        # Get location info based on current_location
        location_type = "an industrial"
        if self.current_location.agri_level > self.current_location.tech_level:
            location_type = "an agricultural"
        elif self.current_location.research_points > 15:
            location_type = "a research"

        intro_text = f"\n  You arrive on {self.current_location.name}, {location_type} {self.current_location.location_type.lower()}, where your adventure begins."
        special_events = [
            "Revolutions are happening!",
            "Economy boom!",
            "Technological advancements!",
            "Agricultural breakthroughs!",
            "Nothing special happening."
        ]
        special_event = random.choice(special_events)
        special_event_text = f"Special Event: {special_event}"

        self.display_story_message(self.word_wrap(intro_text))
        self.display_story_message(self.word_wrap(special_event_text))
        time.sleep(3)  # Pause to let the player read the information

    def word_wrap(self, text, width=None):
        if width is None:
            term_width = shutil.get_terminal_size().columns
            width = term_width - 4  # Account for padding

        words = text.split()
        lines = []
        current_line = []
        current_length = 0

        for word in words:
            if current_length + len(word) + len(current_line) > width:
                lines.append(' '.join(current_line))
                current_line = [word]
                current_length = len(word)
            else:
                current_line.append(word)
                current_length += len(word)

        if current_line:
            lines.append(' '.join(current_line))

        return lines

    def display_story_message(self, message, pause=2, style='round', color=None):
        if isinstance(message, list):
            box_content = message
        else:
            box_content = [message]

        box = self.ui.create_simple_box(box_content, style)
        if color:
            box = f"\033[{color}m{box}\033[0m"
        print(box)
        if pause > 0:
            time.sleep(pause)

    def display_character_message(self, character_name, message, pause=2, style='round', color=None):
        box_content = [f"{character_name}: {message}"]
        box = self.ui.create_simple_box(box_content, style)
        if color:
            box = f"\033[{color}m{box}\033[0m"
        print(box)
        if pause > 0:
            time.sleep(pause)
            
    def clear_screen(self):
        os.system('clear' if os.name == 'posix' else 'cls')

    def force_check_chapter_progression(self):
        """Manually trigger chapter progression checks"""
        current_chapter = self.story_manager.current_chapter
        current_chapter_obj = self.story_manager.chapters[current_chapter]
        
        # Check next possible chapters
        next_chapters = current_chapter_obj.get_next_chapters(self)
        
        if next_chapters:
            if len(next_chapters) > 1:
                self.story_manager.present_chapter_choice(next_chapters)
            else:
                self.story_manager.start_chapter(next_chapters[0].id)

# core/game.py

    def play(self):
        while True:
            # Play a turn
            turn_result = play_turn(self)
            
            # Check if player quit or resigned
            if turn_result == "quit":
                self.ui.display_simple_message("Thanks for playing!")
                break
            elif turn_result == "resign":
                self.ui.display_simple_message("Resigning from current game...")
                self.display_score()
                break
                
            self.update_rank()

            # Check game over conditions
            if self.ship.money <= 0 and self.ship.is_empty_cargo():
                self.ui.display_simple_message("Game Over: No money and no cargo left.", 2)
                self.display_score()
                break

            if self.ship.damage >= 100:
                self.ui.display_simple_message("Game Over: Ship destroyed!", 2)
                self.display_score()
                break

            # Check for special quest availability
            # Only check planets and locations that can have stockmarkets
            valid_locations = [loc for loc in self.locations 
                            if loc.location_type == "Planet" or 
                            loc.location_type in ["AsteroidBase", "DeepSpaceOutpost"]]
            
            if valid_locations and all(loc.stockmarket_base for loc in valid_locations):
                self.secret_quest_available = True
                resign = self.validate_input("Do you want to resign? (yes/no): ", ['yes', 'no'])
                if resign == 'yes':
                    self.display_score()
                    print("You are the Galactic Tycoon!")
                    print(f"Congratulations, {self.player_name}! You have achieved the rank of {self.rank}.")
                    print("Your story will be remembered throughout the galaxy.")
                    break
                else:
                    self.ui.display_simple_message("You have chosen to continue your adventure into the unknown.")
                    self.stellar_portal_available = True
                    if self.ship.money >= 1500:
                        self.ship.money -= 1500
                        self.ui.display_simple_message("You have paid for the secret quest and a Stellar Portal appears on this location.")
                        # Generate new locations
                        new_locations = self.generate_new_locations()
                        self.locations.extend(new_locations)
                        self.current_location = random.choice(new_locations)
                        self.known_locations = [self.current_location.name]
                        self.ui.display_simple_message("You have traveled to a new set of locations with more volatile price movements.")
                    else:
                        self.ui.display_simple_message("Not enough money to pay for the secret quest.")

            # Ask to play again
            if turn_result == "quit":
                play_again = self.validate_input("Do you want to play again? (yes/no): ", ['yes', 'no'])
                if play_again == 'yes':
                    self.__init__()
                    self.play()
                break

#    def generate_new_locations(self):

    
# missing methods

    def handle_passenger_celebration(self):
        """Handle passenger celebration event"""
        for module in self.ship.passenger_modules:
            for passenger in module.passengers:
                passenger.satisfaction = min(100, passenger.satisfaction + 10)
        self.ui.display_simple_message("Passengers are having a celebration! Satisfaction increased!")

    def handle_passenger_complaint(self):
        """Handle passenger complaint event"""
        for module in self.ship.passenger_modules:
            for passenger in module.passengers:
                passenger.satisfaction = max(0, passenger.satisfaction - 15)
        self.ui.display_simple_message("Passengers have filed complaints! Satisfaction decreased!")

    def handle_medical_emergency(self):
        """Handle medical emergency event"""
        cost = random.randint(500, 1500)
        if self.ship.money >= cost:
            self.ship.money -= cost
            self.ui.display_simple_message(f"Medical emergency handled! Cost: {self.format_money(cost)}")
        else:
            # If can't afford medical care, big satisfaction hit
            for module in self.ship.passenger_modules:
                for passenger in module.passengers:
                    passenger.satisfaction = max(0, passenger.satisfaction - 30)
            self.ui.display_simple_message("Couldn't afford medical care! Passengers very unhappy!")

    def handle_vip_request(self):
        """Handle VIP passenger request"""
        cost = random.randint(1000, 2000)
        if self.ship.money >= cost:
            self.ship.money -= cost
            self.ship.passenger_reputation += 2
            self.ui.display_simple_message(f"VIP request handled! Cost: {self.format_money(cost)}, Reputation increased!")
        else:
            self.ship.passenger_reputation = max(0, self.ship.passenger_reputation - 1)
            self.ui.display_simple_message("Couldn't fulfill VIP request! Reputation decreased!")

    def handle_passenger_trade_info(self):
        """Handle passengers sharing trade information"""
        # Reveal profitable trade opportunities
        self.ui.display_simple_message("Passengers shared valuable trade information!")
        # Implement trade tip functionality here
        
    def check_location_events(self, event_type):
        """Handle location-specific event consequences"""
        location = self.current_location
        
        if location.location_type == "AsteroidBase":
            if event_type == "disaster":
                # Asteroid bases might discover new mining opportunities after disasters
                if random.random() < 0.2:
                    mineral_type = random.choice(["salt", "fuel"])
                    amount = random.randint(1000, 3000)
                    location.mineral_deposits[mineral_type] = location.mineral_deposits.get(mineral_type, 0) + amount
                    self.ui.display_simple_message(f"The disaster revealed new {mineral_type} deposits!")
                    
        elif location.location_type == "ResearchColony":
            if event_type == "exploration":
                # Research colonies might gain research points from exploration events
                bonus_points = random.randint(10, 30)
                self.ship.research_points += bonus_points
                self.ui.display_simple_message(f"Colony researchers analyzed the phenomenon: +{bonus_points} RP")
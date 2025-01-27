# core/character_encounters.py
import random
import yaml
from core.template import CharacterTemplate

class SpecialCharacterEncounters:
    def __init__(self, game):
        self.game = game
        self.encounter_chances = {
            "Planet": {
                "merchant": 0.3,
                "researcher": 0.4,
                "rogue_captain": 0.0  # Not on planets
            },
            "AsteroidBase": {
                "merchant": 0.2,
                "researcher": 0.1,
                "rogue_captain": 0.3
            },
            "DeepSpaceOutpost": {
                "merchant": 0.3,
                "researcher": 0.3,
                "rogue_captain": 0.5
            },
             "ResearchColony": {
                "merchant": 0.2,
                "researcher": 0.6,
                "rogue_captain": 0.0
             },
            "Space": {  # For random events
                "merchant": 0.2,
                "researcher": 0.1,
                "rogue_captain": 0.4
            }
        }
        self.enemy_data = self.load_enemy_data()
        self.templates = CharacterTemplate.load_character_templates("data/characters.yml")

    def load_enemy_data(self):
        """Load enemy data from data/enemies.yml"""
        try:
            with open("data/enemies.yml", 'r') as f:
                import yaml
                return yaml.safe_load(f)
        except FileNotFoundError:
            print("Error: enemies.yml not found. Using default enemy data.")
            return {}
        except yaml.YAMLError as e:
            print(f"Error loading enemies from YAML: {e}")
            return {}    

    def generate_character(self, character_type):
         """Generate a new character based on character type using templates"""
         
         if character_type == 'merchant':
            return self.game.character_generators["human"].generate_character("merchant_trader")
         elif character_type == 'researcher':
            return self.game.character_generators["human"].generate_character(
                title="Research Coordinator",
                specialization="research"
            )
         elif character_type == 'rogue_captain':
             return self.game.character_generators["human"].generate_character("PirateCaptain")
         return None

    def generate_merchant_offers(self):
        """Generate random merchant offers"""
        offers = []
        possible_items = [
            ("quantum_shield", 3000, "Advanced defense system"),
            ("neural_boost", 2500, "Research point multiplier"),
            ("cargo_expander", 4000, "Increased storage capacity"),
            ("stealth_drive", 5000, "Improved escape chances")
        ]
        return random.sample(possible_items, random.randint(2, 3))


    def handle_merchant_encounter(self, character):
        """Handle interaction with merchant"""
        content = [
            [f"Encounter: {character.full_name}"],
            [character.content["dialogue"]["first_meeting"][0]],
            [""],
            ["Available Items:"]
        ]
        
        for i, offer in enumerate(self.generate_merchant_offers(), 1):
            content.append([
                f"{i}. {offer[0].title()}",
                f"¤: {self.game.format_money(offer[1])}",
                offer[2]
            ])
            
        print(self.game.ui.create_box(content, 'double'))
        
        options = [str(i) for i in range(1, 4)] + ['0']
        choice = self.game.validate_input("Choose item to buy (0 to leave): ", options)

        # If choice is None, return immediately
        if choice is None:
            return

        if choice == '0':
            return
            
        offer = self.generate_merchant_offers()[int(choice) - 1]
        if self.game.ship.money >= offer[1]:
            self.game.ship.money -= offer[1]
            self.game.ship.acquire_item(offer[0])
            self.mark_item_sold(offer[0])
            self.game.ui.display_simple_message(f"You bought a {offer[0]}!")
        else:
            self.game.ui.display_simple_message("Insufficient funds!")

    def handle_researcher_encounter(self, character):
        """Handle interaction with researcher"""
        exchange_rate = random.randint(500, 1000)
        max_points = int(self.game.ship.research_points / exchange_rate)
        
        content = [
            [f"Encounter: {character.full_name}"],
            [f"Your data could advance our understanding..."],
            [""],
            [f"Exchange Rate: {self.game.format_money(exchange_rate)} credits per research point"],
            [f"Your funds: {self.game.format_money(self.game.ship.money)}"],
            [f"Maximum points available: {max_points}"]
        ]
        print(self.game.ui.create_box(content, 'double'))
        
        amount = self.game.validate_quantity_input("Enter research points to buy (max/m, half/h): ")
        if amount is None:
            return
        
        if amount == 'max':
            amount = max_points
        elif amount == 'half':
            amount = (max_points) // 2
            
        total_cost = amount * exchange_rate
        if self.game.ship.money >= total_cost:
            self.game.ship.money -= total_cost
            self.game.ship.research_points += amount
            self.game.ui.display_simple_message(
                f"Exchanged {self.game.format_money(total_cost)} credits for {amount} research points!"
            )
        else:
            self.game.ui.display_simple_message("Insufficient funds!")

    def handle_rogue_captain_encounter(self, character):
        """Handle interaction with rogue captain"""
        content = [
            [f"Encounter: {character.full_name}"],
            ["Your cargo or your ship..."],
            [""],
            [f"Demands {self.game.format_money(random.randint(5000, 15000))} credits"],
            [""],
            ["Options:"],
            ["1. Pay demand"],
            ["2. Attempt to flee"],
            ["3. Stand and fight"]
        ]
        print(self.game.ui.create_box(content, 'double'))
        
        choice = self.game.validate_input("Choose action (1/2/3): ", ['1', '2', '3'])
        
        if choice == '1':
            if self.game.ship.money >= character.demand:
                self.game.ship.money -= character.demand
                self.game.ui.display_simple_message("Demand paid. Rogue captain lets you pass.")
                return True
            else:
                self.game.ui.display_simple_message("Can't pay! Prepare for combat!")
                return False
        elif choice == '2':
            # Chance to escape based on speed
            escape_chance = min(0.8, self.game.ship.speed * 0.2)
            if random.random() < escape_chance:
                self.game.ui.display_simple_message("Successfully evaded the rogue captain!")
                return True
            else:
                self.game.ui.display_simple_message("Failed to escape! Prepare for combat!")
                return False
        else:
            self.game.ui.display_simple_message("Preparing for combat with rogue captain...")
            return False

    def trigger_random_encounter(self, location_type="Space"):
        """Trigger a random character encounter"""
        chances = self.encounter_chances[location_type]
        for char_type, chance in chances.items():
            if random.random() < chance:
                character = self.generate_character(char_type)
                
                if char_type == "merchant":
                    self.handle_merchant_encounter(character)
                elif char_type == "researcher":
                    self.handle_researcher_encounter(character)
                elif char_type == "rogue_captain":
                    if not self.handle_rogue_captain_encounter(character):
                        # Start combat with enhanced enemy stats
                        enemy = self.enemy_data.get('pirate_scout')  # Default pirate for testing
                        enemy_stats = {
                            "attack": self.game.ship.attack + enemy["attack"],
                            "defense": self.game.ship.defense + enemy["defense"],
                            "type": "rogue_captain"
                        }
                        self.game.handle_combat(enemy_stats)
                break
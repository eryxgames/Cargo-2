# core/character.py
import random
import yaml
from core.template import CharacterTemplate

class SpecialCharacter:
    def __init__(self, title, name, role, specialization):
        self.title = title
        self.name = name
        self.role = role
        self.specialization = specialization
        self.full_name = f"{title} {name}"
        self.met = False
        self.quests_given = []
        self.relationship = 0  # -100 to 100
        self.last_interaction = None
        self.location_preference = None
        self.special_contracts = []

class SpecialCharacterGenerator:
    def __init__(self, game):
        self.game = game  # Store game instance
        self.templates = CharacterTemplate.load_character_templates("data/characters.yml")
        
        self.titles = {
            "military": ["Fleet Commander", "Fleet Admiral", "Security Chief", "Defense Director"],
            "science": ["Research Coordinator", "Science Director", "Chief Researcher", "Lab Supervisor"],
            "trade": ["Trade Minister", "Commerce Director", "Market Supervisor", "Exchange Chief"],
            "engineering": ["Engineering Chief", "Tech Director", "Systems Coordinator", "Project Lead"]
        }
        
        self.surnames = ["Wu", "Cheng", "Tahoe", "Singh", "Patel", "Kim", "Rodriguez", "Novak", 
                        "Chen", "Zhang", "Yamamoto", "Anderson", "Silva", "Kumar", "Hassan"]
        
        self.roles = {
            "military": ["Combat training", "Fleet operations", "Security protocols", "Defense systems"],
            "science": ["Research projects", "Lab experiments", "Data analysis", "Discovery missions"],
            "trade": ["Market analysis", "Trade routes", "Economic planning", "Resource management"],
            "engineering": ["System upgrades", "Tech maintenance", "Innovation projects", "Infrastructure"]
        }
        
        self.known_characters = {}  # Track generated characters
        self.add_vip_templates()

    def generate_character(self, char_type=None):
        """Generate a character with optional title and specialization"""
        if char_type in self.templates:
            template = self.templates[char_type]
            title = random.choice(template.content["basic_info"]["title_pool"])
            name = self.generate_name_from_pattern(title, template.content["basic_info"].get("name_pattern"), template.content["basic_info"].get("type"))
            character = SpecialCharacter(
                title = title,
                name = name,
                role = template.content["basic_info"]["specialization"],
                specialization = template.content["basic_info"]["specialization"]
            )
            character.content = template.content
            return character
        return None
    
    def generate_name_from_pattern(self, title, name_patterns, type=None):
        """Generate a name using provided pattern with available data"""
        if not name_patterns:
           return random.choice(self.surnames)
           
        name_pattern = random.choice(name_patterns)
        
        # Fill placeholders from different sources
        if type == "synthetic":
            name = name_pattern.format(
                number = random.choice(["alpha", "prime", "omega", "zero"]).upper()
            )
        else:
            name = name_pattern.format(
                title = title,
                surname = random.choice(self.surnames),
                culture = random.choice(self.alien_cultures) if hasattr(self, "alien_cultures") else ""
            )
        return name.capitalize()

    # Added to SpecialCharacterGenerator class for vip passengers
    def add_vip_templates(self):
        """Add VIP passenger templates to character generator"""
        self.vip_templates = {}
        for key, template in self.templates.items():
            if template.content.get('basic_info',{}).get('type') == 'VIPPassenger':
                self.vip_templates[key] = template.content

    def generate_vip_passenger(self):
        """Generate a VIP passenger with special characteristics"""
        vip_type = random.choice(list(self.vip_templates.keys()))
        template = self.vip_templates[vip_type]
        
        title = random.choice(template["title_pool"])
        name = self.generate_name_from_pattern(title, template.get("name_pattern"), "human")
        role = random.choice(template["roles"])
        
        character = SpecialCharacter(
            title=f"{vip_type} {title}",
            name=name,
            role=role,
            specialization="VIP"
        )
        
        # Add VIP-specific attributes
        character.rewards = dict(template["rewards"])
        character.special_abilities = list(template.get("special_abilities", []))
        
        # Scale rewards based on reputation
        reputation_multiplier = 1 + (self.game.ship.passenger_reputation / 100)
        character.rewards["base_money"] = int(character.rewards["base_money"] * reputation_multiplier)
        
        return character

class SyntheticCharacterGenerator:
    """Generator for synthetic characters like Neurodroids and Agrobots"""
    
    def __init__(self, game):
        self.game = game
        self.templates = CharacterTemplate.load_character_templates("data/characters.yml")
        self.synthetic_types = {}
        for key, template in self.templates.items():
            if template.content.get('basic_info', {}).get('type') == "synthetic":
                self.synthetic_types[key] = template.content

    def generate_character(self, char_type):
        """Generate a synthetic character of specified type"""
        template = self.synthetic_types.get(char_type)
        if template:
            title = random.choice(template["title_pool"])
            name = self.generate_name_from_pattern(title, template.get("name_pattern"), template.get("type"))
            character = SpecialCharacter(title, name, "synthetic", char_type.lower())
            character.content = template
            character.demand = random.randint(10000, 50000)
            character.uprising_chance = 0.3
            return character
        return None

class AlienCharacterGenerator:
    """Generator for alien characters that appear later in the game"""
    
    def __init__(self,game):
        self.game = game
        self.templates = CharacterTemplate.load_character_templates("data/characters.yml")
        self.alien_cultures = []
        for key, template in self.templates.items():
            if template.content.get('basic_info', {}).get('type') == "alien":
                self.alien_cultures = template.content.get("cultures", [])

        self.titles = [
            "Emissary", "Observer", "Overseer", "Ambassador", "Neo-Eryxian"
        ]
        self.specializations = [
            "diplomacy", "technology", "commerce", "research", "military"
        ]

    def generate_character(self, char_type=None):
        """Generate an alien character"""
        template = self.templates.get(char_type.lower())
        if template:
            culture = random.choice(self.alien_cultures)
            title = random.choice(template.content["title_pool"])
            name = self.generate_name_from_pattern(title, template.content.get("name_pattern"), template.content["basic_info"].get("type"))
            specialization = random.choice(self.specializations)
            
            character = SpecialCharacter(
                title=f"{culture} {title}",
                name=name,
                role="alien_contact",
                specialization=specialization
            )
            
            # Add alien-specific attributes
            character.culture = culture
            character.tech_bonus = random.randint(1, 5)
            character.trade_multiplier = 1 + (random.randint(1, 5) / 10)
            character.content = template.content
            return character
        return None

    def generate_alien_name(self, culture):
        """Generate culturally appropriate alien name"""
        name_patterns = {
            "Zentari": ["'", "-", "x"],
            "Novaren": ["ae", "eo", "ia"],
            "Qyth": ["q", "y", "th"],
            "Xylax": ["x", "z", "ax"],
            "Merovian": ["v", "m", "ian"]
        }
        
        patterns = name_patterns[culture]
        syllables = random.randint(2, 3)
        name = ""
        
        for _ in range(syllables):
            name += random.choice("aeiou")
            name += random.choice("bcdfghjklmnpqrstvwxyz")
            if random.random() < 0.5:
                name += random.choice(patterns)
                
        return name.capitalize()
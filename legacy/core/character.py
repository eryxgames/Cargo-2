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
    
# core/character.py
# Removed here as now in template.py
# class CharacterTemplate:

class CharacterManager:
    def __init__(self, game):
        self.game = game
        self.templates = CharacterTemplate.load_character_templates("data/characters.yml")
        self.active_characters = {}
        self.met_characters = set()
        self.current_interactions = {}

    def update(self):
        """Check for character spawning each turn"""
        self.cleanup_old_characters()  # Add this line first

        location_type = self.game.current_location.location_type.lower()
        
        # Check each template for possible spawning
        for template_id, template in self.templates.items():
            if 'requirements' in template.content and location_type in template.content['requirements'].get('spawn_locations', []):
                if random.random() < template.content['requirements'].get('spawn_chance', 0):
                    character = self.spawn_character(template_id, self.game.current_location)
                    if character:
                        self.announce_character(character.character_id)

    def generate_character_from_template(self, template_id):
        """Create character instance from template"""
        if template_id not in self.templates:
            return None
            
        template = self.templates[template_id]
        basic_info = template.content['basic_info']
        
        # Generate name
        title = random.choice(basic_info['title_pool'])
        
        # Create character
        character = CharacterTemplate(
            character_id=f"{template_id}_{self.game.turn}",
            content=template.content
        )
        
        # Add runtime attributes
        character.full_name = title
        character.template_id = template_id
        
        return character

    def spawn_character(self, template_id, location):
        """Spawn a character from template at location"""
        template = self.templates[template_id]
        
        # Check spawn requirements
        if not self.check_spawn_requirements(template, location):
            return None
            
        # Generate character
        character = self.generate_character_from_template(template_id)
        
        # Add to active characters
        char_id = f"{template_id}_{self.game.turn}"
        self.active_characters[char_id] = {
            "character": character,
            "location": location,
            "spawn_turn": self.game.turn
        }
        
        return character

    def check_spawn_requirements(self, template, location):
        """Check if character can spawn based on requirements"""
        if 'requirements' not in template.content:
            return False
        reqs = template.content["requirements"]
        
        # Check location
        if location not in reqs.get("spawn_locations", []):
            return False
            
        # Check reputation
        if self.game.ship.passenger_reputation < reqs.get("min_reputation", 0):
            return False
            
        # Check chance
        if random.random() > reqs.get("spawn_chance", 0.1):
            return False
            
        return True

    def get_character_dialogue(self, character_id, dialogue_type, **kwargs):
        """Get appropriate dialogue for character and context"""
        character = self.active_characters[character_id]["character"]
        template = self.templates[character.template_id]
        
        dialogue_pool = template.content["dialogue"].get(dialogue_type, [])
        if not dialogue_pool:
            return ""
            
        dialogue = random.choice(dialogue_pool)
        return dialogue.format(**kwargs)

    def handle_character_interaction(self, character_id, choice, location_type):
        """Process player interaction with character"""
        character = self.active_characters[character_id]["character"]
        template = self.templates[character.template_id]
        
        # Get available interactions for location
        interactions = template.content["interactions"].get(location_type, [])
        if not interactions or choice >= len(interactions):
            return False
            
        # Process interaction
        interaction = interactions[choice]
        return self.process_interaction_outcome(character_id, interaction)

    def cleanup_old_characters(self):
        """Remove characters that have been around too long"""
        current_turn = self.game.turn
        for char_id in list(self.active_characters.keys()):
            if current_turn - self.active_characters[char_id]["spawn_turn"] > 5:  # 5 turn lifetime
                del self.active_characters[char_id]  

    def process_interaction_outcome(self, character_id, interaction):
        """Process the result of a character interaction"""
        character = self.active_characters[character_id]
        template = self.templates[character["character"].template_id]
        
        # Apply rewards if any
        if 'rewards' in template.content:
            if 'money' in template.content['rewards']:
                self.game.ship.money += template.content['rewards']['money']
            if 'reputation_gain' in template.content['rewards']:
                self.game.ship.passenger_reputation += template.content['rewards']['reputation_gain']
            if 'plot_points' in template.content['rewards']:
                self.game.story_manager.plot_points += template.content['rewards']['plot_points']
        
        return True
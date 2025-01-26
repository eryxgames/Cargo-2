# core/template.py
import yaml
import os

class CharacterTemplate:
    """Central template for character content and behavior"""
    def __init__(self, character_id, content):
        self.character_id = character_id
        self.content = content
        self.validate_content()

    def validate_content(self):
        """Ensure all required content sections exist"""
        required_sections = {
            'basic_info',   # Always required
            'dialogue'      # Always required
        }
        
        optional_sections = {
            'interactions',
            'requirements',
            'rewards'
        }
        
        missing = required_sections - set(self.content.keys())
        if missing:
            raise ValueError(f"Missing required sections: {missing}")
            
        # Add any optional sections that don't exist as empty dicts
        for section in optional_sections:
            if section not in self.content:
                self.content[section] = {}

    @staticmethod
    def load_character_templates(filepath):
        """Load all character templates from a YAML file"""
        try:
            with open(filepath, 'r') as f:
                data = yaml.safe_load(f)
                if not data:
                    print("Warning: characters.yml is empty.")
                    return {}
                return {key: CharacterTemplate(key, value) for key, value in data.items()}
        except FileNotFoundError:
            print("Error: characters.yml not found. No character templates loaded.")
            return {}
        except yaml.YAMLError as e:
             print(f"Error loading character templates from YAML: {e}")
             return {}
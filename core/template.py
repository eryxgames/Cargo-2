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
        """Ensure that content is a dictionary"""
        if not isinstance(self.content, dict):
            raise ValueError(f"Character content must be a dictionary, not {type(self.content)}")

    @staticmethod
    def load_character_templates(filepath):
        """Load all character templates from a YAML file"""
        try:
            with open(filepath, 'r') as f:
                data = yaml.safe_load(f)
                if not data:
                    print("Warning: characters.yml is empty.")
                    return {}
                # Only create CharacterTemplate if content is a dict, skip if its list
                return {
                    key: CharacterTemplate(key, value)
                    for key, value in data.items()
                    if isinstance(value, dict)
                }
        except FileNotFoundError:
            print("Error: characters.yml not found. No character templates loaded.")
            return {}
        except yaml.YAMLError as e:
             print(f"Error loading character templates from YAML: {e}")
             return {}
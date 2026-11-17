# ui/theme_manager.py
import json
import os

class ThemeManager:
    def __init__(self, themes_path, assets_path):
        self.themes_path = themes_path
        self.assets_path = assets_path
        self.themes = self.load_themes()
        self.current_theme = {}

    def load_themes(self):
        """Load all themes from themes.json"""
        try:
            with open(self.themes_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: Theme file not found at {self.themes_path}")
            return {}
        except json.JSONDecodeError:
            print(f"Error: Could not parse themes file at {self.themes_path}")
            return {}

    def load_theme(self, theme_name):
        """Load specific theme and set as current"""
        if theme_name not in self.themes:
            print(f"Warning: Theme '{theme_name}' not found.")
            return

        theme_path = self.themes[theme_name].get("path")
        full_path = os.path.join(self.assets_path, theme_path)

        try:
            with open(full_path, 'r') as f:
                self.current_theme = json.load(f)
                print(f"Theme '{theme_name}' loaded.")
        except FileNotFoundError:
            print(f"Error: Theme file not found at {full_path}")
        except json.JSONDecodeError:
            print(f"Error: Could not parse theme file at {full_path}")

    def get_style(self, style_key):
        """Get a specific style from the current theme"""
        return self.current_theme.get(style_key, {})
# cargo.py
import os
import json
import pygame
from core.game import Game
from ui.text_ui import TextUI
from ui.theme_manager import ThemeManager
from core.audio import AudioManager

def load_settings():
    """Load game settings from JSON file."""
    try:
        with open("data/settings.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: settings.json not found. Using default settings.")
        return {}
    except json.JSONDecodeError:
        print("Error: Could not parse settings.json. Using default settings.")
        return {}

def main():
    # Initialize Pygame
    pygame.init()

    # Load game settings
    settings = load_settings()
    
    # Initialize ThemeManager
    theme_manager = ThemeManager("data/themes.json", "assets/themes/")
    active_theme = settings.get("active_theme", "default")
    theme_manager.load_theme(active_theme)
    
    # Initialize text-based UI
    ui = TextUI(theme_manager)  # Pass ThemeManager to UI
    
    # Initialize the game
    game = Game(settings=settings, ui=ui) # Pass settings and ui
    
    # Start the game
    game.play()
    
    # Quit pygame
    pygame.quit()

if __name__ == "__main__":
    main()
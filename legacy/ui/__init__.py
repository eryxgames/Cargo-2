# ui/__init__.py
#from ui.text_ui import TextUI # Remove TextUI import
from ui.theme_manager import ThemeManager

class UI_Interface:
    def create_simple_box(self, content, style='single'):
        raise NotImplementedError
    def create_box(self, content, style='single'):
        raise NotImplementedError
    def create_character_box(self, character_content, style='round'):
        raise NotImplementedError
    def display_simple_message(self, message, pause=1, style='round', color=None):
        raise NotImplementedError
    def display_message(self, message, pause=2, style='round', color=None):
        raise NotImplementedError
    def validate_input(self, prompt, valid_options):
        raise NotImplementedError
    def word_wrap(self, text, width=None):
         raise NotImplementedError
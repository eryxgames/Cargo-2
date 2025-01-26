# core/utils.py
import os
import shutil
import time
from math import floor

def display_logo(logo, centered=True):
    """Displays the logo, optionally centered."""
    try:
        terminal_width = os.get_terminal_size().columns
    except OSError:
        terminal_width = 80  # Default if not in a terminal

    for line in logo:
        if centered:
            padding = (terminal_width - len(line)) // 2
            print(" " * padding + line)
        else:
            print(line)  # Just print without centering

def print_centered_text(text):
    try:
        terminal_width = os.get_terminal_size().columns
    except OSError:
        terminal_width = 80  # Default if not in a terminal
    print(text.center(terminal_width))

def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

def word_wrap(text, width=None):
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

def format_money(amount):
        if amount >= 1_000_000_000:
            return f"{amount/1_000_000_000:.1f}B"
        elif amount >= 1_000_000:
            return f"{amount/1_000_000:.1f}M"
        elif amount >= 1_000:
            return f"{amount/1_000:.1f}K"
        return str(floor(amount))
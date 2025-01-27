# ui/text_ui.py
import os
import shutil
import time

class TextUI:
    def __init__(self, theme_manager=None):
        self.theme_manager = theme_manager
        self.default_theme = {
            "background_color": None,
            "text_color": "37",
            "header_color": "33",
            "success_color": "32",
            "error_color": "31",
            "warning_color": "33",
            "box_style": "single"
        }
        self.available_themes = []
        if theme_manager:
            self.available_themes = list(theme_manager.themes.keys())
        self.current_theme_index = 0


    def get_current_theme(self):
        return self.theme_manager.current_theme if self.theme_manager else self.default_theme

    def create_simple_box(self, content, style='single'):
        term_width = shutil.get_terminal_size().columns
        width = term_width - 4  # Adjust for padding
        theme = self.get_current_theme()
        chars = {
            'single': {'tl': '┌', 'tr': '┐', 'bl': '└', 'br': '┘', 'h': '─', 'v': '│'},
            'double': {'tl': '╔', 'tr': '╗', 'bl': '╚', 'br': '╝', 'h': '═', 'v': '║'},
            'round': {'tl': '╭', 'tr': '╮', 'bl': '╰', 'br': '╯', 'h': '─', 'v': '│'},
            'bold': {'tl': '▛', 'tr': '▜', 'bl': '▙', 'br': '▟', 'h': '█', 'v': '▌'},
            'dashed': {'tl': '╌', 'tr': '╌', 'bl': '╌', 'br': '╌', 'h': '╌', 'v': '╎'},
            'dotted': {'tl': ':', 'tr': ':', 'bl': ':', 'br': ':', 'h': '.', 'v': '.'},
            'thick': {'tl': '┏', 'tr': '┓', 'bl': '┗', 'br': '┛', 'h': '━', 'v': '┃'},
            'block': {'tl': '█', 'tr': '█', 'bl': '█', 'br': '█', 'h': '█', 'v': '█'},
            'slant': {'tl': '╱', 'tr': '╲', 'bl': '╲', 'br': '╱', 'h': '—', 'v': '|'},
            'none': {'tl': '', 'tr': '', 'bl': '', 'br': '', 'h': ' ', 'v': ' '}
        }[style if style else theme.get("box_style", "single")]

        lines = []
        if style != 'none':
             lines.append(f"{chars['tl']}{chars['h'] * width}{chars['tr']}")

        for row in content:
            wrapped_row = self.word_wrap(row, width - 2)
            for line in wrapped_row:
                text_color = theme.get("text_color", "37")
                lines.append(f"{chars['v']} \033[{text_color}m{line:<{width-2}}\033[0m {chars['v']}")

        if style != 'none':
            lines.append(f"{chars['bl']}{chars['h'] * width}{chars['br']}")
        return '\n'.join(lines)
    
    def create_box(self, content, style='single'):
        """Create a box that expands to terminal width with proportionally sized columns."""
        # Get terminal width and account for borders and spacing
        term_width = shutil.get_terminal_size().columns
        usable_width = term_width - 4  # Account for borders and minimum spacing
        
        # Get theme data
        theme = self.get_current_theme()

        # Define box characters
        chars = {
            'single': {'tl': '┌', 'tr': '┐', 'bl': '└', 'br': '┘', 'h': '─', 'v': '│', 'sep': '│'},
            'double': {'tl': '╔', 'tr': '╗', 'bl': '╚', 'br': '╝', 'h': '═', 'v': '║', 'sep': '║'},
            'round': {'tl': '╭', 'tr': '╮', 'bl': '╰', 'br': '╯', 'h': '─', 'v': '│', 'sep': '│'},
            'bold': {'tl': '▛', 'tr': '▜', 'bl': '▙', 'br': '▟', 'h': '█', 'v': '▌', 'sep': '│'},
            'dashed': {'tl': '╌', 'tr': '╌', 'bl': '╌', 'br': '╌', 'h': '╌', 'v': '╎', 'sep': '╎'},
            'dotted': {'tl': ':', 'tr': ':', 'bl': ':', 'br': ':', 'h': '.', 'v': '.', 'sep': '.'},
            'thick': {'tl': '┏', 'tr': '┓', 'bl': '┗', 'br': '┛', 'h': '━', 'v': '┃', 'sep': '┃'},
            'block': {'tl': '█', 'tr': '█', 'bl': '█', 'br': '█', 'h': '█', 'v': '█', 'sep': '█'},
            'slant': {'tl': '╱', 'tr': '╲', 'bl': '╲', 'br': '╱', 'h': '—', 'v': '|', 'sep': '│'},
             'none': {'tl': '', 'tr': '', 'bl': '', 'br': '', 'h': ' ', 'v': ' ', 'sep': ' '}
        }[style if style else theme.get("box_style", "single")]

        # Calculate number of columns and get content lengths
        num_cols = max(len(row) for row in content)
        max_lengths = [0] * num_cols
        
        # Get maximum content length for each column
        for row in content:
            for i, cell in enumerate(row):
                if i < num_cols:
                    max_lengths[i] = max(max_lengths[i], len(str(cell)))

        # Calculate spacing requirements
        separator_space = 3  # Space for " │ " between columns
        total_separator_width = separator_space * (num_cols - 1)
        padding_width = 2  # Space for padding around content " x "
        
        # Calculate available space for content
        available_content_width = usable_width - total_separator_width - padding_width
        
        # Calculate proportional column widths
        total_content_length = sum(max_lengths)
        col_widths = []
        remaining_width = available_content_width
        
        for i in range(num_cols):
            if i == num_cols - 1:
                # Last column gets remaining width
                width = remaining_width
            else:
                # Calculate proportional width
                proportion = max_lengths[i] / total_content_length
                width = max(3, min(
                    int(available_content_width * proportion),
                    max_lengths[i] + 2
                ))
                remaining_width -= width
            col_widths.append(width)

        # Ensure minimum widths and adjust if necessary
        for i in range(num_cols):
            col_widths[i] = max(3, min(col_widths[i], max_lengths[i] + 10))

        # Calculate final horizontal width
        horizontal_width = sum(col_widths) + total_separator_width + padding_width

        # Create the box
        lines = []
        
        # Top border
        if style != 'none':
            lines.append(f"{chars['tl']}{chars['h'] * horizontal_width}{chars['tr']}")
        
        # Content rows
        for row in content:
            # Pad row with empty strings if necessary
            padded_row = row + [''] * (num_cols - len(row))
            
            # Format each cell
            formatted_cells = []
            for i, cell in enumerate(padded_row):
                cell_str = str(cell)
                if len(cell_str) > col_widths[i]:
                    cell_str = cell_str[:col_widths[i]-3] + "..."
                formatted_cells.append(f"{cell_str:<{col_widths[i]}}")
            
            # Join cells with separators
            row_str = f"{chars['v']} {(' ' + chars['sep'] + ' ').join(formatted_cells)} {chars['v']}"
            lines.append(row_str)
        
        # Bottom border
        if style != 'none':
             lines.append(f"{chars['bl']}{chars['h'] * horizontal_width}{chars['br']}")
        
        return '\n'.join(lines)
    
    def create_character_box(self, character_content, style='round'):
        """Create a character display box optimized for different terminal widths"""
        try:
            term_width = os.get_terminal_size().columns
        except OSError:
            term_width = 80  # Default width
                
        # Adjust width based on terminal size
        if term_width < 60:
            content_width = term_width - 4
            compact_mode = True
        else:
            content_width = min(80, term_width - 4)  # Cap at 80 chars
            compact_mode = False
        theme = self.get_current_theme()    
        chars = {
            'round': {'tl': '╭', 'tr': '╮', 'bl': '╰', 'br': '╯', 'h': '─', 'v': '│'},
            'double': {'tl': '╔', 'tr': '╗', 'bl': '╚', 'br': '╝', 'h': '═', 'v': '║'},
            'single': {'tl': '┌', 'tr': '┐', 'bl': '└', 'br': '┘', 'h': '─', 'v': '│'},
            'bold': {'tl': '▛', 'tr': '▜', 'bl': '▙', 'br': '▟', 'h': '█', 'v': '▌'},
            'dashed': {'tl': '╌', 'tr': '╌', 'bl': '╌', 'br': '╌', 'h': '╌', 'v': '╎'},
            'dotted': {'tl': ':', 'tr': ':', 'bl': ':', 'br': ':', 'h': '.', 'v': '.'},
            'thick': {'tl': '┏', 'tr': '┓', 'bl': '┗', 'br': '┛', 'h': '━', 'v': '┃'},
            'block': {'tl': '█', 'tr': '█', 'bl': '█', 'br': '█', 'h': '█', 'v': '█'},
            'slant': {'tl': '╱', 'tr': '╲', 'bl': '╲', 'br': '╱', 'h': '—', 'v': '|'},
             'none': {'tl': '', 'tr': '', 'bl': '', 'br': '', 'h': ' ', 'v': ' '}
        }[style if style else theme.get("box_style", "single")]
            
        lines = []
        if style != 'none':
            lines.append(f"{chars['tl']}{chars['h'] * content_width}{chars['tr']}")
            
        # Process title section
        if 'title' in character_content:
            wrapped_title = self.word_wrap(character_content['title'], content_width - 2)
            for line in wrapped_title:
                header_color = theme.get("header_color", "33")
                lines.append(f"{chars['v']} \033[{header_color}m{line:<{content_width-2}}\033[0m {chars['v']}")
            if style != 'none':
                lines.append(f"{chars['v']}{chars['h'] * content_width}{chars['v']}")
            
        # Process main content with proper sections
        for section in ['introduction', 'description', 'demands', 'options']:
            if section in character_content:
                if not compact_mode:
                    lines.append(f"{chars['v']}{' ' * content_width}{chars['v']}")
                    
                wrapped_content = self.word_wrap(character_content[section], content_width - 2)
                for line in wrapped_content:
                    text_color = theme.get("text_color", "37")
                    lines.append(f"{chars['v']} \033[{text_color}m{line:<{content_width-2}}\033[0m {chars['v']}")
        
        if style != 'none':
             lines.append(f"{chars['bl']}{chars['h'] * content_width}{chars['br']}")
        return '\n'.join(lines)

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

    def display_simple_message(self, message, pause=1, style='round', color=None):
        if isinstance(message, list):
            box_content = message
        else:
            box_content = [message]

        box = self.create_simple_box(box_content, style)
        if color:
            box = f"\033[{color}m{box}\033[0m"
        print(box)
        if pause > 0:
            time.sleep(pause)
            
    def display_message(self, message, pause=2, style='round', color=None):
        if isinstance(message, list):
            box_content = message
        else:
            box_content = [message]

        box = self.create_box(box_content, style)
        if color:
            box = f"\033[{color}m{box}\033[0m"
        print(box)
        if pause > 0:
            time.sleep(pause)

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
            self.display_simple_message(wrapped_prompt, 0)

            try:
                user_input = input(">>> ").strip().lower()
                if not user_input:
                    self.display_simple_message("Command cancelled.")
                    return None
                if user_input in valid_options:
                    return user_input
                self.display_simple_message(f"Invalid input, try: {', '.join(valid_options)}", 1)
            except KeyboardInterrupt:
                print(f"Do you want to exit? (yes/no):")
                confirm = input(">>> ").strip().lower()
                if confirm == 'yes':
                    self.display_simple_message("Goodbye!", 1)
                    exit()
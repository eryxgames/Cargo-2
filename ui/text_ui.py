import os
import shutil
import time
import re

class TextUI(object):
    def __init__(self, theme_manager=None):
        self.theme_manager = theme_manager
        self.default_theme = {
            "background_color": None,
            "text_color": "37",
            "header_color": "33",
            "success_color": "32",
            "error_color": "31",
            "warning_color": "33",
            "box_style": "single",
            "font_face": "default",
            "header_style": "bold",
            "text_style": "normal",
            "border_color": "37"
        }
        self.available_themes = []
        if theme_manager:
            self.available_themes = list(theme_manager.themes.keys())
        self.current_theme_index = 0
        self.rich_installed = False
        try:
            import rich
            self.rich_installed = True
        except ImportError:
            pass

    def get_current_theme(self):
        return self.theme_manager.current_theme if self.theme_manager else self.default_theme
    
    def format_text(self, text, color=None, style=None):
        """Formats a string with optional style and color from theme."""
        theme = self.get_current_theme()
        if not color:
            color = theme.get("text_color", "37") #default color
        if not style:
           style = theme.get("text_style", "normal") #default style
        
        if style == 'bold' and self.rich_installed:
             return f'\033[{color}m\033[1m{text}\033[0m'
        elif style == 'italic' and self.rich_installed:
            return f'\033[{color}m\033[3m{text}\033[0m'
        elif style == 'underline' and self.rich_installed:
            return f'\033[{color}m\033[4m{text}\033[0m'
        else:
            return f'\033[{color}m{text}\033[0m'

    def get_text_length(self, text):
        """Get length of the text, excluding control chars"""
        return len(re.sub(r'\033\[\d+m', '', text))

    def create_simple_box(self, content, style='single'):
        term_width = shutil.get_terminal_size().columns
        width = term_width - 4  # Adjust for padding
        theme = self.get_current_theme()
        border_color = theme.get("border_color", "37")  # Get border color from theme
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
            lines.append(self.format_text(f"{chars['tl']}{chars['h'] * width}{chars['tr']}", color=border_color))

        for row in content:
            wrapped_row = self.word_wrap(row, width - 2)
            for line in wrapped_row:
                lines.append(f"{self.format_text(chars['v'], color=border_color)} {self.format_text(line, theme.get('text_color', '37')):<{width-2}} {self.format_text(chars['v'], color=border_color)}")

        if style != 'none':
            lines.append(self.format_text(f"{chars['bl']}{chars['h'] * width}{chars['br']}", color=border_color))
        return '\n'.join(lines)
    
    def create_box(self, content, style='single', text_color=None, header_color=None, text_style=None, header_style=None, double_border=False, border_color=None):
        """Create a box that expands to terminal width with proportionally sized columns."""
        # Get terminal width and account for borders and spacing
        term_width = shutil.get_terminal_size().columns
        usable_width = term_width - 4  # Account for borders and minimum spacing
        
        # Get theme data
        theme = self.get_current_theme()
        
        if not text_color:
            text_color = theme.get("text_color", "37")
        if not header_color:
            header_color = theme.get("header_color", "33")
        if not text_style:
            text_style = theme.get("text_style", "normal")
        if not header_style:
            header_style = theme.get("header_style", "bold")
        if not border_color:
            border_color = theme.get("border_color", "37")

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
                    max_lengths[i] = max(max_lengths[i], self.get_text_length(str(cell)))
        
        # Calculate available space for content
        separator_space = 3  # Space for " │ " between columns
        total_separator_width = separator_space * (num_cols - 1)
        padding_width = 2  # Space for padding around content " x "
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
                proportion = max_lengths[i] / total_content_length if total_content_length > 0 else 1/num_cols
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
            border_line = f"{chars['tl']}{chars['h'] * horizontal_width}{chars['tr']}"
            if double_border:
                lines.append(self.format_text(border_line, color=border_color))
                lines.append(self.format_text(f"{chars['tl']}{chars['h'] * horizontal_width}{chars['tr']}", color=border_color))
            else:
                lines.append(self.format_text(border_line, color=border_color))

        # Content rows
        for row in content:
            padded_row = row + [''] * (num_cols - len(row))
            formatted_cells = []
            for i, cell in enumerate(padded_row):
                cell_str = str(cell)
                if self.get_text_length(cell_str) > col_widths[i]:
                    cell_str = cell_str[:col_widths[i]-3] + "..."
                formatted_cells.append(f"{self.format_text(cell_str, text_color, text_style):<{col_widths[i]}}")
            
            separator_string = (' ' + self.format_text(chars['sep'], color=border_color) + ' ').join(['' for _ in range(num_cols - 1)])
            row_str = f"{self.format_text(chars['v'], color=border_color)}{separator_string.join(formatted_cells)}{self.format_text(chars['v'], color=border_color)}"
            lines.append(row_str)
        
        # Bottom border
        if style != 'none':
            border_line = f"{chars['bl']}{chars['h'] * horizontal_width}{chars['br']}"
            if double_border:
                lines.append(self.format_text(border_line, color=border_color))
                lines.append(self.format_text(f"{chars['bl']}{chars['h'] * horizontal_width}{chars['br']}", color=border_color))
            else:
                lines.append(self.format_text(border_line, color=border_color))
        
        return '\n'.join(lines)

    def create_character_box(self, character_content, style='round', text_color=None, header_color=None, text_style=None, header_style=None):
        """Create a character display box optimized for different terminal widths"""
        try:
            term_width = os.get_terminal_size().columns
        except OSError:
            term_width = 80  # Default width
                
        if term_width < 60:
            content_width = term_width - 4
            compact_mode = True
        else:
            content_width = min(80, term_width - 4)
            compact_mode = False
            
        theme = self.get_current_theme()    
        
        if not text_color:
            text_color = theme.get("text_color", "37")
        if not header_color:
            header_color = theme.get("header_color", "33")
        if not text_style:
            text_style = theme.get("text_style", "normal")
        if not header_style:
            header_style = theme.get("header_style", "bold")
        border_color = theme.get("border_color", "37")  # Get border color from theme

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
            lines.append(self.format_text(f"{chars['tl']}{chars['h'] * content_width}{chars['tr']}", color=border_color))
            
        if 'title' in character_content:
            wrapped_title = self.word_wrap(character_content['title'], content_width - 2)
            for line in wrapped_title:
                lines.append(f"{self.format_text(chars['v'], color=border_color)} {self.format_text(line, header_color, header_style):<{content_width-2}} {self.format_text(chars['v'], color=border_color)}")
            if style != 'none':
                lines.append(f"{self.format_text(chars['v'], color=border_color)}{chars['h'] * content_width}{self.format_text(chars['v'], color=border_color)}")
            
        for section in ['introduction', 'description', 'demands', 'options']:
            if section in character_content:
                if not compact_mode:
                    lines.append(f"{self.format_text(chars['v'], color=border_color)}{' ' * content_width}{self.format_text(chars['v'], color=border_color)}")
                    
                wrapped_content = self.word_wrap(character_content[section], content_width - 2)
                for line in wrapped_content:
                    lines.append(f"{self.format_text(chars['v'], color=border_color)} {self.format_text(line, text_color, text_style):<{content_width-2}} {self.format_text(chars['v'], color=border_color)}")
                            
                    if style != 'none':
                        lines.append(self.format_text(f"{chars['bl']}{chars['h'] * content_width}{chars['br']}", color=border_color))
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

    def display_simple_message(self, message, pause=1, style='round', color=None, text_style=None):
        if isinstance(message, list):
            box_content = message
        else:
            box_content = [message]
        theme = self.get_current_theme()
        box = self.create_simple_box(box_content, style)
        
        # Apply the color and style
        if color or theme.get("text_color") or text_style or theme.get("text_style"):
            formatted_box = self.format_text(box, color if color else theme.get("text_color"), text_style if text_style else theme.get("text_style"))
            print(formatted_box)
        else:
            print(box)
        if pause > 0:
            time.sleep(pause)
            
    def display_message(self, message, pause=2, style='round', color=None, text_style=None, header_style=None):
        if isinstance(message, list):
            box_content = message
        else:
            box_content = [message]
        theme = self.get_current_theme()
        box = self.create_box(box_content, style, color, text_style=text_style, header_style=header_style)
        
        # Apply color if specified
        if color or theme.get("text_color") or text_style or theme.get("text_style"):
            formatted_box = self.format_text(box, color if color else theme.get("text_color", "37"), text_style if text_style else theme.get("text_style"))
            print(formatted_box)
        else:
            print(box)
        if pause > 0:
            time.sleep(pause)
            
    def fast_message(self, message, pause=0.5, style='round', color=None, clear_screen=True):
        if isinstance(message, list):
            box_content = message
        else:
            box_content = [message]
        theme = self.get_current_theme()
        box = self.create_simple_box(box_content, style)
        if color:
            box = f"\033[{color}m{box}\033[0m"
        elif theme.get("text_color"):
            box = f"\033[{theme.get('text_color')}m{box}\033[0m"
        print(box)
        if pause > 0:
            time.sleep(pause)
        if clear_screen:
            os.system('clear' if os.name == 'posix' else 'cls')
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
        """Create a simple box with proper width calculations for both single and multi-line content."""
        term_width = shutil.get_terminal_size().columns
        theme = self.get_current_theme()
        border_color = theme.get("border_color", "37")

        # Convert single string to list and handle empty content
        if isinstance(content, str):
            content = [content]
        if not content:
            content = [""]
        
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

        # Calculate maximum content width needed
        max_content_width = 0
        wrapped_content = []
        
        for line in content:
            if line is None:
                line = ""
            wrapped_lines = self.word_wrap(str(line), term_width - 4)  # -4 for borders and minimum padding
            if wrapped_lines:
                wrapped_content.extend(wrapped_lines)
                line_lengths = [self.get_text_length(wl) for wl in wrapped_lines]
                if line_lengths:
                    max_content_width = max(max_content_width, max(line_lengths))
            else:
                wrapped_content.append("")
                
        # If we still have no content width, set a minimum
        if max_content_width == 0:
            max_content_width = 2

        # Add padding to content width
        border_space = 1  # Space between border and content
        content_width = max_content_width + (2 * border_space)  # Add border spaces
        box_width = content_width + 2  # Add 2 for border characters

        # Ensure box width doesn't exceed terminal width
        box_width = min(box_width, term_width)
        content_width = box_width - 2

        lines = []
        if style != 'none':
            # Top border
            lines.append(self.format_text(
                f"{chars['tl']}{chars['h'] * content_width}{chars['tr']}", 
                color=border_color
            ))

        # Content
        for line in wrapped_content:
            # Format the line with proper padding and alignment
            formatted_line = self.format_text(line, theme.get('text_color', '37'))
            padding_right = content_width - border_space - self.get_text_length(line)
            lines.append(
                f"{self.format_text(chars['v'], color=border_color)}"
                f"{' ' * border_space}"
                f"{formatted_line}{' ' * padding_right}"
                f"{self.format_text(chars['v'], color=border_color)}"
            )

        if style != 'none':
            # Bottom border
            lines.append(self.format_text(
                f"{chars['bl']}{chars['h'] * content_width}{chars['br']}", 
                color=border_color
            ))

        return '\n'.join(lines)

    def create_box(self, content, style='single', text_color=None, header_color=None, text_style=None, header_style=None, double_border=False, border_color=None):
        """Create a box with multiple columns and proper width calculations."""
        term_width = shutil.get_terminal_size().columns
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

        # Calculate number of columns and column sizes
        num_cols = max(len(row) for row in content)
        col_sizes = [[] for _ in range(num_cols)]
        
        # Collect all content for each column
        for row in content:
            for i, cell in enumerate(row[:num_cols]):
                col_sizes[i].extend(self.word_wrap(str(cell), term_width // num_cols - 4))
        
        # Calculate maximum width needed for each column
        max_col_widths = [max(self.get_text_length(line) for line in col) if col else 0 for col in col_sizes]
        
        # Calculate spacing and final column widths
        separator_width = 3  # Space for " │ "
        available_width = term_width - (num_cols + 1) * separator_width
        
        # Distribute available width proportionally
        total_content_width = sum(max_col_widths)
        col_widths = []
        remaining_width = available_width
        
        for i, max_width in enumerate(max_col_widths):
            if i == len(max_col_widths) - 1:
                width = remaining_width
            else:
                proportion = max_width / total_content_width if total_content_width > 0 else 1/num_cols
                width = max(3, min(int(available_width * proportion), max_width + 2))
                remaining_width -= width
            col_widths.append(width)

        # Calculate total box width - corrected for width with adding - 2
        horizontal_width = sum(col_widths) + (num_cols + 1) * separator_width - 2

        lines = []
        if style != 'none':
            # Top border
            border_line = (
                f"{chars['tl']}"
                f"{chars['h'] * (horizontal_width - 2)}"
                f"{chars['tr']}"
            )
            if double_border:
                lines.append(self.format_text(border_line, color=border_color))
                lines.append(self.format_text(border_line, color=border_color))
            else:
                lines.append(self.format_text(border_line, color=border_color))

        # Process content row by row
        for row in content:
            # Split each cell content into lines
            row_lines = []
            max_lines = 1
            for i, cell in enumerate(row[:num_cols]):
                wrapped = self.word_wrap(str(cell), col_widths[i])
                row_lines.append(wrapped)
                max_lines = max(max_lines, len(wrapped))
            
            # Pad cells with empty lines if needed
            for lines_list in row_lines:
                while len(lines_list) < max_lines:
                    lines_list.append('')
            
            # Create each line of the row
            for line_idx in range(max_lines):
                line_parts = []
                for col_idx, lines_list in enumerate(row_lines):
                    cell_content = lines_list[line_idx] if line_idx < len(lines_list) else ''
                    formatted_cell = self.format_text(cell_content, text_color, text_style)
                    padding = col_widths[col_idx] - self.get_text_length(cell_content)
                    line_parts.append(f"{formatted_cell}{' ' * padding}")
                
                separator = self.format_text(f" {chars['sep']} ", color=border_color)
                line = f"{self.format_text(chars['v'], color=border_color)} {separator.join(line_parts)} {self.format_text(chars['v'], color=border_color)}"
                lines.append(line)

        if style != 'none':
            # Bottom border
            border_line = (
                f"{chars['bl']}"
                f"{chars['h'] * (horizontal_width - 2)}" #removed (horizontal_width - 2) because of calculation of width
                f"{chars['br']}"
            )
            if double_border:
                lines.append(self.format_text(border_line, color=border_color))
                lines.append(self.format_text(border_line, color=border_color))
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
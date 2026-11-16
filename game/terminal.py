"""The terminal: its width, narrow layouts, wrapping, and the box every screen is drawn in."""
import os
import re
import shutil
import sys
import unicodedata

# Define your logo data ONCE, at the module level:
logo_data = [
    "╔═══════ C Δ R G Ω ][ ══════╗",
    "║     Space Trading Saga    ║",
    "╚═══════════════════════════╝"
]

# =============================================================================
# Terminal kit: width, wrapping and the one box renderer.
# Everything the game draws goes through here, so a 36-column phone screen in
# Termux and a wide desktop terminal get the same boxes, laid out to fit.
# =============================================================================

MIN_COLUMNS = 24        # below this nothing sensible fits; lay out as if this wide
NARROW_COLUMNS = 60     # below this the layout switches to the phone arrangement
RULE = object()         # a row that draws a horizontal rule inside a box

_ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")

BOX_STYLES = {
    'single': {'tl': '┌', 'tr': '┐', 'bl': '└', 'br': '┘', 'h': '─', 'v': '│', 'sep': '│', 'l': '├', 'r': '┤'},
    'double': {'tl': '╔', 'tr': '╗', 'bl': '╚', 'br': '╝', 'h': '═', 'v': '║', 'sep': '║', 'l': '╟', 'r': '╢', 'rule': '─'},
    'round':  {'tl': '╭', 'tr': '╮', 'bl': '╰', 'br': '╯', 'h': '─', 'v': '│', 'sep': '│', 'l': '├', 'r': '┤'},
    'ascii':  {'tl': '+', 'tr': '+', 'bl': '+', 'br': '+', 'h': '-', 'v': '|', 'sep': '|', 'l': '+', 'r': '+'},
}


def safe_output():
    """Characters this terminal cannot show print as '?' instead of stopping the game
    (old Windows code pages, output sent to a file or a pipe)."""
    for stream in (sys.stdout, sys.stderr):
        try:
            if "utf" not in (getattr(stream, "encoding", None) or "utf").lower():
                stream.reconfigure(errors="replace")
        except (AttributeError, ValueError, OSError):
            pass


def plain_terminal():
    """True when the terminal cannot be trusted with box-drawing characters."""
    if os.environ.get("CARGO_ASCII"):
        return True
    encoding = (getattr(sys.stdout, "encoding", None) or "").lower()
    return bool(encoding) and "utf" not in encoding


def terminal_columns():
    """Width of the terminal in columns; 80 when it cannot be known."""
    try:
        columns = shutil.get_terminal_size((80, 24)).columns
    except (OSError, ValueError):
        columns = 80
    return max(MIN_COLUMNS, columns or 80)


def is_narrow():
    return terminal_columns() < NARROW_COLUMNS


def box_inner_width(cap=None):
    """Columns between the two borders of a full-width box."""
    columns = terminal_columns()
    # wide terminals keep the classic one-column margin; phones use every column
    inner = columns - 4 if columns >= NARROW_COLUMNS else columns - 3
    if cap:
        inner = min(inner, cap)
    return max(MIN_COLUMNS - 3, inner)


def visible_len(text):
    """Printed width of a string: colour codes count 0, wide characters 2."""
    width = 0
    for ch in _ANSI_RE.sub("", str(text)):
        if unicodedata.combining(ch):
            continue
        width += 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
    return width


def pad_to(text, width):
    text = str(text)
    return text + " " * max(0, width - visible_len(text))


def wrap_text(text, width):
    """Word-wrap to `width` columns; words longer than a line are split. Leading spaces
    are kept, on every line the text wraps to (an indented line stays indented)."""
    text = str(text)
    indent = len(text) - len(text.lstrip(" "))
    if indent and indent < int(width) // 2:
        return [" " * indent + line for line in wrap_text(text.lstrip(" "), int(width) - indent)]
    width = max(1, int(width))
    lines, current, current_len = [], [], 0
    for word in str(text).split():
        while visible_len(word) > width:           # a word wider than the box
            if current:
                lines.append(" ".join(current))
                current, current_len = [], 0
            lines.append(word[:width])
            word = word[width:]
        word_len = visible_len(word)
        if current and current_len + 1 + word_len > width:
            lines.append(" ".join(current))
            current, current_len = [word], word_len
        elif current:
            current.append(word)
            current_len += 1 + word_len
        else:
            current, current_len = [word], word_len
    if current:
        lines.append(" ".join(current))
    return lines


def flow_cells(cells, width, gap="  "):
    """Lay short cells out left to right, breaking only between cells."""
    lines, current = [], ""
    for cell in cells:
        cell = str(cell)
        if not cell.strip():
            continue
        if visible_len(cell) > width:
            if current:
                lines.append(current)
                current = ""
            lines.extend(wrap_text(cell, width))
        elif current and visible_len(current) + len(gap) + visible_len(cell) > width:
            lines.append(current)
            current = cell
        else:
            current = current + gap + cell if current else cell
    if current:
        lines.append(current)
    return lines


def render_box(rows, style='single', inner=None, narrow='auto'):
    """Draw a box around `rows` and return it as one string.

    rows    a list of rows; a row is a list of cells (one cell = plain text that is
            word-wrapped, several cells = table columns) or RULE for a rule.
    style   'single', 'double' or 'round'.
    inner   columns between the borders (default: the terminal width).
    narrow  what a table does when its columns do not fit:
            'auto'  wrap the widest column; if even that is too tight, put each
                    row on its own lines (first cell, then the rest indented)
            'flow'  for side-by-side panels: each column becomes a block whose
                    cells flow left to right, blocks separated by a rule
            'stack' for side-by-side lists: each column becomes a block with
                    one cell per line, blocks separated by a rule
    Nothing is ever cut off and no line is wider than the box.
    """
    chars = BOX_STYLES['ascii'] if plain_terminal() else BOX_STYLES.get(style, BOX_STYLES['single'])
    if inner is None:
        inner = box_inner_width()
    text_width = max(1, inner - 2)
    body = []          # each entry: a text line, or RULE

    table = [r for r in rows if r is not RULE]
    num_cols = max([len(r) for r in table] or [1])

    if num_cols <= 1:
        for row in rows:
            if row is RULE:
                body.append(RULE)
                continue
            cell = row[0] if isinstance(row, (list, tuple)) and row else (row if isinstance(row, str) else "")
            lines = wrap_text(cell, text_width)
            if lines:
                body.extend(lines)
            elif body and body[-1] not in ("", RULE):
                body.append("")             # an empty row is a blank line (one at most)
        while body and body[-1] == "":
            body.pop()
    else:
        natural = [0] * num_cols
        for row in table:
            for i, cell in enumerate(row):
                natural[i] = max(natural[i], visible_len(cell))
        gaps = 3 * (num_cols - 1)
        sep = " " + chars['sep'] + " "

        def table_lines(widths):
            for row in rows:
                if row is RULE:
                    body.append(RULE)
                    continue
                cells = [str(c) for c in row] + [''] * (num_cols - len(row))
                wrapped = [wrap_text(c, widths[i]) or [''] for i, c in enumerate(cells)]
                for k in range(max(len(w) for w in wrapped)):
                    body.append(sep.join(
                        pad_to(w[k] if k < len(w) else '', widths[i]) for i, w in enumerate(wrapped)))

        if sum(natural) + gaps <= text_width:
            # everything fits: natural widths with a little air, last column takes the rest
            widths = list(natural)
            spare = text_width - gaps - sum(natural)
            for i in range(num_cols - 1):
                extra = min(2, spare)
                widths[i] += extra
                spare -= extra
            widths[-1] += spare
            table_lines(widths)
        elif narrow in ('flow', 'stack'):
            for i in range(num_cols):
                column = [str(row[i]) for row in table if i < len(row)]
                while column and not column[-1].strip():
                    column.pop()
                if not column:
                    continue
                if body:
                    body.append(RULE)
                if narrow == 'flow':
                    body.extend(flow_cells(column, text_width))
                else:
                    for cell in column:
                        indent = len(cell) - len(cell.lstrip(' '))
                        for line in wrap_text(cell, text_width - indent) or ['']:
                            body.append(' ' * indent + line)
        else:
            widest = max(range(num_cols), key=lambda i: natural[i])
            room = text_width - gaps - (sum(natural) - natural[widest])
            if room >= min(natural[widest], 14):
                widths = list(natural)
                widths[widest] = room
                table_lines(widths)
            else:
                for row in rows:
                    if row is RULE:
                        body.append(RULE)
                        continue
                    cells = [str(c) for c in row if str(c).strip()]
                    if not cells:
                        body.append('')
                        continue
                    body.extend(wrap_text(cells[0], text_width))
                    if len(cells) > 1:
                        for line in wrap_text(" · ".join(cells[1:]), text_width - 2):
                            body.append("  " + line)

    rule_char = chars.get('rule', chars['h'])
    lines = [chars['tl'] + chars['h'] * inner + chars['tr']]
    for line in body:
        if line is RULE:
            lines.append(chars['l'] + rule_char * inner + chars['r'])
        else:
            lines.append(chars['v'] + " " + pad_to(line, text_width) + " " + chars['v'])
    lines.append(chars['bl'] + chars['h'] * inner + chars['br'])
    return "\n".join(lines)


def say(text=""):
    """Print plain text, wrapped to the terminal."""
    for line in wrap_text(text, terminal_columns() - 1) or [""]:
        print(line)


def display_logo(logo, centered=True):
    """Displays the logo, optionally centered."""
    terminal_width = terminal_columns()
    for line in logo:
        if plain_terminal():
            line = line.translate(str.maketrans("╔╗╚╝═║", "++++-|"))
        if centered:
            padding = max(0, (terminal_width - visible_len(line)) // 2)
            print(" " * padding + line)
        else:
            print(line)  # Just print without centering

def print_centered_text(text):
    print(text.center(terminal_columns() - 1))

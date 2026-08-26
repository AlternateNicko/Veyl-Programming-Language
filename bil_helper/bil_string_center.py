import unicodedata
import textwrap

def get_visual_width(s: str) -> int:
    """Calculates the visual display width of a string, accounting for wide Unicode characters."""
    width = 0
    for char in s:
        # 'W' (Wide) and 'F' (Fullwidth) characters take 2 display columns
        if unicodedata.east_asian_width(char) in ('W', 'F'):
            width += 2
        else:
            width += 1
    return width

def center_line(line: str, width: int, fill: str = " ", overflow: str = "truncate", unicode_width: bool = True) -> str:
    """Centers a single line of text according to width and overflow settings."""
    calc_len = get_visual_width if unicode_width else len
    current_len = calc_len(line)

    # Handle overflow conditions
    if current_len > width:
        if overflow == "error":
            raise ValueError(f"String length ({current_len}) exceeds specified width ({width}).")
        elif overflow == "ignore":
            return line
        elif overflow == "truncate":
            # Trim character by character to respect visual boundaries
            trimmed = ""
            for char in line:
                if calc_len(trimmed + char) > width:
                    break
                trimmed += char
            line = trimmed
            current_len = calc_len(line)
        elif overflow == "wrap":
            # Handled at higher level for multiline, fallback to ignore if hit directly
            return line
        else:
            raise ValueError(f"Invalid overflow option: '{overflow}'")

    padding_needed = width - current_len
    left_pad = padding_needed // 2
    right_pad = padding_needed - left_pad

    # Account for visual width of the fill character
    fill_len = calc_len(fill) if unicode_width else len(fill)
    if fill_len > 1:
        fill_left = (fill * (left_pad // fill_len + 1))[:left_pad]
        fill_right = (fill * (right_pad // fill_len + 1))[:right_pad]
        return f"{fill_left}{line}{fill_right}"

    return f"{fill * left_pad}{line}{fill * right_pad}"

def center(
    text: str,
    width: int,
    fill: str = " ",
    multiline: bool = True,
    overflow: str = "truncate",  # Options: 'truncate', 'error', 'ignore', 'wrap'
    unicode_width: bool = True
) -> str:
    """Centers text within a given visual width supporting multiline and custom overflow behaviors."""
    if not multiline:
        # Replace newlines with spaces if multiline processing is disabled
        text = text.replace("\r\n", " ").replace("\n", " ")
        lines = [text]
    elif overflow == "wrap":
        # Wrap long lines before centering each segment
        lines = []
        for line in text.splitlines():
            wrapped = textwrap.wrap(line, width=width) or [""]
            lines.extend(wrapped)
    else:
        lines = text.splitlines()

    centered_lines = [
        center_line(line, width, fill=fill, overflow=overflow, unicode_width=unicode_width)
        for line in lines
    ]

    return "\n".join(centered_lines)
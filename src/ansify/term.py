import os

def get_terminal_color_depth():
    # Truecolor check
    if os.environ.get("COLORTERM", "").lower() in ("truecolor", "24bit"):
        return 24
    term = os.environ.get("TERM", "")
    if "256color" in term:
        return 8  # 8 bits per channel, but usually called "256 color"
    if any(x in term for x in ("xterm", "vt100", "color", "ansi", "cygwin", "linux")):
        return 4  # 16 color
    return 1  # monochrome/unknown

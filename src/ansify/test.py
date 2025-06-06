def rgb_to_ansi256(r:int, g:int, b:int) -> int:
    # Standard xterm 256-color approximation (see: https://stackoverflow.com/a/33206814)
    # Grayscale range
    if r == g == b:
        if r < 8: return 16
        if r > 248: return 231
        return round(((r - 8) / 247) * 24) + 232
    # Color cube
    r_val = int(round(r / 255 * 5))
    g_val = int(round(g / 255 * 5))
    b_val = int(round(b / 255 * 5))
    return 16 + 36 * r_val + 6 * g_val + b_val

bg = rgb_to_ansi256(0, 0, 0)
fg = rgb_to_ansi256(0, 0, 255)

lines = [
  f"\x1b[38;5;{fg};49m\u2580\u2588\u2591\u2592\u2593\u2584"
]

for line in lines:
    print(line, end="")

print("\x1b[0m")

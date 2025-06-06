import numpy as np

from PIL import Image

from .term import get_terminal_color_depth

def resize_image(img, max_height):
    w, h = img.size
    if h <= max_height:
        return img  # No resize needed
    scale = max_height / h
    new_size = (max(1, int(w * scale)), max(1, int(h * scale)))
    return img.resize(new_size, Image.LANCZOS)  # LANCZOS = high-quality downsampling

def rgb_to_ansi256(r, g, b):
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

def image_to_ansi8(img, bg_color, brightness) -> list[str]:
    img = img.convert("RGBA")
    w, h = img.size
    lines = []
    for y in range(0, h, 2):
        line = ""
        for x in range(w):
            def blend(px):
                r, g, b, a = px
                r_out = min(int((r * a + bg_color[0] * (255 - a)) / 255 * brightness), 255)
                g_out = min(int((g * a + bg_color[1] * (255 - a)) / 255 * brightness), 255)
                b_out = min(int((b * a + bg_color[2] * (255 - a)) / 255 * brightness), 255)
                return (r_out, g_out, b_out)
            top = img.getpixel((x, y))
            bot = img.getpixel((x, y+1)) if y+1 < h else (bg_color[0], bg_color[1], bg_color[2], 255)
            fg = blend(top)
            bg = blend(bot)
            fg_ansi = rgb_to_ansi256(*fg)
            bg_ansi = rgb_to_ansi256(*bg)
            line += f"\x1b[38;5;{fg_ansi};48;5;{bg_ansi}m▀"
        line += "\x1b[0m"
        lines.append(line)
    return lines

def image_to_ansi24(img, bg_color, brightness) -> list[str]:
    # Assume input is RGBA or RGB
    img = img.convert("RGBA")
    w, h = img.size
    lines = []
    for y in range(0, h, 2):
        line = ""
        for x in range(w):
            def blend(px):
                r, g, b, a = px
                # Premultiply with alpha over bg_color
                r_out = min(int((r * a + bg_color[0] * (255 - a)) / 255 * brightness), 255)
                g_out = min(int((g * a + bg_color[1] * (255 - a)) / 255 * brightness), 255)
                b_out = min(int((b * a + bg_color[2] * (255 - a)) / 255 * brightness), 255)
                return (r_out, g_out, b_out)

            top = img.getpixel((x, y))
            bot = img.getpixel((x, y+1)) if y+1 < h else (bg_color[0], bg_color[1], bg_color[2], 255)
            fg = blend(top)
            bg = blend(bot)
            line += f"\x1b[38;2;{fg[0]};{fg[1]};{fg[2]};48;2;{bg[0]};{bg[1]};{bg[2]}m▀"
        line += "\x1b[0m"
        lines.append(line)
    return lines

def img_to_ansi(img, bg_color=(0, 0, 0), brightness=1.0):
    """
    Converts an image to ANSI escape codes.
    img: PIL.Image object.
    bg_color: (R,G,B) tuple for the background color.
    brightness: float, scaling factor for brightness.
    Returns a list of strings representing the ANSI image.
    """
    bits = get_terminal_color_depth()

    if img.mode not in ("RGBA", "RGB"):
        img = img.convert("RGBA")
    if bits == 8:
        return image_to_ansi8(img, bg_color, brightness)
    elif bits == 24:
        return image_to_ansi24(img, bg_color, brightness)
    else:
        raise ValueError(f"Unsupported color depth: {bits}. Use 8 or 24 bits.")

def crop_image(img, crop_top=0, crop_right=0, crop_bottom=0, crop_left=0):
    """
    Crops the image by the specified number of pixels on each side.
    Returns a new PIL.Image object.
    """
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    w, h = img.size
    new_w = max(0, w - crop_left - crop_right)
    new_h = max(0, h - crop_top - crop_bottom)
    left = crop_left
    top = crop_top
    return img.crop((left, top, left + new_w, top + new_h))

def pad_image(img, pad_top=0, pad_right=0, pad_bottom=0, pad_left=0, bg_color=(0,0,0,0)):
    """
    Pads the image with the specified number of pixels on each side.
    bg_color: (R,G,B) or (R,G,B,A) tuple for the background color.
    """
    # Ensure RGBA for alpha safety
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    w, h = img.size
    new_w = w + pad_left + pad_right
    new_h = h + pad_top + pad_bottom
    # Create RGBA output, always
    new_img = Image.new("RGBA", (new_w, new_h), bg_color)
    # Paste with mask for alpha
    new_img.paste(img, (pad_left, pad_top), mask=img)
    return new_img

import sys
import re

def split_lines(ansi_img):
    """Helper: splits input into lines."""
    if isinstance(ansi_img, str):
        return ansi_img.splitlines()
    return ansi_img

def pad_lines(lines, target_len):
    """Pad lines to a given length with empty lines."""
    return lines + [""] * (target_len - len(lines))

def join_ansi_images_side_by_side(ansi_img1, ansi_img2, sep=""):
    """
    Joins two ANSI images side by side, line by line.
    Inputs can be lists of strings or multi-line strings.
    """
    lines1 = split_lines(ansi_img1)
    lines2 = split_lines(ansi_img2)
    max_lines = max(len(lines1), len(lines2))
    lines1 = pad_lines(lines1, max_lines)
    lines2 = pad_lines(lines2, max_lines)
    # Optionally, add separator (e.g., sep="  ") between images
    joined = [
        f"{l1}{sep}{l2}" for l1, l2 in zip(lines1, lines2)
    ]
    return "\n".join(joined)

def composite_background(img, bg_color):
    """
    Composites img (any mode, ideally RGBA or LA) over a solid bg_color.
    bg_color: (R,G,B) tuple.
    Returns: RGB PIL.Image
    """
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    arr = np.array(img).astype(np.float32)
    fg_rgb = arr[..., :3]
    alpha = arr[..., 3:4] / 255  # Normalize to 0..1

    # Broadcast bg_color to shape
    bg = np.array(bg_color, dtype=np.float32).reshape(1,1,3)
    out_rgb = fg_rgb * alpha + bg * (1 - alpha)
    out_rgb = np.clip(out_rgb, 0, 255).astype(np.uint8)
    return Image.fromarray(out_rgb, "RGB")

class AnsiImageRenderer:
    """
    Class to render ANSI images.
    This class can be extended to add more rendering features.
    """
    def __init__(self, max_width, max_height, bg_color, brightness):
        self.max_width = max_width
        self.max_height = max_height
        self.bg_color = bg_color
        self.brightness = brightness

    def render(self, img: Image.Image) -> str:
        img = composite_background(img, bg_color=self.bg_color)
        img = resize_image(img, max_height=self.max_height)
        ansi_art = img_to_ansi(img, bg_color=self.bg_color, brightness=self.brightness)
        return ansi_art

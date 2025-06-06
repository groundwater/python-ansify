import numpy as np

from matplotlib.font_manager import FontProperties, findfont
from PIL import Image, ImageDraw, ImageFont
from typing import List, Literal, Callable

from .term import get_terminal_color_depth
from .img import AnsiImageRenderer, img_to_ansi

# Colors: choose ANSI256 codes for ON/OFF pixels
FG_ON = 12   # Bright white (ANSI 15)
FG_OFF = 16  # Black (ANSI 16)
THRESHOLD = 128  # Midpoint for 8-bit (0=black, 255=white)

def adjust_image_levels(img: Image.Image, black=0, white=255) -> Image.Image:
    """Linearly stretch RGBA so black→0, white→255 for R,G,B,A."""
    img = img.convert("RGBA")
    arr = np.array(img).astype(np.float32)
    arr = (arr - black) / (white - black) * 255
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")

def colorize_image(img: Image.Image, fg_color=(255, 255, 255), bg_color=(0, 0, 0)) -> Image.Image:
    img = img.convert("RGBA")
    arr = np.array(img).astype(np.float32)
    alpha = arr[..., 3:4] / 255  # shape (H, W, 1)

    fg = np.array(fg_color, dtype=np.float32).reshape(1, 1, 3)
    bg = np.array(bg_color, dtype=np.float32).reshape(1, 1, 3)

    out_rgb = fg * alpha + bg * (1 - alpha)
    out_alpha = arr[..., 3:4]  # preserve alpha

    out = np.concatenate([out_rgb, out_alpha], axis=2)
    out = np.clip(out, 0, 255).astype(np.uint8)
    return Image.fromarray(out, "RGBA")

def text_to_image(text, font_path, font_size, color=(255,255,255), bg=(0,0,0,0)):
    font = ImageFont.truetype(font_path, font_size)
    # Calculate size needed
    dummy_img = Image.new("RGBA", (1,1))
    draw = ImageDraw.Draw(dummy_img)
    bbox = draw.textbbox((0,0), text, font=font)
    width, height = bbox[2] - bbox[0], bbox[3] - bbox[1]
    # Create final image
    img = Image.new("RGBA", (width, height), bg)
    draw = ImageDraw.Draw(img)
    draw.text((-bbox[0], -bbox[1]), text, font=font, fill=color)
    return img

def font_from_name(font_name):
    prop = FontProperties(family=font_name)
    try:
        return findfont(prop, fallback_to_default=False)  # raises error if not found
    except ValueError:
        raise ValueError(f"Font '{font_name}' not found")

def list_fonts() -> List[str]:
    """List all available fonts."""
    from matplotlib.font_manager import fontManager
    return [f.name for f in fontManager.ttflist]

def text_to_ansi(line:str, font:str, size:int, background:tuple[int, int, int], foreground:tuple[int, int, int]) -> str:
    # Adjust spacing
    black_level = 0
    white_level = 200
    brightness=1.0

    font_path = font_from_name(font)
    img = text_to_image(line, font_path, size)
    img = adjust_image_levels(img, black_level, white_level)
    img = colorize_image(img, fg_color=foreground, bg_color=background)

    ansi_lines: list[str] = img_to_ansi(img, bg_color=background, brightness=brightness)
    return ("\n".join(ansi_lines))

import qrcode
from PIL import Image
from argparse import ArgumentParser
from .img import AnsiImageRenderer, img_to_ansi, resize_image, pad_image, crop_image, composite_background
from .font import list_fonts, text_to_ansi, colorize_image
from .comp import combine_ansi_horizontally
from .term import get_terminal_color_depth

def color_to_color(color: str) -> tuple[int, int, int]:
    """Convert a color string 'R,G,B' to a tuple of integers."""
    if color == "black":
        return (0, 0, 0)
    if color == "white":
        return (255, 255, 255)
    if color == "red":
        return (255, 0, 0)
    if color == "green":
        return (0, 255, 0)
    if color == "blue":
        return (0, 0, 255)
    if color == "yellow":
        return (255, 255, 0)
    if color == "cyan":
        return (0, 255, 255)
    if color == "magenta":
        return (255, 0, 255)
    if color == "gray":
        return (128, 128, 128)
    if color == "darkgray":
        return (64, 64, 64)
    if color == "lightgray":
        return (192, 192, 192)
    try:
        return tuple(map(int, color.split(',')))
    except ValueError:
        raise ValueError(f"Invalid color format: {color}. Use 'R,G,B' format.")

# Usage: ansify [GLOBAL] COMMAND [ARGS]
# Commands:
#     img IMG_FILE [OPTIONS]  Process an image file
#         --bg-color R,G,B      Background color (default: 0,0,0)
#         --brightness VALUE     Brightness adjustment (default: 1.0)
#     font FONT_FILE [OPTIONS] Process a font file
def _main():
    parser = ArgumentParser(description="Render ANSI Graphics")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # img command
    img_parser = subparsers.add_parser("img", help="Image commands")
    img_parser.add_argument("file", help="Image file to process")
    img_parser.add_argument("--background", default="255,255,255", help="Background color")
    img_parser.add_argument("--brightness", type=float, default=1.0, help="Brightness")
    img_parser.add_argument("--width", type=int, default=80, help="Maximum width of the output")
    img_parser.add_argument("--height", type=int, default=24, help="Maximum height of the output")
    img_parser.add_argument("--padding", type=str, default="0,0,0,0")
    img_parser.add_argument("--crop", type=str, default="0,0,0,0")

    # text command
    text_parser = subparsers.add_parser("text", help="Text commands")
    text_parser.add_argument("text", help="Text to render")
    text_parser.add_argument("--font", default="PT Serif", help="Font name to use")
    text_parser.add_argument("--font-size", type=int, default=24, help="Font size to use")
    text_parser.add_argument("--color", default="255,255,255", help="Font color (R,G,B)")
    text_parser.add_argument("--background", default="0,0,0", help="Background color (R,G,B)")
    text_parser.add_argument("--depth", help="Color depth", type=int, default=get_terminal_color_depth())

    # comp command
    comp_parser = subparsers.add_parser("comp", help="Compositing commands")
    comp_parser.add_argument("files", nargs='+', help="Image files to process")

    # Qr Code command
    qr_parser = subparsers.add_parser("qr", help="QR Code commands")
    qr_parser.add_argument("text", help="Text to encode in QR Code")
    qr_parser.add_argument("--color", default="255,255,255", help="Foreground color (R,G,B)")
    qr_parser.add_argument("--background", default="0,0,0", help="Background color (R,G,B)")

    args = parser.parse_args()
    if args.command == "img":
        bg_color_tuple = color_to_color(args.background)
        renderer = AnsiImageRenderer(
            bg_color=bg_color_tuple,
            brightness=args.brightness,
            max_width=args.width,
            max_height=args.height
        )
        img = Image.open(args.file)
        img = composite_background(img, bg_color=bg_color_tuple)
        img = resize_image(img, args.height)
        img = crop_image(
            img,
            crop_top=int(args.crop.split(",")[0]),
            crop_right=int(args.crop.split(",")[1]),
            crop_bottom=int(args.crop.split(",")[2]),
            crop_left=int(args.crop.split(",")[3])
        )
        img = pad_image(
            img,
            pad_top=int(args.padding.split(",")[0]),
            pad_right=int(args.padding.split(",")[1]),
            pad_bottom=int(args.padding.split(",")[2]),
            pad_left=int(args.padding.split(",")[3]),
            bg_color=bg_color_tuple
        )
        ansi_art = img_to_ansi(img, bg_color=bg_color_tuple, brightness=args.brightness)
        print("\n".join(ansi_art))
    elif args.command == "qr":
        fg_color_tuple = color_to_color(args.color)
        bg_color_tuple = color_to_color(args.background)
        qr = qrcode.QRCode(border=0)
        qr.add_data(args.text)
        qr.make()
        matrix = qr.get_matrix()  # <-- this is the "small" logical QR, not a pixel image
        size = len(matrix)
        img = Image.new("RGBA", (size, size))

        for y, row in enumerate(matrix):
            for x, val in enumerate(row):
                if val:
                    img.putpixel((x, y), (0, 0, 0, 255))    # Black, fully opaque
                else:
                    img.putpixel((x, y), (0, 0, 0, 0))      # Transparent (or change color as needed)
        img = colorize_image(img, fg_color=fg_color_tuple, bg_color=bg_color_tuple)
        print("\n".join(img_to_ansi(img)))
    elif args.command == "text":
        text = args.text
        font_color_tuple = args.color
        bg_color_tuple = args.background
        for line in text.splitlines():
            print(
                text_to_ansi(
                    line,
                    font=args.font,
                    size=args.font_size,
                    background=color_to_color(bg_color_tuple),
                    foreground=color_to_color(font_color_tuple)
                ), end="")
        print("\x1b[0m")  # Reset ANSI colors at the end
        # Here you would add the logic to process the font file
    elif args.command == "comp":
        # Assume args.files are stdout to ANSI streams, NOT IMAGES
        # We compoite EACH stream horizontally
        streams = [open(f).read() for f in args.files]
        print(combine_ansi_horizontally(*streams))
    else:
        print("Unknown command")
        return 1
    return 0

import sys

def main():
    # try:
    #     return _main()
    # except Exception as e:
    #     print(f"Error: {e}", file=sys.stderr)
    #     return 1
    _main()

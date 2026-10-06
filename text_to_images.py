#!/usr/bin/env python3
"""
Convert a text file into a batch of images, each containing a block of text.
Useful for sharing long text on platforms with character limits (e.g., Facebook carousel).
"""

import os
import sys
import argparse
from PIL import Image, ImageDraw, ImageFont

def find_default_font():
    """Try to locate a sensible TrueType font on the system."""
    candidates = [
        # Linux
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        # macOS
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        # Windows
        "C:\\Windows\\Fonts\\Arial.ttf",
        "C:\\Windows\\Fonts\\Calibri.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None

def wrap_text(text, font, max_width):
    """
    Wrap a single line of text to fit within max_width pixels.
    Returns a list of lines.
    """
    if not text.strip():
        return [""]  # preserve empty lines
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        # Try adding the word
        test_line = word if not current_line else current_line + " " + word
        # Use getlength if available (Pillow >= 8.0), else getsize
        if hasattr(font, "getlength"):
            width = font.getlength(test_line)
        else:
            width = font.getsize(test_line)[0]
        if width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            # If a single word is too long, break it by characters
            if hasattr(font, "getlength"):
                word_width = font.getlength(word)
            else:
                word_width = font.getsize(word)[0]
            if word_width > max_width:
                # Break the word
                temp = ""
                for char in word:
                    test_temp = temp + char
                    if hasattr(font, "getlength"):
                        w = font.getlength(test_temp)
                    else:
                        w = font.getsize(test_temp)[0]
                    if w <= max_width:
                        temp = test_temp
                    else:
                        lines.append(temp)
                        temp = char
                if temp:
                    current_line = temp
                else:
                    current_line = ""
            else:
                current_line = word
    if current_line:
        lines.append(current_line)
    return lines

def main():
    parser = argparse.ArgumentParser(description="Convert text file to a batch of images.")
    parser.add_argument("input", help="Path to input text file (UTF-8)")
    parser.add_argument("output_dir", help="Directory to save output images")
    parser.add_argument("--width", type=int, default=1080, help="Image width in pixels (default: 1080)")
    parser.add_argument("--height", type=int, default=1080, help="Image height in pixels (default: 1080)")
    parser.add_argument("--font", help="Path to .ttf font file (optional)")
    parser.add_argument("--font-size", type=int, default=28, help="Font size (default: 28)")
    parser.add_argument("--margin", type=int, default=40, help="Margin in pixels (default: 40)")
    parser.add_argument("--line-spacing", type=int, default=6, help="Extra spacing between lines (default: 6)")
    parser.add_argument("--bg", default="white", help="Background color (default: white)")
    parser.add_argument("--fg", default="black", help="Text color (default: black)")
    parser.add_argument("--prefix", default="page", help="Prefix for output filenames (default: page)")
    args = parser.parse_args()

    # Read input text
    with open(args.input, "r", encoding="utf-8") as f:
        text = f.read()

    # Load font
    if args.font:
        font_path = args.font
    else:
        font_path = find_default_font()
        if not font_path:
            print("No suitable font found. Please specify --font path/to/font.ttf")
            sys.exit(1)
        print(f"Using font: {font_path}")
    font = ImageFont.truetype(font_path, args.font_size)

    # Create output directory if needed
    os.makedirs(args.output_dir, exist_ok=True)

    # Prepare lines: split by newlines, then wrap each line
    raw_lines = text.splitlines()
    wrapped_lines = []
    for line in raw_lines:
        wrapped_lines.extend(wrap_text(line, font, args.width - 2 * args.margin))

    # Calculate how many lines fit per image
    # We need the line height: font ascent + descent + line_spacing
    if hasattr(font, "getmetrics"):
        ascent, descent = font.getmetrics()
    else:
        ascent, descent = font.getsize("Ag")[1], 0  # fallback
    line_height = ascent + descent + args.line_spacing
    max_lines_per_image = (args.height - 2 * args.margin) // line_height
    if max_lines_per_image < 1:
        print("Error: font size and margins too large for the given image height.")
        sys.exit(1)

    # Split into pages
    pages = []
    for i in range(0, len(wrapped_lines), max_lines_per_image):
        pages.append(wrapped_lines[i:i + max_lines_per_image])

    # Render each page
    for page_num, page_lines in enumerate(pages, start=1):
        img = Image.new("RGB", (args.width, args.height), color=args.bg)
        draw = ImageDraw.Draw(img)
        y = args.margin
        for line in page_lines:
            draw.text((args.margin, y), line, font=font, fill=args.fg)
            y += line_height
        # Save
        filename = f"{args.prefix}_{page_num:03d}.png"
        filepath = os.path.join(args.output_dir, filename)
        img.save(filepath, "PNG")
        print(f"Saved {filepath}")

    print(f"Done. {len(pages)} image(s) created in '{args.output_dir}'.")

if __name__ == "__main__":
    main()
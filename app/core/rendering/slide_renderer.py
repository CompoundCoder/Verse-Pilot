from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from PyQt6.QtGui import QPixmap
from app.core.bible import bible_lookup
import textwrap

def load_font_with_weight(path, size, weight=400):
    """
    Loads a variable font and sets its weight using axis variations.
    Falls back to the default bitmap font if the specified font is not found or not variable.
    """
    try:
        font = ImageFont.truetype(path, size)
        # Use set_variation_by_axes for numeric weight on a variable font
        font.set_variation_by_axes([weight])
        return font
    except (OSError, AttributeError):
        print(f"⚠️ Font '{path}' not found or not a variable font. Falling back to default.")
        try:
            return ImageFont.load_default(size=size)
        except AttributeError:
            return ImageFont.load_default()

def apply_rounded_corners(pil_image, radius=32):
    width, height = pil_image.size
    mask = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, width, height), radius=radius, fill=255)
    pil_image.putalpha(mask)
    return pil_image

def render_slide(book, chapter, verse, theme):
    img_width, img_height = 1280, 720
    img = Image.new("RGBA", (img_width, img_height), color=(0, 0, 0, 255))
    draw = ImageDraw.Draw(img)

    verse_text = bible_lookup.get_verse(book, chapter, verse)
    ref_text = f"{book} {chapter}:{verse}"

    font_path = "assets/fonts/Montserrat-VariableFont_wght.ttf"
    
    # --- Verse Text Rendering (Slightly Bold) ---
    font_size_main = 80
    font_main = load_font_with_weight(font_path, font_size_main, weight=600)

    # Wrap text and dynamically adjust font size
    char_width_ratio = 0.5
    max_chars_per_line = int((img_width * 0.9) / (font_size_main * char_width_ratio))
    
    wrapped_lines = textwrap.wrap(verse_text, width=max_chars_per_line, break_long_words=True)
    
    # Dynamically reduce font size if text is still too wide
    while True:
        text_too_wide = any(draw.textlength(line, font=font_main) > img_width * 0.9 for line in wrapped_lines)
        if not text_too_wide or font_size_main <= 20:
            break
        font_size_main -= 4
        font_main = load_font_with_weight(font_path, font_size_main, weight=600)
        max_chars_per_line = int((img_width * 0.9) / (font_size_main * char_width_ratio))
        wrapped_lines = textwrap.wrap(verse_text, width=max_chars_per_line, break_long_words=True)
        
    # Calculate vertical position for centered block
    num_lines = len(wrapped_lines)
    # Get line height from font properties for more accuracy
    _, top, _, bottom = font_main.getbbox("A")
    line_height = bottom - top
    total_text_height = num_lines * line_height * 1.2 # Add 20% spacing
    y_start = (img_height - total_text_height) / 2
    
    for i, line in enumerate(wrapped_lines):
        y = y_start + i * (line_height * 1.2)
        draw.text((img_width / 2, y), line, font=font_main, fill="white", anchor="ma", align="center")

    # --- Reference Text Rendering (Regular Weight) ---
    font_ref = load_font_with_weight(font_path, 36, weight=400)
    draw.text(
        (img_width / 2, img_height - 100), 
        ref_text, 
        font=font_ref, 
        fill="white", 
        anchor="mb"
    )

    img = apply_rounded_corners(img, radius=32)

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    pixmap = QPixmap()
    pixmap.loadFromData(buffer.getvalue(), "PNG")
    return pixmap
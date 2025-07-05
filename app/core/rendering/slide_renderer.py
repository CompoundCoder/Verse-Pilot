import os
import logging
import textwrap
from PIL import Image, ImageDraw, ImageFont
from typing import Optional

# --- Configuration ---
IMAGE_WIDTH = 1280
IMAGE_HEIGHT = 720
BG_COLOR = "white"
TEXT_COLOR = "black"
FONT_NAME = "Arial.ttf" # A common font, change if you have a specific one in assets/fonts
FONT_SIZE = 60
REF_FONT_SIZE = 40
OUTPUT_DIR = "output"

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def _get_font_path(font_name: str) -> Optional[str]:
    """Finds a font path, prioritizing the assets/fonts folder, then system fonts."""
    # Priority 1: Check in local assets/fonts folder
    # This path is relative to the project root
    local_font_path = os.path.join("assets", "fonts", font_name)
    if os.path.exists(local_font_path):
        return local_font_path
    
    # Priority 2: Check common macOS system font directory
    system_font_path = f"/System/Library/Fonts/Supplemental/{font_name}"
    if os.path.exists(system_font_path):
        return system_font_path
        
    logging.warning(f"Font '{font_name}' not in assets/fonts or system fonts. Using default.")
    return None

def render_verse_slide(
    text: str, 
    reference: str, 
    output_path: str = os.path.join(OUTPUT_DIR, "verse.png")
) -> Optional[str]:
    """
    Renders a verse text and reference onto an image, saving it to a file.

    Args:
        text: The main Bible verse text to display.
        reference: The verse reference (e.g., "John 3:16").
        output_path: The path to save the generated image file.

    Returns:
        The final output path of the image if successful, otherwise None.
    """
    try:
        img = Image.new('RGB', (IMAGE_WIDTH, IMAGE_HEIGHT), color=BG_COLOR)
        draw = ImageDraw.Draw(img)

        font_path = _get_font_path(FONT_NAME)
        font = ImageFont.truetype(font_path, FONT_SIZE) if font_path else ImageFont.load_default()
        ref_font = ImageFont.truetype(font_path, REF_FONT_SIZE) if font_path else ImageFont.load_default()

        # Wrap text to fit within 90% of image width
        avg_char_width = FONT_SIZE * 0.45
        max_chars = int((IMAGE_WIDTH * 0.9) / avg_char_width)
        wrapped_text = textwrap.fill(text, width=max_chars)
        
        # Position and draw main text
        text_bbox = draw.textbbox((0, 0), wrapped_text, font=font, align="center")
        text_x = (IMAGE_WIDTH - (text_bbox[2] - text_bbox[0])) / 2
        text_y = (IMAGE_HEIGHT - (text_bbox[3] - text_bbox[1])) / 2
        draw.text((text_x, text_y), wrapped_text, font=font, fill=TEXT_COLOR, align="center")

        # Position and draw reference text
        ref_bbox = draw.textbbox((0, 0), reference, font=ref_font)
        ref_x = (IMAGE_WIDTH - (ref_bbox[2] - ref_bbox[0])) / 2
        ref_y = IMAGE_HEIGHT - 80 # 80px from bottom
        draw.text((ref_x, ref_y), reference, font=ref_font, fill=TEXT_COLOR)
        
        # Ensure output directory exists and save the image
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path)
        logging.info(f"Successfully rendered slide to {output_path}")
        return output_path

    except Exception as e:
        logging.error(f"Failed to render verse slide: {e}", exc_info=True)
        return None

if __name__ == '__main__':
    print("--- Testing Slide Renderer ---")
    test_text = "For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life."
    test_ref = "John 3:16"
    
    file_path = render_verse_slide(test_text, test_ref)
    if file_path:
        print(f"Slide created at: {file_path}")
        # To see the result on macOS, uncomment the line below:
        # os.system(f"open {file_path}")

    # Test a longer verse to check wrapping
    long_text = "And be not conformed to this world: but be ye transformed by the renewing of your mind, that ye may prove what is that good, and acceptable, and perfect, will of God."
    long_ref = "Romans 12:2"
    render_verse_slide(long_text, long_ref) 
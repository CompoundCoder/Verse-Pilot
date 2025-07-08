"""
This file contains archived, legacy code from the slide renderer.
It includes logic for rendering slides to disk as PNG files, which was
superseded by an in-memory rendering approach using BytesIO and QPixmap.

This code is kept for reference purposes.
"""

# --- Theme Configuration ---
# This was part of the original design but is not used by the current
# in-memory render_slide function.
THEMES = {
    "dark": {
        "bg_color": "#121212",
        "text_color": "#EAEAEA",
        "font_name": "Arial.ttf"
    },
    "light": {
        "bg_color": "#FFFFFF",
        "text_color": "#121212",
        "font_name": "Arial.ttf"
    }
}

# --- Image Configuration ---
# These constants were used by the old file-based renderer. The new
# renderer uses hardcoded values. The OUTPUT_DIR is a clear sign
# of file-based operations.
IMAGE_WIDTH = 1280
IMAGE_HEIGHT = 720
FONT_SIZE = 60
REF_FONT_SIZE = 40
OUTPUT_DIR = "output" 
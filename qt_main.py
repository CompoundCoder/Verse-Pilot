import os
from dotenv import load_dotenv
load_dotenv() # Load .env before any other application imports

import sys
import logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from app.qt_ui.main_window import MainWindow

def load_stylesheet(app):
    """Loads the main QSS stylesheet."""
    dir_path = os.path.dirname(os.path.realpath(__file__))
    stylesheet_path = os.path.join(dir_path, "app/qt_ui/resources/mac_dark.qss")
    try:
        with open(stylesheet_path, "r") as f:
            app.setStyleSheet(f.read())
        logging.info("Successfully loaded stylesheet.")
    except FileNotFoundError:
        logging.warning(f"Stylesheet not found at {stylesheet_path}. UI will not be styled.")

def main():
    """
    The main entry point for the VersePilot application.
    Initializes the PyQt6 application, loads the main window, and applies styling.
    """
    # --- Confirm AI Backend ---
    # This provides immediate feedback about which AI model is active.
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL_ID = os.getenv("GEMINI_MODEL_ID")

    if GEMINI_API_KEY and GEMINI_MODEL_ID:
        print(f"✅ AI DETECTOR: Using Gemini model -> {GEMINI_MODEL_ID}")
        ai_available = True
    else:
        print("❌ Gemini API key or model ID missing. Disabling AI features.")
        ai_available = False

    # --- Initialize Application ---
    app = QApplication(sys.argv)
    app.setApplicationName("VersePilot")
    app.setApplicationVersion("1.0")

    # Set app icon before showing any windows
    try:
        dir_path = os.path.dirname(os.path.realpath(__file__))
        icon_path = os.path.join(dir_path, "app/qt_ui/assets/icon.png")
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
        else:
            logging.warning(f"App icon not found at {icon_path}")
    except Exception as e:
        logging.error(f"Error setting app icon: {e}")

    load_stylesheet(app)

    # The VerseDetector is no longer instantiated here.
    # MainWindow now manages its own verse detection logic internally.
    window = MainWindow(ai_available=ai_available)
    window.show()
    
    # --- Start Event Loop ---
    sys.exit(app.exec())

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    main() 
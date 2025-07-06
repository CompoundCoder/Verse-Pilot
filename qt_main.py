import sys
import os
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

    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    main() 
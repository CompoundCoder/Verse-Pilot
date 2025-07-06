import sys
import queue
import time
import logging
import os
import sounddevice as sd
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QToolBar, 
    QPushButton, QLabel, QSplitter, QComboBox, QMessageBox, QMenu,
    QGraphicsDropShadowEffect, QSizePolicy
)
from PyQt6.QtGui import QIcon, QAction, QPixmap, QColor
from PyQt6.QtCore import Qt, QSize, QTimer

# --- App Dependencies ---
from app.core.settings.settings_model import get_settings
from app.core.audio.listener import VerseListener
from app.core.bible import bible_lookup
from app.core.rendering import slide_renderer
from app.qt_ui.components.sidebar_panel import SidebarPanel
from app.qt_ui.settings_screen import SettingsScreen
from app.qt_ui.verse_confirmation_popup import VerseConfirmationPopup
from app.qt_ui.components.edit_verse_popup import EditVersePopup
from app.qt_ui.resources.icon_provider import get_icon

# --- Constants ---
SIDEBAR_ICON_PATH = "app/assets/icons/sidebar_toggle.png"
PREVIEW_IMAGE_PATH = "output/verse.png"

class MainWindow(QMainWindow):
    """
    The main application window for the PyQt6 version of VersePilot.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VersePilot (PyQt6)")
        self.setGeometry(100, 100, 900, 700)

        # --- Child Windows ---
        self.settings_window = None

        # --- State and Core Logic ---
        self.mic_devices = {}
        self.live_history = []
        self.confirmation_buffer = []
        self.rejected_keys = set()
        
        self.verse_queue = queue.Queue()
        self.verse_listener = VerseListener()
        
        # --- Main Layout ---
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0,0,0,0)
        self.main_layout.setSpacing(0)

        # --- Menu Bar & Toolbar ---
        self._setup_menu_bar()
        self._setup_toolbar()
        
        # --- Content Area (Splitter) ---
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_layout.addWidget(self.splitter)

        # --- Sidebar ---
        self._setup_sidebar()
        
        # --- Main Content ---
        self._setup_main_content()
        
        # Restore initial state
        self._apply_initial_settings()
        
        # --- Queue Polling Timer ---
        self.queue_timer = QTimer(self)
        self.queue_timer.timeout.connect(self._check_verse_queue)
        self.queue_timer.start(100) # Check every 100ms

    def _setup_menu_bar(self):
        """Creates the main application menu bar."""
        menu_bar = self.menuBar()
        
        # On macOS, this creates a native-style "VersePilot" menu.
        # On Windows/Linux, it will appear as a standard top-level menu.
        app_menu = menu_bar.addMenu("VersePilot")

        about_action = QAction("About VersePilot", self)
        about_action.triggered.connect(self._show_about_dialog)
        app_menu.addAction(about_action)

        app_menu.addSeparator()

        settings_action = QAction("Settings...", self)
        settings_action.setIcon(get_icon("gear"))
        settings_action.triggered.connect(self._open_settings_window)
        app_menu.addAction(settings_action)

        app_menu.addSeparator()

        quit_action = QAction("Quit VersePilot", self)
        quit_action.setShortcut("Command+Q")
        quit_action.triggered.connect(self.close)
        app_menu.addAction(quit_action)

    def _setup_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Sidebar Toggle Action
        self.toggle_sidebar_action = QAction(self)
        self.toggle_sidebar_action.setIcon(get_icon("sidebar"))
        self.toggle_sidebar_action.setToolTip("Toggle Sidebar Visibility")
        self.toggle_sidebar_action.setCheckable(True)
        self.toggle_sidebar_action.setChecked(get_settings().sidebar_visible)
        self.toggle_sidebar_action.triggered.connect(self._toggle_sidebar)
        toolbar.addAction(self.toggle_sidebar_action)

        # Spacer to push settings button to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)

        # Settings Action
        settings_action = QAction(self)
        settings_action.setIcon(get_icon("gear"))
        settings_action.setToolTip("Open Settings")
        settings_action.triggered.connect(self._open_settings_window)
        toolbar.addAction(settings_action)

    def _setup_sidebar(self):
        self.sidebar_container = QWidget()
        self.sidebar_layout = QVBoxLayout(self.sidebar_container)
        self.sidebar_layout.setContentsMargins(5, 5, 5, 5)
        
        self.queue_panel = SidebarPanel("Queue")
        self.history_panel = SidebarPanel("History")
        
        # Connect signals
        self.queue_panel.verse_double_clicked.connect(self._on_sidebar_double_click)
        self.history_panel.verse_double_clicked.connect(self._on_sidebar_double_click)
        self.queue_panel.verse_right_clicked.connect(self._on_sidebar_right_click)
        self.history_panel.verse_right_clicked.connect(self._on_sidebar_right_click)
        
        self.sidebar_layout.addWidget(self.queue_panel)
        self.sidebar_layout.addWidget(self.history_panel)
        
        self.splitter.addWidget(self.sidebar_container)

    def _setup_main_content(self):
        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(10, 10, 10, 10)

        self.preview_label = QLabel("Preview will go here")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("font-size: 24px; color: #888;")
        
        # Mic Control Bar
        mic_controls_widget = self._create_mic_controls()

        content_layout.addWidget(self.preview_label, 1) # Add with stretch
        content_layout.addWidget(mic_controls_widget)   # Add at the bottom

        self.splitter.addWidget(content_area)
        
        # Set initial sizes for the splitter
        self.splitter.setSizes([250, 650])

    def _create_mic_controls(self) -> QWidget:
        """Creates the microphone control bar widget."""
        mic_control_bar = QWidget()
        mic_layout = QHBoxLayout(mic_control_bar)
        mic_layout.setContentsMargins(0, 5, 0, 5)

        # Mic Dropdown
        self.mic_dropdown = QComboBox()
        self.mic_dropdown.setPlaceholderText("No input devices found")
        self.mic_dropdown.currentTextChanged.connect(self._on_mic_selected)
        
        # Status Label
        self.status_label = QLabel("Idle")
        self.status_label.setObjectName("StatusLabel")

        # Buttons
        self.start_button = QPushButton("Start Listening")
        self.start_button.setIcon(get_icon("mic"))
        self.start_button.setIconSize(QSize(16, 16))
        self.start_button.clicked.connect(self._on_start_listening)
        self.start_button.setEnabled(False)

        self.stop_button = QPushButton("Stop Listening")
        self.stop_button.setIcon(get_icon("stop"))
        self.stop_button.setIconSize(QSize(16, 16))
        self.stop_button.clicked.connect(self._on_stop_listening)
        self.stop_button.setEnabled(False)

        mic_layout.addWidget(self.mic_dropdown, 2) # Give dropdown more stretch
        mic_layout.addWidget(self.status_label, 3)
        mic_layout.addWidget(self.start_button, 1)
        mic_layout.addWidget(self.stop_button, 1)

        self._populate_mic_dropdown()
        return mic_control_bar

    def _populate_mic_dropdown(self):
        """Queries sounddevice for mics and populates the dropdown."""
        try:
            devices = sd.query_devices()
            input_devices = [d for d in devices if d['max_input_channels'] > 0]
            if not input_devices:
                return

            self.mic_devices = {d['name']: i for i, d in enumerate(devices) if d['max_input_channels'] > 0}
            self.mic_dropdown.addItems(self.mic_devices.keys())
            
            # Restore last used mic
            last_mic = get_settings().last_used_mic
            if last_mic and last_mic in self.mic_devices:
                self.mic_dropdown.setCurrentText(last_mic)
            
            self.start_button.setEnabled(True)

        except Exception as e:
            logging.error(f"Could not query audio devices: {e}", exc_info=True)
            self.status_label.setText("Error: Audio devices not found.")

    def _apply_initial_settings(self):
        """Loads and applies settings at startup."""
        settings = get_settings()
        self.sidebar_container.setVisible(settings.sidebar_visible)
        settings.sidebar_visible = not self.sidebar_container.isVisible()

    def _toggle_sidebar(self):
        """Toggles the visibility of the sidebar and saves the state."""
        is_visible = self.sidebar_container.isVisible()
        self.sidebar_container.setVisible(not is_visible)
        
        # Persist the new state
        settings = get_settings()
        settings.sidebar_visible = not is_visible

    def _on_mic_selected(self, mic_name: str):
        """Saves the selected microphone to settings."""
        if mic_name and mic_name in self.mic_devices:
            get_settings().last_used_mic = mic_name
            logging.info(f"Microphone selection saved: {mic_name}")

    def _on_start_listening(self):
        """Starts the VerseListener with the selected microphone."""
        selected_mic_name = self.mic_dropdown.currentText()
        if not selected_mic_name or selected_mic_name not in self.mic_devices:
            self.status_label.setText("Error: Please select a valid microphone.")
            return

        try:
            device_index = self.mic_devices[selected_mic_name]
            self.verse_listener.start_listening(self.verse_queue, input_device_index=device_index)
            
            self.status_label.setText("Listening...")
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.mic_dropdown.setEnabled(False)
            logging.info(f"VerseListener started on '{selected_mic_name}'")

        except Exception as e:
            logging.error(f"Failed to start listener on '{selected_mic_name}': {e}", exc_info=True)
            self.status_label.setText("Error: Could not start listener.")

    def _on_stop_listening(self):
        """Stops the VerseListener."""
        self.verse_listener.stop_listening()
        self.status_label.setText("Idle")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.mic_dropdown.setEnabled(True)
        logging.info("VerseListener stopped.")

    def _check_verse_queue(self):
        """Periodically checks the verse queue for new data from the listener."""
        try:
            verse_data = self.verse_queue.get_nowait()
            logging.info(f"QT_UI: Dequeued verse: {verse_data}")

            # --- Filtering Logic ---
            verse_key = self._get_verse_key(verse_data)

            # 1. Skip if already rejected
            if verse_key in self.rejected_keys:
                logging.debug(f"Skipping rejected verse: {verse_key}")
                return

            # 2. Skip if already processed (in history or buffer)
            if any(self._get_verse_key(v) == verse_key for v in self.live_history) or \
               any(self._get_verse_key(v) == verse_key for v in self.confirmation_buffer):
                logging.debug(f"Skipping already processed verse: {verse_key}")
                return

            # 3. Route based on confidence
            settings = get_settings()
            confidence = verse_data.get("confidence", 1.0)

            if settings.require_approval and confidence < settings.confidence_threshold:
                logging.info(f"Verse {verse_key} requires confirmation.")
                self.confirmation_buffer.append(verse_data)
                self.queue_panel.update_verses(self.confirmation_buffer)
                
                # Launch confirmation popup
                popup = VerseConfirmationPopup(
                    verse_data,
                    settings.auto_show_delay_seconds,
                    settings.auto_show_after_delay,
                    self
                )
                if popup.exec(): # .exec() is blocking and returns True if accepted
                    self._on_confirmation_result(True, verse_data)
                else:
                    self._on_confirmation_result(False, verse_data)

            else:
                logging.info(f"Verse {verse_key} sent directly to history (confidence: {confidence:.2f})")
                self.live_history.append(verse_data)
                self._update_history_panel()
                self._process_and_render_verse(verse_data)

        except queue.Empty:
            pass # No new verses, normal operation
        except Exception as e:
            logging.error(f"An error occurred while processing the verse queue: {e}", exc_info=True)

    def _on_sidebar_double_click(self, verse_data: dict):
        """Renders any verse that is double-clicked in a sidebar."""
        logging.info(f"Double-click detected on verse: {verse_data}")
        self._process_and_render_verse(verse_data)

    def _on_sidebar_right_click(self, verse_data: dict, global_pos):
        """Creates and shows a context menu for a sidebar item."""
        # --- Context Menu ---
        menu = QMenu(self)

        # Apply a drop shadow for a more "native" feel
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 180))
        menu.setGraphicsEffect(shadow)

        # Edit Action
        edit_action = QAction("Edit", self)
        edit_action.setIcon(get_icon("edit"))
        edit_action.triggered.connect(lambda: self._edit_verse(verse_data))
        menu.addAction(edit_action)

        # Delete Action
        delete_action = QAction("Delete", self)
        delete_action.setIcon(get_icon("trash"))
        delete_action.triggered.connect(lambda: self._delete_verse(verse_data))
        menu.addAction(delete_action)

        menu.exec(global_pos)

    def _on_confirmation_result(self, approved: bool, verse_data: dict):
        """Handles the result from the confirmation popup."""
        key = self._get_verse_key(verse_data)
        
        # Remove from buffer regardless of outcome
        self.confirmation_buffer = [v for v in self.confirmation_buffer if self._get_verse_key(v) != key]
        self.queue_panel.update_verses(self.confirmation_buffer)

        if approved:
            logging.info(f"Verse approved: {key}")
            self.live_history.append(verse_data)
            self._update_history_panel()
            self._process_and_render_verse(verse_data)
        else:
            logging.info(f"Verse rejected: {key}")
            self.rejected_keys.add(key)
    
    def _update_history_panel(self):
        """Sorts and updates the history panel."""
        sorted_history = sorted(self.live_history, key=lambda v: v.get('timestamp', 0), reverse=True)
        self.history_panel.update_verses(sorted_history)

    def _process_and_render_verse(self, verse_data: dict):
        """Looks up a verse, renders it, and displays it in the preview."""
        try:
            book = verse_data.get("book")
            chapter = verse_data.get("chapter")
            verse = verse_data.get("verse")

            verse_text = bible_lookup.get_verse(book, chapter, verse)
            if "not found" in verse_text:
                self.preview_label.setText(f"Verse not found:\n{book} {chapter}:{verse}")
                self.preview_label.setPixmap(QPixmap()) # Clear image
                return

            reference = f"{book} {chapter}:{verse}"
            slide_renderer.render_verse_slide(verse_text, reference, PREVIEW_IMAGE_PATH)

            if os.path.exists(PREVIEW_IMAGE_PATH):
                pixmap = QPixmap(PREVIEW_IMAGE_PATH)
                # Scale pixmap to fit the label while preserving aspect ratio
                self.preview_label.setPixmap(pixmap.scaled(
                    self.preview_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                ))
            else:
                self.preview_label.setText(f"Error: Rendered file not found.")
                self.preview_label.setPixmap(QPixmap())

        except Exception as e:
            logging.error(f"Error rendering verse slide: {e}", exc_info=True)
            self.preview_label.setText(f"Error rendering slide.")
            self.preview_label.setPixmap(QPixmap())

    def _get_verse_key(self, verse_data: dict) -> tuple:
        """Generates a unique, hashable key for a verse."""
        return (verse_data.get("book"), verse_data.get("chapter"), verse_data.get("verse"))

    def _edit_verse(self, original_data: dict):
        """Opens a dialog to edit a verse."""
        popup = EditVersePopup(original_data, self)
        if popup.exec():
            updated_data = popup.get_updated_verse_data()
            if not updated_data:
                return

            original_key = self._get_verse_key(original_data)
            
            # Find and replace in the correct list
            found_and_updated = False
            for i, verse in enumerate(self.confirmation_buffer):
                if self._get_verse_key(verse) == original_key:
                    self.confirmation_buffer[i] = updated_data
                    found_and_updated = True
                    break
            
            if not found_and_updated:
                for i, verse in enumerate(self.live_history):
                    if self._get_verse_key(verse) == original_key:
                        self.live_history[i] = updated_data
                        found_and_updated = True
                        break
            
            if found_and_updated:
                logging.info(f"Verse updated: {original_key} -> {self._get_verse_key(updated_data)}")
                self._update_sidebar_panels()
                # If it's the current verse, re-render it
                # Note: A proper check against a `self.current_verse` state would be better
                # self._process_and_render_verse(updated_data) # DECOUPLED: Rendering is now only on double-click

    def _delete_verse(self, verse_data: dict):
        """Confirms and deletes a verse from the appropriate list."""
        key = self._get_verse_key(verse_data)
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete {key[0]} {key[1]}:{key[2]}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Try removing from confirmation buffer first
            buffer_len = len(self.confirmation_buffer)
            self.confirmation_buffer = [v for v in self.confirmation_buffer if self._get_verse_key(v) != key]
            if len(self.confirmation_buffer) < buffer_len:
                logging.info(f"Verse deleted from confirmation buffer: {key}")
                self._update_sidebar_panels()
                return

            # If not in buffer, try removing from live history
            history_len = len(self.live_history)
            self.live_history = [v for v in self.live_history if self._get_verse_key(v) != key]
            if len(self.live_history) < history_len:
                logging.info(f"Verse deleted from live history: {key}")
                self._update_sidebar_panels()
                # TODO: Clear preview if this was the active verse
                return

    def _update_sidebar_panels(self):
        """Updates both sidebar panels."""
        self.queue_panel.update_verses(self.confirmation_buffer)
        self.history_panel.update_verses(self.live_history)

    def closeEvent(self, event):
        """Ensures graceful shutdown of background threads."""
        logging.info("Shutting down VerseListener...")
        self.verse_listener.stop_listening()
        event.accept()

    def _show_about_dialog(self):
        """Displays a simple 'About' message box."""
        QMessageBox.about(
            self,
            "About VersePilot",
            "<b>VersePilot (PyQt6 Migration)</b>"
            "<p>Version 0.2.0</p>"
            "<p>A real-time verse detection and display application.</p>"
        )

    def _open_settings_window(self):
        """Opens the settings window, ensuring only one instance exists."""
        if self.settings_window is None or not self.settings_window.isVisible():
            self.settings_window = SettingsScreen(self)
            self.settings_window.show()
        else:
            self.settings_window.activateWindow() 
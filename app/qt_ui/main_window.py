import sys
import queue
import time
import logging
import os
import sounddevice as sd
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QToolBar, 
    QPushButton, QLabel, QSplitter, QComboBox, QMessageBox, QMenu,
    QGraphicsDropShadowEffect, QSizePolicy, QFrame,
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsRectItem
)
from PyQt6.QtGui import QIcon, QAction, QPixmap, QColor, QPainter, QBrush, QPen
from PyQt6.QtCore import Qt, QSize, QTimer, QThread, QPropertyAnimation

# --- App Dependencies ---
from app.core.settings.settings_model import get_settings
from app.core.audio.listener import VerseListener
from app.core.bible import bible_lookup
from app.core.bible.constants import BOOK_TO_NUM_CHAPTERS
from app.core.rendering import slide_renderer
from app.qt_ui.components.sidebar_panel import SidebarPanel
from app.qt_ui.settings_window import SettingsWindow
from app.qt_ui.verse_confirmation_popup import VerseConfirmationPopup
from app.qt_ui.components.user_confirm_popup import UserConfirmPopup
from app.qt_ui.components.edit_verse_popup import EditVersePopup
from app.qt_ui.resources.icon_provider import get_icon
from app.qt_ui.components.mic_ripple_widget import MicRippleWidget
from app.qt_ui.components.upward_combo_box import UpwardComboBox
# --- Dev Tools (can be safely removed) ---
from app.qt_ui.components.dev_input_window import DevInputWindow
# -----------------------------------------

# --- Placeholder for verse data parsing ---
def parse_verse_data(verse_data: dict) -> tuple:
    """Helper to extract book, chapter, and verse from the data dictionary."""
    return verse_data.get('book'), verse_data.get('chapter'), verse_data.get('verse')

# --- Constants ---
SIDEBAR_ICON_PATH = "app/assets/icons/sidebar_toggle.png"
PREVIEW_IMAGE_PATH = "output/verse.png"

class MainWindow(QMainWindow):
    """
    The main application window for the PyQt6 version of VersePilot.
    """
    def __init__(self, ai_available: bool, parent=None):
        super().__init__(parent)
        self.settings = get_settings() # Ensure settings are loaded first
        self.ai_available = ai_available
        self.setWindowTitle("VersePilot")
        self.setGeometry(100, 100, 900, 700)

        # --- Child Windows ---
        self.settings_window = None
        # --- Dev Tools (can be safely removed) ---
        self.dev_input_window = DevInputWindow(self)
        self.dev_input_window.text_submitted.connect(self._handle_dev_input)
        # -----------------------------------------

        # --- State and Core Logic ---
        self.mic_devices = {}
        self.selected_mic_index = None # Store the selected device index
        self.live_history = []
        self.confirmation_buffer = []
        self.rejected_keys = set()
        self.current_verse_data = None # Track the currently displayed verse
        
        self.verse_queue = queue.Queue()
        self.verse_listener = VerseListener(
            ai_available=self.ai_available,
            gemini_api_key=os.getenv("GEMINI_API_KEY"),
            gemini_model_id=os.getenv("GEMINI_MODEL_ID")
        )
        self.verse_listener.verse_needs_confirmation.connect(self._show_confirmation_popup)
        
        # --- UI State for AI Status ---
        self._ai_color_status = "red"  # Initial state
        self._ai_backend_name = ""     # Initial state
        
        # --- Main Layout ---
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0,0,0,0)
        self.main_layout.setSpacing(0)

        # --- Actions ---
        self._create_actions()

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

        # --- Queue Polling Timer ---
        self.queue_timer = QTimer(self)
        self.queue_timer.timeout.connect(self._check_verse_queue)
        self.queue_timer.start(100) # Check every 100ms
        
        # Restore initial state
        self._apply_initial_settings()
        
        # --- AI Status Monitor (Removed) ---
        # self._setup_ai_monitor()

    def _create_actions(self):
        """Creates shared actions for menus and toolbars."""
        self.preferences_action = QAction(get_icon("gear"), "Preferences...", self)
        self.preferences_action.setShortcut("Command+,")
        self.preferences_action.setMenuRole(QAction.MenuRole.PreferencesRole)
        self.preferences_action.triggered.connect(self._open_settings_dialog)

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

        # This action is handled by _create_actions now, just add it.
        app_menu.addAction(self.preferences_action)

        app_menu.addSeparator()

        quit_action = QAction("Quit VersePilot", self)
        quit_action.setShortcut("Command+Q")
        quit_action.triggered.connect(self.close)
        app_menu.addAction(quit_action)

        # --- Dev Tools (can be safely removed) ---
        dev_menu = menu_bar.addMenu("Developer")
        manual_input_action = QAction("Manual Text Input...", self)
        manual_input_action.setShortcut("Ctrl+Shift+T")
        manual_input_action.triggered.connect(self.dev_input_window.show)
        dev_menu.addAction(manual_input_action)
        # -----------------------------------------


    def _setup_toolbar(self):
        """Creates and configures the main application toolbar."""
        # --- Initialize Toolbar FIRST ---
        self.toolbar = QToolBar("Main Toolbar")
        self.toolbar.setObjectName("MainToolbar")
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        self.toolbar.setIconSize(QSize(18, 18))
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)

        # --- Now, Add Actions to the Toolbar ---
        # Sidebar Toggle Button
        self.sidebar_toggle_action = QAction(get_icon("sidebar"), "Toggle Sidebar", self)
        self.sidebar_toggle_action.setToolTip("Show/Hide Sidebar")
        self.sidebar_toggle_action.setCheckable(True)
        self.toolbar.addAction(self.sidebar_toggle_action)
        self.toolbar.addSeparator()

        # Spacer to push settings button to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.toolbar.addWidget(spacer)

        # Use the shared preferences action
        self.toolbar.addAction(self.preferences_action)
        self.preferences_action.setToolTip("Open Preferences")

    def _setup_sidebar(self):
        """Sets up the sidebar with resizable Queue and History panels."""
        self.sidebar_container = QWidget()
        self.sidebar_container.setObjectName("SidebarContainer") # For styling
        sidebar_layout = QVBoxLayout(self.sidebar_container)
        sidebar_layout.setContentsMargins(4, 4, 4, 4)
        sidebar_layout.setSpacing(6)

        self.sidebar_splitter = QSplitter(Qt.Orientation.Vertical)
        self.sidebar_splitter.setHandleWidth(1)
        self.sidebar_splitter.setChildrenCollapsible(False)

        self.queue_panel = SidebarPanel("Queue")
        self.history_panel = SidebarPanel("History")

        self.queue_panel.verse_double_clicked.connect(self._on_sidebar_double_click)
        self.history_panel.verse_double_clicked.connect(self._on_sidebar_double_click)
        self.queue_panel.verse_right_clicked.connect(self._on_sidebar_right_click)
        self.history_panel.verse_right_clicked.connect(self._on_sidebar_right_click)

        self.sidebar_splitter.addWidget(self.queue_panel)
        self.sidebar_splitter.addWidget(self.history_panel)
        
        sidebar_layout.addWidget(self.sidebar_splitter)
        
        # Restore saved sizes if available
        saved_sizes = self.settings.sidebar_split_sizes
        if saved_sizes and len(saved_sizes) == 2:
            self.sidebar_splitter.setSizes(saved_sizes)
        else:
            self.sidebar_splitter.setSizes([250, 650]) # Default sizes

        # Restore sidebar visibility from settings
        is_visible = self.settings.sidebar_visible
        self.sidebar_container.setVisible(is_visible)
        # Sync the toggle button's state without triggering the signal
        self.sidebar_toggle_action.setChecked(is_visible)

        self.splitter.insertWidget(0, self.sidebar_container)

    def _setup_main_content(self):
        """Sets up the main content area with a vertical stack layout."""
        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(15, 15, 15, 15)
        content_layout.setSpacing(15)

        # --- 1. Preview Section (Canvas) ---
        self.canvas_wrapper = QWidget()
        self.canvas_wrapper.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                border-radius: 16px;
                border: 1px solid #444;
                padding: 0px;
                margin: 0px;
            }
        """)
        canvas_layout = QVBoxLayout(self.canvas_wrapper)
        canvas_layout.setContentsMargins(0, 0, 0, 0)
        canvas_layout.setSpacing(0)

        self.graphics_view = QGraphicsView()
        self.graphics_scene = QGraphicsScene(self.graphics_view)
        self.graphics_view.setScene(self.graphics_scene)
        self.graphics_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.graphics_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.graphics_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.graphics_view.setStyleSheet("background: transparent; border: none;")
        
        # Enforce 16:9 canvas by setting fixed sceneRect
        self.graphics_scene.setSceneRect(0, 0, 1280, 720)

        canvas_layout.addWidget(self.graphics_view)
        content_layout.addWidget(self.canvas_wrapper)

        # --- 2. Mic Control Area (Centered) ---
        self.mic_ripple_widget = MicRippleWidget()
        self.mic_ripple_widget.listening_state_changed.connect(self._on_toggle_listening)
        self.mic_ripple_widget.setEnabled(False)

        # Horizontally center the mic widget using a nested layout
        mic_container_layout = QHBoxLayout()
        mic_container_layout.addStretch()
        mic_container_layout.addWidget(self.mic_ripple_widget)
        mic_container_layout.addStretch()
        content_layout.addLayout(mic_container_layout)

        # --- Bottom Toolbar ---
        bottom_bar = QWidget()
        bottom_bar.setObjectName("BottomToolbar")
        self.bottom_layout = QHBoxLayout(bottom_bar)
        self.bottom_layout.setContentsMargins(12, 4, 12, 4)
        self.bottom_layout.setSpacing(6)

        self.status_label = QLabel("Idle")
        self.status_label.setObjectName("StatusLabel")

        self.mic_dropdown = UpwardComboBox() # Continue using the flicker-free combobox
        self.mic_dropdown.setObjectName("MicDropdown")
        self.mic_dropdown.setMinimumWidth(160)
        self.mic_dropdown.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.mic_dropdown.view().setMinimumWidth(200)
        self.mic_dropdown.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.mic_dropdown.currentTextChanged.connect(self._on_mic_selected)

        self.bottom_layout.addStretch()
        self.bottom_layout.addWidget(self.status_label)
        self.bottom_layout.addWidget(self.mic_dropdown)
        
        content_layout.addWidget(bottom_bar)

        # --- Configure Layout Stretching ---
        content_layout.setStretch(0, 2)  # Preview takes 2/3
        content_layout.setStretch(1, 1)  # Mic widget takes 1/3
        content_layout.setStretch(2, 0)  # Toolbar has fixed height

        # --- Final Assembly ---
        self.splitter.addWidget(content_area)
        self.splitter.setSizes([250, 650])
        self._populate_mic_devices()
        self._apply_ai_availability()

    def _handle_dev_input(self, text: str):
        """Processes text submitted from the developer input window."""
        if not text.strip():
            return
        logging.info(f"[DevTool] Manually processing transcript: '{text}'")
        self.verse_listener.process_manual_transcript(text)

    def _populate_mic_devices(self):
        """Queries sounddevice for mics and populates the dropdown."""
        self.mic_dropdown.clear()
        try:
            devices = sd.query_devices()
            self.mic_devices = {d['name']: i for i, d in enumerate(devices) if d['max_input_channels'] > 0}
            
            if not self.mic_devices:
                self.status_label.setText("Error: No input devices found.")
                self.mic_dropdown.setPlaceholderText("No devices")
                return

            self.mic_dropdown.addItems(self.mic_devices.keys())
            
            last_mic = self.settings.mic_device
            if last_mic and last_mic in self.mic_devices:
                self.mic_dropdown.setCurrentText(last_mic)
            
            self.mic_ripple_widget.setEnabled(True)
            self.status_label.setText("Idle")
            
        except Exception as e:
            logging.error(f"Could not query audio devices: {e}")
            self.status_label.setText("Error: Audio devices not found.")
            self.mic_dropdown.setPlaceholderText("Error")

    def _apply_ai_availability(self):
        """Disables AI-dependent UI if credentials are not available."""
        if not self.ai_available:
            self.mic_ripple_widget.setEnabled(False)
            self.mic_ripple_widget.set_status(False, "AI_Error")
            # Override the tooltip to provide a clear explanation
            self.mic_ripple_widget.setToolTip("AI features unavailable. Please check your API key settings.")
            # Optionally, disable the mic dropdown as well
            self.mic_dropdown.setEnabled(False)
            self.status_label.setText("AI Unavailable")


    def _apply_initial_settings(self):
        """Connects signals and applies settings on startup."""
        # Connect signals after UI is built
        self.sidebar_toggle_action.toggled.connect(self._on_sidebar_toggled)
        self.sidebar_splitter.splitterMoved.connect(self._on_sidebar_resized)

        # Apply sidebar visibility from settings
        is_visible = self.settings.sidebar_visible
        self.sidebar_container.setVisible(is_visible)
        self.sidebar_toggle_action.setChecked(is_visible)

        # Apply sidebar splitter position
        saved_sizes = self.settings.sidebar_split_sizes
        if saved_sizes and len(saved_sizes) == 2:
            self.sidebar_splitter.setSizes(saved_sizes)
        else:
            self.sidebar_splitter.setSizes([250, 450])

    def _on_sidebar_toggled(self, is_checked: bool):
        """Shows or hides the sidebar based on the toggle button's state."""
        self.sidebar_container.setVisible(is_checked)
        self.settings.sidebar_visible = is_checked
        self.settings.save()

    def _on_sidebar_resized(self, pos: int, index: int):
        """Saves the new sidebar splitter position to settings."""
        sizes = self.sidebar_splitter.sizes()
        self.settings.sidebar_split_sizes = sizes
        self.settings.save()

    def _on_mic_selected(self, mic_name: str):
        """Handles microphone selection from the dropdown."""
        if mic_name and mic_name in self.mic_devices:
            mic_index = self.mic_devices[mic_name]
            self.selected_mic_index = mic_index # Store the index
            self.settings.mic_device = mic_name
            self.settings.save()
            self.status_label.setText(f"Using: {mic_name.split('(')[0]}")
            self.mic_ripple_widget.setEnabled(True)

    def _on_toggle_listening(self, is_listening: bool):
        """Starts or stops the verse listener based on the Mic button state."""
        if is_listening:
            self.verse_listener.start_listening(self.verse_queue, self.selected_mic_index)
            self.status_label.setText("Listening...")
            self._show_ai_waiting_state()
        else:
            self.verse_listener.stop_listening()
            self.status_label.setText("Idle")

    def _check_verse_queue(self):
        """Periodically checks the queue for new verses and processes them."""
        try:
            verse_data = self.verse_queue.get_nowait()
            logging.info(f"Dequeued verse data: {verse_data}")

            # Check if this exact verse was recently rejected
            verse_key = self._get_verse_key(verse_data)
            if verse_key in self.rejected_keys:
                logging.warning(f"Skipping recently rejected verse: {verse_key}")
                return

            if self.settings.confirmation_popup:
                popup = VerseConfirmationPopup(verse_data, self)
                popup.finished.connect(lambda approved, data=verse_data: self._on_confirmation_result(approved, data))
                popup.exec()
            else:
                self._process_and_render_verse(verse_data)
        
        except queue.Empty:
            pass # No verse found, continue
        except Exception as e:
            logging.error(f"Error processing verse from queue: {e}", exc_info=True)

    def _on_sidebar_double_click(self, verse_data: dict):
        """Processes a double-click on a verse in either sidebar panel."""
        self._process_and_render_verse(verse_data)

    def _on_sidebar_right_click(self, verse_data: dict, global_pos):
        """Shows a context menu for a verse in the sidebar."""
        menu = QMenu(self)
        
        edit_action = QAction(get_icon("edit"), "Edit Verse", self)
        edit_action.triggered.connect(lambda: self._edit_verse(verse_data))
        menu.addAction(edit_action)

        delete_action = QAction(get_icon("trash"), "Delete Verse", self)
        delete_action.triggered.connect(lambda: self._delete_verse(verse_data))
        menu.addAction(delete_action)

        menu.exec(global_pos)

    def _on_confirmation_result(self, approved: bool, verse_data: dict):
        """Handles the result from the confirmation popup."""
        verse_key = self._get_verse_key(verse_data)
        if approved:
            self._process_and_render_verse(verse_data)
        else:
            # Add to rejected set to prevent it from re-appearing if re-detected
            self.rejected_keys.add(verse_key)
            logging.info(f"Verse '{verse_key}' rejected by user.")
            
            # Optionally remove from queue panel if it was added optimistically
            self.queue_panel.remove_item(verse_key)

    def _update_history_panel(self):
        """Refreshes the history panel from the `live_history` list."""
        self.history_panel.update_items(self.live_history)

    def _process_and_render_verse(self, verse_data: dict):
        """
        Final step to render a verse and update application state.
        This is the definitive "acceptance" of a verse.
        """
        book, chapter, verse = parse_verse_data(verse_data)
        
        # Final validation check before adding to history or displaying
        max_chapters = BOOK_TO_NUM_CHAPTERS.get(book, 0)
        if not max_chapters or chapter > max_chapters:
            logging.warning(
                f"⚠️ Invalid chapter for {book}: "
                f"Book has {max_chapters} chapters, but got {chapter}. Verse rejected."
            )
            return

        verse_key = self._get_verse_key(verse_data)
        
        # --- Add to History ---
        # Avoid adding duplicates to history
        if not any(self._get_verse_key(item) == verse_key for item in self.live_history):
            self.live_history.append(verse_data)
            self._update_history_panel()
        
        # --- Remove from Queue ---
        self.queue_panel.remove_item(verse_key)
        
        # --- Render Slide ---
        self.current_verse_data = verse_data # Track current verse
        self._display_verse(verse_data)

    def _get_verse_key(self, verse_data: dict) -> tuple:
        """Generates a unique, hashable key for a verse."""
        return (verse_data.get('book'), verse_data.get('chapter'), verse_data.get('verse'))

    def _edit_verse(self, original_data: dict):
        """Opens a popup to edit a verse reference."""
        dialog = EditVersePopup(original_data, self)
        if dialog.exec():
            new_data = dialog.get_verse_data()
            if new_data:
                logging.info(f"Editing verse. Original: {original_data}, New: {new_data}")
                
                # Create keys for comparison
                original_key = self._get_verse_key(original_data)
                new_key = self._get_verse_key(new_data)

                # Update history list
                for i, item in enumerate(self.live_history):
                    if self._get_verse_key(item) == original_key:
                        self.live_history[i] = new_data
                        break
                
                # Update queue panel (if it exists there)
                self.queue_panel.remove_item(original_key)
                
                # Re-render if the edited verse was the one being displayed
                if self.current_verse_data and self._get_verse_key(self.current_verse_data) == original_key:
                    self._display_verse(new_data)
                
                self._update_sidebar_panels()

    def _delete_verse(self, verse_data: dict):
        """Deletes a verse from history and queue."""
        key_to_delete = self._get_verse_key(verse_data)
        
        # Add to rejected set to prevent immediate re-detection
        self.rejected_keys.add(key_to_delete)
        
        # Remove from history
        self.live_history = [item for item in self.live_history if self._get_verse_key(item) != key_to_delete]
        
        # Remove from queue
        self.queue_panel.remove_item(key_to_delete)

        # Clear the preview if the deleted verse was showing
        if self.current_verse_data and self._get_verse_key(self.current_verse_data) == key_to_delete:
            self.graphics_scene.clear()
            self.current_verse_data = None

        self._update_sidebar_panels()

    def _update_sidebar_panels(self):
        """Utility to refresh both sidebars."""
        self.history_panel.update_items(self.live_history)

    def get_all_verses_from_sidebar(self) -> list[dict]:
        """Utility to get all unique verses from both queue and history panels."""
        all_verses = {} # Use dict to handle duplicates by key
        
        # We need to access the internal list of verses from each panel
        # This assumes the panels store verses in a 'verses' attribute.
        queue_verses = self.queue_panel.verses if hasattr(self.queue_panel, 'verses') else []
        history_verses = self.history_panel.verses if hasattr(self.history_panel, 'verses') else []

        for v in queue_verses + history_verses:
            key = self._get_verse_key(v)
            if key not in all_verses:
                all_verses[key] = v
        
        return list(all_verses.values())

    def closeEvent(self, event):
        """Ensures graceful shutdown of background services on window close."""
        logging.info("Close event received. Shutting down background services...")
        self.verse_listener.stop_listening()
        logging.info("Services stopped. Closing application.")
        event.accept()

    def _show_about_dialog(self):
        """Displays a simple 'About' dialog."""
        QMessageBox.about(self, "About VersePilot",
                          "VersePilot: Real-time verse detection and display.")

    def _open_settings_dialog(self):
        """Opens the main settings/preferences dialog."""
        # Use a single instance of the settings window
        if not hasattr(self, 'settings_dialog') or not self.settings_dialog:
            self.settings_dialog = SettingsWindow(self)
        
        # Show the dialog modally
        self.settings_dialog.exec()

    def _show_ai_waiting_state(self):
        """Visual feedback when waiting for AI processing."""
        # This method can be expanded for more complex visual state handling.
        self.mic_ripple_widget.set_status(True, "AI_Waiting")


    def _show_confirmation_popup(self, verse_data: dict):
        """Shows the custom confirmation popup for an unverified verse."""
        
        def on_user_decision(confirmed: bool):
            # Pass the result and the original verse data to the handler
            self._handle_confirmation_result(confirmed, verse_data)

        # Create and show the popup
        popup = UserConfirmPopup(verse_data, on_user_decision, self)
        popup.show()
        # Keep a reference to prevent garbage collection
        self.confirmation_buffer.append(popup)

    def _handle_confirmation_result(self, confirmed: bool, verse_data: dict):
        """
        Handles the user's decision from the confirmation popup.
        """
        # Remove the popup from the buffer
        self.confirmation_buffer = [p for p in self.confirmation_buffer if p.verse_data != verse_data]

        verse_key = self._get_verse_key(verse_data)
        if confirmed:
            logging.info(f"User approved displaying potentially invalid verse: {verse_key}")
            # Mark as confirmed and process
            verse_data['validation_status'] = 'user_confirmed'
            self._process_and_render_verse(verse_data)
        else:
            logging.info(f"User rejected displaying potentially invalid verse: {verse_key}")
            # Optionally, add to a rejected list to prevent re-prompting for a while
            self.rejected_keys.add(verse_key)


    def _display_verse(self, verse_data: dict):
        """Renders the selected verse and updates the preview."""
        try:
            book = verse_data.get('book')
            chapter = verse_data.get('chapter')
            verse = verse_data.get('verse')
            
            if not all([book, chapter, verse]):
                logging.warning(f"Attempted to display incomplete verse data: {verse_data}")
                return

            # The new render_slide function returns a QPixmap directly
            pixmap = slide_renderer.render_slide(book, chapter, verse, theme="dark")
            
            if pixmap:
                self.graphics_scene.clear()
                self.graphics_scene.addPixmap(pixmap)
                self.graphics_view.fitInView(self.graphics_scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
            else:
                logging.error("Failed to generate pixmap for verse.")

        except Exception as e:
            logging.error(f"Failed to render verse slide: {e}", exc_info=True)

    def resizeEvent(self, event):
        """Handle window resize to maintain aspect ratio of the content."""
        super().resizeEvent(event)
        self.graphics_view.fitInView(self.graphics_scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        
        # Trigger any layout adjustments needed on resize
        self.central_widget.updateGeometry() 
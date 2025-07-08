from functools import partial
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, 
    QStackedWidget, QButtonGroup, QLabel, QFrame, QToolButton,
    QComboBox, QCheckBox, QSlider, QScrollArea, QPushButton, QDialogButtonBox,
    QLineEdit, QProgressBar
)
from app.qt_ui.resources.icon_provider import get_icon

# --- Helper Dialog for Adding/Editing a Screen ---
class AddScreenDialog(QDialog):
    def __init__(self, screen_data=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Output Screen" if not screen_data else "Edit Output Screen")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Screen Selector (for adding new) or Name (for editing)
        if not screen_data:
            screen_label = QLabel("Select a Display:")
            layout.addWidget(screen_label)
            self.screen_combo = QComboBox()
            # In a real app, this would be populated with actual available screens
            self.screen_combo.addItems(["Display 1 (1920x1080)", "Display 2 (1024x768)"])
            layout.addWidget(self.screen_combo)
        else:
            self.setWindowTitle(f"Edit {screen_data.get('name')}")

        # Resolution
        resolution_label = QLabel("Resolution:")
        layout.addWidget(resolution_label)
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(["1920x1080", "1280x720", "1024x768"])
        layout.addWidget(self.resolution_combo)
        
        # Screen Name Input
        name_label = QLabel("Screen Name:")
        layout.addWidget(name_label)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., Main Display, Side Wall")
        layout.addWidget(self.name_input)

        # Pre-fill data if in edit mode
        if screen_data:
            self.resolution_combo.setCurrentText(screen_data.get("resolution", "1920x1080"))
            self.name_input.setText(screen_data.get("name", ""))
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_data(self) -> dict:
        """Returns the selected data from the dialog's fields."""
        resolution = self.resolution_combo.currentText()
        aspect_ratio = "16:9" # Placeholder
        if resolution == "1024x768":
            aspect_ratio = "4:3"
            
        return {
            "name": self.name_input.text(),
            "resolution": resolution,
            "aspect_ratio": aspect_ratio
        }

class SettingsWindow(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.setMinimumSize(680, 500)
        self.setObjectName("SettingsWindow")

        self.tab_definitions = [
            {"name": "Appearance", "icon": "monitor"},
            {"name": "Output", "icon": "sliders-horizontal"},
            {"name": "Audio", "icon": "waveform"},
            {"name": "Live", "icon": "record_circle"},
            {"name": "Misc", "icon": "gear"},
        ]
        
        # Mock data for screens
        self.screens = [
            {"id": 1, "name": "Main Display", "resolution": "1920x1080", "aspect_ratio": "16:9"},
            {"id": 2, "name": "Side Wall", "resolution": "1280x720", "aspect_ratio": "16:9"},
        ]
        self.next_screen_id = 3

        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.tab_bar_widget = self._create_tab_bar()
        
        self.main_content = QFrame(self)
        self.main_content.setObjectName("MainContentFrame")
        content_layout = QVBoxLayout(self.main_content)
        
        self.stacked_widget = QStackedWidget(self)
        content_layout.addWidget(self.stacked_widget)

        main_layout.addWidget(self.tab_bar_widget)
        main_layout.addWidget(self.main_content, 1)

        self._populate_tabs()

    def _create_tab_bar(self) -> QWidget:
        tab_bar_container = QWidget()
        tab_bar_container.setObjectName("TabBarContainer")
        
        self.tab_bar_layout = QHBoxLayout(tab_bar_container)
        self.tab_bar_layout.setContentsMargins(0, 10, 0, 10)
        self.tab_bar_layout.setSpacing(12)
        self.tab_bar_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        
        return tab_bar_container

    def _populate_tabs(self):
        for idx, tab_info in enumerate(self.tab_definitions):
            button = QToolButton()
            button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            
            icon_color = "#E57373" if tab_info["name"] == "Live" else "white"
            button.setIcon(get_icon(tab_info["icon"], color=icon_color))

            button.setIconSize(QSize(28, 28))
            button.setText(tab_info["name"])
            button.setCheckable(True)
            button.setFixedSize(80, 65)
            
            self.tab_bar_layout.addWidget(button)
            self.button_group.addButton(button, idx)
            
            if tab_info["name"] == "Appearance":
                page = self._create_appearance_tab()
            elif tab_info["name"] == "Output":
                page = self._create_output_tab()
            elif tab_info["name"] == "Audio":
                page = self._create_audio_tab()
            elif tab_info["name"] == "Live":
                page = self._create_live_mode_tab()
            elif tab_info["name"] == "Misc":
                page = self._create_misc_tab()
            else:
                page = self._create_placeholder_tab(tab_info["name"])
            
            self.stacked_widget.addWidget(page)

        self.button_group.idClicked.connect(self.stacked_widget.setCurrentIndex)
        
        if self.button_group.buttons():
            self.button_group.buttons()[0].setChecked(True)

    def _create_appearance_tab(self) -> QWidget:
        """Creates the content widget for the Appearance tab."""
        appearance_tab = QWidget()
        appearance_layout = QVBoxLayout(appearance_tab)
        appearance_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        appearance_layout.setContentsMargins(20, 20, 20, 20)
        appearance_layout.setSpacing(16)

        # === Section Title ===
        title = QLabel("Appearance Settings")
        title.setStyleSheet("color: white; font-size: 18px; font-weight: 600;")
        appearance_layout.addWidget(title)

        # === Theme Mode Dropdown ===
        theme_label = QLabel("Theme Mode")
        theme_label.setStyleSheet("color: #CCCCCC;")
        appearance_layout.addWidget(theme_label)

        theme_dropdown = QComboBox()
        theme_dropdown.addItems(["System Default", "Light Mode", "Dark Mode"])
        theme_dropdown.setStyleSheet("background-color: #3c3c3c; color: white; padding: 6px;")
        appearance_layout.addWidget(theme_dropdown)
        appearance_layout.addWidget(self._create_description_label(
            "Choose how the app’s theme behaves. Use System Default to follow your computer’s light or dark mode."
        ))

        # === Font Size Selector ===
        font_label = QLabel("Font Size")
        font_label.setStyleSheet("color: #CCCCCC;")
        appearance_layout.addWidget(font_label)

        font_dropdown = QComboBox()
        font_dropdown.addItems(["Small", "Medium", "Large"])
        font_dropdown.setStyleSheet("background-color: #3c3c3c; color: white; padding: 6px;")
        appearance_layout.addWidget(font_dropdown)
        appearance_layout.addWidget(self._create_description_label(
            "Adjusts the font size throughout the app for better visibility or compactness."
        ))

        # === Preview Box Settings ===
        preview_title = QLabel("Preview Box")
        preview_title.setStyleSheet("color: white; font-size: 16px; font-weight: 500; margin-top: 12px;")
        appearance_layout.addWidget(preview_title)

        # === Performance dropdown ===
        performance_label = QLabel("Performance")
        performance_label.setStyleSheet("color: #CCCCCC;")
        appearance_layout.addWidget(performance_label)

        performance_dropdown = QComboBox()
        performance_dropdown.addItems([
            "Auto (Recommended)",
            "Low (Less CPU/GPU usage)",
            "Medium",
            "High (Best Quality)"
        ])
        performance_dropdown.setStyleSheet("background-color: #3c3c3c; color: white; padding: 6px;")
        appearance_layout.addWidget(performance_dropdown)
        appearance_layout.addWidget(self._create_description_label(
            "Sets how the preview box balances quality and speed. Auto picks the best setting based on your hardware."
        ))

        # === Preview mode dropdown ===
        mode_label = QLabel("Preview Mode")
        mode_label.setStyleSheet("color: #CCCCCC;")
        appearance_layout.addWidget(mode_label)

        mode_dropdown = QComboBox()
        mode_dropdown.addItems([
            "Basic Preview",
            "Live Preview",
            "Dual Screen (Preview + Live)"
        ])
        mode_dropdown.setStyleSheet("background-color: #3c3c3c; color: white; padding: 6px;")
        appearance_layout.addWidget(mode_dropdown)
        appearance_layout.addWidget(self._create_description_label(
            "Choose the level of detail shown in the preview box. Basic Preview is fastest, while Full may show more effects."
        ))

        appearance_layout.addStretch(1)
        
        return appearance_tab

    def _create_output_tab(self) -> QWidget:
        """Creates the content widget for the Output tab."""
        output_tab = QWidget()
        output_layout = QVBoxLayout(output_tab)
        output_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        output_layout.setContentsMargins(20, 20, 20, 20)
        output_layout.setSpacing(16)

        # === Section Title ===
        title = QLabel("Output Settings")
        title.setStyleSheet("color: white; font-size: 18px; font-weight: 600;")
        output_layout.addWidget(title)

        # === Slide Resolution Dropdown ===
        resolution_label = QLabel("Slide Resolution")
        resolution_label.setStyleSheet("color: #CCCCCC;")
        output_layout.addWidget(resolution_label)
        resolution_dropdown = QComboBox()
        resolution_dropdown.addItems([
            "1280×720 (HD)", "1920×1080 (Full HD)", "2560×1440 (2K)", "3840×2160 (4K)"
        ])
        resolution_dropdown.setStyleSheet("background-color: #3c3c3c; color: white; padding: 6px;")
        output_layout.addWidget(resolution_dropdown)
        output_layout.addWidget(self._create_description_label(
            "Choose the resolution for slide output. Match this to your projector or display for the best quality."
        ))

        # === Text Smoothing Checkbox ===
        smoothing_checkbox = QCheckBox("Enable Text Smoothing")
        smoothing_checkbox.setStyleSheet("color: white; margin-top: 12px;")
        output_layout.addWidget(smoothing_checkbox)
        output_layout.addWidget(self._create_description_label(
            "Renders text with anti-aliasing to reduce jagged edges and improve clarity."
        ))

        # === Active Screens Section ===
        screens_title = QLabel("Active Screens")
        screens_title.setStyleSheet("color: white; font-size: 16px; font-weight: 500; margin-top: 20px;")
        output_layout.addWidget(screens_title)

        # Scrollable container for screen cards
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setObjectName("ScreenScrollArea")
        scroll_area.setFixedHeight(200)

        scroll_content = QWidget()
        self.screens_layout = QVBoxLayout(scroll_content)
        self.screens_layout.setSpacing(10)
        self.screens_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll_area.setWidget(scroll_content)
        output_layout.addWidget(scroll_area)

        # === Add Screen Button ===
        add_screen_button = QPushButton("+ Add Screen")
        add_screen_button.setObjectName("AddScreenButton")
        add_screen_button.setFixedSize(120, 32)
        add_screen_button.clicked.connect(self._on_add_screen)
        
        button_container = QHBoxLayout()
        button_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        button_container.addWidget(add_screen_button)
        output_layout.addLayout(button_container)
        output_layout.addWidget(self._create_description_label(
            "Set up a new projector or monitor for displaying slides."
        ))
        
        output_layout.addStretch(1)

        # Initial population of the screen list
        self._refresh_screen_list()

        return output_tab

    def _refresh_screen_list(self):
        """Clears and re-populates the list of screen cards from self.screens."""
        # Clear existing widgets
        while self.screens_layout.count():
            child = self.screens_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Re-populate from the data model
        for screen_data in self.screens:
            card = self._create_screen_card(screen_data)
            self.screens_layout.addWidget(card)

    def _on_add_screen(self):
        """Handles the 'Add Screen' button click."""
        dialog = AddScreenDialog(parent=self)
        if dialog.exec():
            new_data = dialog.get_data()
            new_name = new_data["name"] if new_data["name"] else f"Screen {self.next_screen_id}"
            
            new_screen = {
                "id": self.next_screen_id,
                "name": new_name,
                "resolution": new_data["resolution"],
                "aspect_ratio": new_data["aspect_ratio"],
            }
            self.screens.append(new_screen)
            self.next_screen_id += 1
            self._refresh_screen_list()

    def _on_edit_screen(self, screen_data: dict):
        """Handles the 'Edit' button click for a screen card."""
        dialog = AddScreenDialog(screen_data=screen_data, parent=self)
        if dialog.exec():
            updated_data = dialog.get_data()
            # Don't allow an empty name on edit; keep the old one if cleared.
            if not updated_data["name"]:
                del updated_data["name"]

            # Find and update the screen in the list
            for i, screen in enumerate(self.screens):
                if screen["id"] == screen_data["id"]:
                    self.screens[i].update(updated_data)
                    break
            self._refresh_screen_list()

    def _on_remove_screen(self, screen_data: dict):
        """Handles the 'Remove' button click for a screen card."""
        self.screens = [s for s in self.screens if s["id"] != screen_data["id"]]
        self._refresh_screen_list()

    def _create_screen_card(self, screen_data: dict) -> QWidget:
        """Creates a styled card widget for a single output screen."""
        card = QFrame()
        card.setObjectName("ScreenCard")
        card.setFrameShape(QFrame.Shape.StyledPanel)
        
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(12, 8, 8, 8) # L, T, R, B
        
        # Left side: Info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        name_label = QLabel(screen_data["name"])
        name_label.setStyleSheet("font-weight: 500; color: white;")
        info_label = QLabel(f"{screen_data['resolution']} ({screen_data['aspect_ratio']})")
        info_label.setStyleSheet("color: #AAAAAA;")
        info_layout.addWidget(name_label)
        info_layout.addWidget(info_label)
        
        card_layout.addLayout(info_layout, 1) # Add with stretch

        # Right side: Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        button_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        edit_button = QPushButton("Edit")
        edit_button.setFixedSize(60, 30)
        edit_button.setObjectName("CardEditButton")

        remove_button = QPushButton()
        remove_button.setIcon(get_icon("trash"))
        remove_button.setToolTip("Remove this screen")
        remove_button.setFixedSize(30, 30)
        remove_button.setObjectName("CardRemoveButton")

        # Connect buttons to handlers, passing the specific screen's data
        edit_button.clicked.connect(partial(self._on_edit_screen, screen_data))
        remove_button.clicked.connect(partial(self._on_remove_screen, screen_data))

        button_layout.addWidget(edit_button)
        button_layout.addWidget(remove_button)

        card_layout.addLayout(button_layout)

        return card

    def _create_audio_tab(self) -> QWidget:
        """Creates the content widget for the Audio tab."""
        audio_tab = QWidget()
        self.audio_layout = QVBoxLayout(audio_tab)
        self.audio_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.audio_layout.setContentsMargins(20, 20, 20, 20)
        self.audio_layout.setSpacing(8)

        # === Section Title ===
        title = QLabel("Audio Settings")
        title.setStyleSheet("color: white; font-size: 18px; font-weight: 600; margin-bottom: 10px;")
        self.audio_layout.addWidget(title)
        
        # --- Active Audio Input ---
        active_input_label = QLabel("Active Audio Input")
        active_input_label.setStyleSheet("color: #CCCCCC;")
        self.audio_layout.addWidget(active_input_label)
        self.active_input_combo = QComboBox()
        self.active_input_combo.addItems(["System Audio (Default)", "Dante Network Audio"])
        self.active_input_combo.setStyleSheet("background-color: #3c3c3c; color: white; padding: 6px;")
        self.active_input_combo.currentIndexChanged.connect(self._on_active_audio_source_changed)
        self.audio_layout.addWidget(self.active_input_combo)

        # --- Dante Network Audio Group ---
        self.dante_group = QWidget()
        dante_layout = QVBoxLayout(self.dante_group)
        dante_layout.setContentsMargins(0, 10, 0, 0)
        dante_layout.setSpacing(8)
        
        dante_title = QLabel("Dante Network Audio")
        dante_title.setStyleSheet("color: white; font-size: 16px; font-weight: 500;")
        dante_layout.addWidget(dante_title)
        
        dante_interface_label = QLabel("Dante Interface")
        dante_interface_label.setStyleSheet("color: #CCCCCC;")
        dante_layout.addWidget(dante_interface_label)
        dante_interface_dropdown = QComboBox()
        dante_interface_dropdown.addItems(["None", "Ethernet 1", "Wi-Fi"])
        dante_interface_dropdown.setStyleSheet("background-color: #3c3c3c; color: white; padding: 6px;")
        dante_layout.addWidget(dante_interface_dropdown)
        dante_layout.addWidget(self._create_description_label("Select which network interface will carry Dante audio."))
        self.audio_layout.addWidget(self.dante_group)

        # --- Audio Behavior ---
        behavior_title = QLabel("Audio Behavior")
        behavior_title.setStyleSheet("color: white; font-size: 16px; font-weight: 500; margin-top: 20px;")
        self.audio_layout.addWidget(behavior_title)
        
        lock_mic_checkbox = QCheckBox("Lock Preferred Mic Setup")
        lock_mic_checkbox.setStyleSheet("color: white;")
        self.audio_layout.addWidget(lock_mic_checkbox)
        self.audio_layout.addWidget(self._create_description_label("Keeps your current input locked across restarts. If unavailable, will auto-reconnect once it comes back online."))

        normalization_checkbox = QCheckBox("Enable Input Normalization")
        normalization_checkbox.setStyleSheet("color: white;")
        self.audio_layout.addWidget(normalization_checkbox)
        self.audio_layout.addWidget(self._create_description_label("Levels out mic volume to avoid sudden spikes or dips."))
        
        monitoring_checkbox = QCheckBox("Enable Audio Monitoring")
        monitoring_checkbox.setStyleSheet("color: white;")
        self.audio_layout.addWidget(monitoring_checkbox)
        self.audio_layout.addWidget(self._create_description_label("Listens to your mic through speakers or headphones for testing."))

        # --- Mic Test Section ---
        mic_test_title = QLabel("Mic Test")
        mic_test_title.setStyleSheet("color: white; font-size: 16px; font-weight: 500; margin-top: 20px;")
        self.audio_layout.addWidget(mic_test_title)

        self.mic_test_button = QPushButton("Start Mic Test")
        self.mic_test_button.setCheckable(True)
        self.mic_test_button.setFixedWidth(120)
        self.audio_layout.addWidget(self.mic_test_button)

        self.mic_level_bar = QProgressBar()
        self.mic_level_bar.setRange(0, 100)
        self.mic_level_bar.setValue(0)
        self.mic_level_bar.setTextVisible(False)
        self.mic_level_bar.setFixedHeight(10)
        self.audio_layout.addWidget(self.mic_level_bar)

        self.audio_layout.addStretch(1)
        
        # Set initial visibility state
        self._on_active_audio_source_changed(0)
        
        return audio_tab

    def _on_active_audio_source_changed(self, index):
        """Shows or hides audio source sections based on dropdown selection."""
        selected_text = self.active_input_combo.itemText(index)
        is_dante = (selected_text == "Dante Network Audio")
        self.dante_group.setVisible(is_dante)

    def _create_misc_tab(self) -> QWidget:
        """Creates the content widget for the Misc tab."""
        misc_tab = QWidget()
        misc_layout = QVBoxLayout(misc_tab)
        misc_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        misc_layout.setContentsMargins(20, 20, 20, 20)
        misc_layout.setSpacing(8)

        # === Section: Startup Behavior ===
        startup_title = QLabel("Startup Behavior")
        startup_title.setStyleSheet("color: white; font-size: 16px; font-weight: 500; margin-bottom: 5px;")
        misc_layout.addWidget(startup_title)

        auto_launch_checkbox = QCheckBox("Auto-Launch on Boot")
        auto_launch_checkbox.setStyleSheet("color: white;")
        misc_layout.addWidget(auto_launch_checkbox)
        misc_layout.addWidget(self._create_description_label("Launch VersePilot automatically when the computer starts."))

        start_mic_active_checkbox = QCheckBox("Start with Mic Active")
        start_mic_active_checkbox.setStyleSheet("color: white;")
        misc_layout.addWidget(start_mic_active_checkbox)
        misc_layout.addWidget(self._create_description_label("Automatically enable verse detection when the app launches."))

        auto_restore_checkbox = QCheckBox("Auto-Restore Last Session")
        auto_restore_checkbox.setStyleSheet("color: white;")
        misc_layout.addWidget(auto_restore_checkbox)
        misc_layout.addWidget(self._create_description_label("Reload the previous screen setup, history, and queue on startup."))

        # === Section: Auto-Clear ===
        autoclear_title = QLabel("Auto-Clear")
        autoclear_title.setStyleSheet("color: white; font-size: 16px; font-weight: 500; margin-top: 20px; margin-bottom: 5px;")
        misc_layout.addWidget(autoclear_title)
        
        autoclear_toggle = QCheckBox("Auto-Clear Slide After Timeout")
        autoclear_toggle.setStyleSheet("color: white;")
        misc_layout.addWidget(autoclear_toggle)
        misc_layout.addWidget(self._create_description_label("Remove the current verse from the screen after a set number of seconds."))

        timeout_duration_widget = QWidget()
        timeout_layout = QHBoxLayout(timeout_duration_widget)
        timeout_layout.setContentsMargins(15, 0, 0, 0)
        timeout_label = QLabel("Timeout Duration:")
        timeout_dropdown = QComboBox()
        timeout_dropdown.addItems(["5s", "10s", "15s", "30s", "60s"])
        timeout_layout.addWidget(timeout_label)
        timeout_layout.addWidget(timeout_dropdown)
        timeout_layout.addStretch()
        misc_layout.addWidget(timeout_duration_widget)
        timeout_duration_widget.setVisible(False)
        autoclear_toggle.toggled.connect(timeout_duration_widget.setVisible)

        # === Section: Reset / Logs ===
        reset_title = QLabel("Reset / Logs")
        reset_title.setStyleSheet("color: white; font-size: 16px; font-weight: 500; margin-top: 20px; margin-bottom: 5px;")
        misc_layout.addWidget(reset_title)

        # Create a horizontal layout for the buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        button_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        clear_cache_button = QPushButton("Clear Cache")
        clear_cache_button.setObjectName("SecondaryButton")
        clear_cache_button.setFixedHeight(32)
        
        view_logs_button = QPushButton("View Logs")
        view_logs_button.setObjectName("SecondaryButton")
        view_logs_button.setFixedHeight(32)

        reset_app_button = QPushButton("Reset App")
        reset_app_button.setObjectName("ResetButton")
        reset_app_button.setFixedHeight(32)
        
        button_layout.addWidget(clear_cache_button)
        button_layout.addWidget(view_logs_button)
        button_layout.addStretch(1) # Add a spacer to push the reset button to the right if needed, or remove for left alignment.
        button_layout.addWidget(reset_app_button)
        
        misc_layout.addLayout(button_layout)

        misc_layout.addStretch(1)
        return misc_tab

    def _create_live_mode_tab(self) -> QWidget:
        """Creates the content widget for the Live Mode tab."""
        live_tab = QWidget()
        live_layout = QVBoxLayout(live_tab)
        live_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        live_layout.setContentsMargins(20, 20, 20, 20)
        live_layout.setSpacing(8)

        # === Section Title ===
        title = QLabel("Live")
        title.setStyleSheet("color: white; font-size: 18px; font-weight: 600; margin-bottom: 10px;")
        live_layout.addWidget(title)

        # --- Live Behavior Group ---
        live_behavior_title = QLabel("Live Behavior")
        live_behavior_title.setStyleSheet("color: white; font-size: 16px; font-weight: 500; margin-top: 12px;")
        live_layout.addWidget(live_behavior_title)

        add_ref_checkbox = QCheckBox("Add Verse Reference to Slide")
        add_ref_checkbox.setStyleSheet("color: white;")
        live_layout.addWidget(add_ref_checkbox)
        live_layout.addWidget(self._create_description_label(
            "Include the verse reference (e.g. John 3:16) at the bottom of each slide."
        ))

        auto_push_checkbox = QCheckBox("Auto Push to Live Screen")
        auto_push_checkbox.setStyleSheet("color: white;")
        live_layout.addWidget(auto_push_checkbox)
        live_layout.addWidget(self._create_description_label(
            "Automatically show each new verse slide without manual confirmation."
        ))

        delay_label = QLabel("Auto Push Delay")
        delay_label.setStyleSheet("color: #CCCCCC;")
        live_layout.addWidget(delay_label)
        delay_dropdown = QComboBox()
        delay_dropdown.addItems(["None", "2s", "5s", "10s"])
        delay_dropdown.setStyleSheet("background-color: #3c3c3c; color: white; padding: 6px;")
        live_layout.addWidget(delay_dropdown)
        live_layout.addWidget(self._create_description_label(
             "Wait this long before automatically showing a new slide."
        ))
        
        start_live_checkbox = QCheckBox("Start in Live Mode")
        start_live_checkbox.setStyleSheet("color: white;")
        live_layout.addWidget(start_live_checkbox)
        live_layout.addWidget(self._create_description_label(
            "Automatically open in Live view instead of Preview view on app launch."
        ))

        go_live_confirm_checkbox = QCheckBox("Show 'Go Live' Confirmation")
        go_live_confirm_checkbox.setStyleSheet("color: white;")
        live_layout.addWidget(go_live_confirm_checkbox)
        live_layout.addWidget(self._create_description_label(
            "Ask for confirmation before pushing a verse slide to the live screen."
        ))

        # --- Startup Behavior Group ---
        startup_title = QLabel("Startup Behavior")
        startup_title.setStyleSheet("color: white; font-size: 16px; font-weight: 500; margin-top: 20px;")
        live_layout.addWidget(startup_title)

        launch_startup_checkbox = QCheckBox("Launch on System Startup")
        launch_startup_checkbox.setStyleSheet("color: white;")
        live_layout.addWidget(launch_startup_checkbox)
        live_layout.addWidget(self._create_description_label(
            "Start VersePilot automatically when the computer boots."
        ))

        autoload_checkbox = QCheckBox("Auto-load Last Screen Setup")
        autoload_checkbox.setStyleSheet("color: white;")
        live_layout.addWidget(autoload_checkbox)
        live_layout.addWidget(self._create_description_label(
            "Restore previously used output screens and settings at launch."
        ))
        
        start_mode_label = QLabel("Start in Mode")
        start_mode_label.setStyleSheet("color: #CCCCCC;")
        live_layout.addWidget(start_mode_label)
        start_mode_dropdown = QComboBox()
        start_mode_dropdown.addItems(["Preview", "Live"])
        start_mode_dropdown.setStyleSheet("background-color: #3c3c3c; color: white; padding: 6px;")
        live_layout.addWidget(start_mode_dropdown)
        live_layout.addWidget(self._create_description_label(
            "Choose whether the app starts in Preview or Live mode."
        ))
        
        live_layout.addStretch(1)

        return live_tab

    def _create_description_label(self, text: str) -> QLabel:
        """Creates a styled description label for settings."""
        label = QLabel(text)
        label.setWordWrap(True)
        label.setStyleSheet("""
            color: #9E9E9E;
            font-size: 11px;
            font-style: italic;
            padding-left: 15px;
            padding-bottom: 10px;
        """)
        return label

    def _create_placeholder_tab(self, name: str) -> QWidget:
        """Creates a generic, empty widget for a tab."""
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label = QLabel(f"{name} Settings Coming Soon")
        label.setObjectName("PlaceholderLabel")
        page_layout.addWidget(label)
        return page

    def _apply_styles(self):
        self.setStyleSheet("""
            SettingsWindow#SettingsWindow {
                background-color: #2e2e2e;
            }
            #TabBarContainer {
                background-color: #262626;
                border-bottom: 1px solid #404040;
            }
            #MainContentFrame {
                background-color: #2e2e2e;
                border: none;
            }
            #PlaceholderLabel {
                color: #808080;
                font-size: 16px;
            }
            #ScreenScrollArea {
                background-color: #252525;
                border: 1px solid #404040;
                border-radius: 8px;
            }
            #ScreenCard {
                background-color: #383838;
                border-radius: 6px;
                padding: 8px;
            }
            #CardEditButton, #CardRemoveButton {
                background-color: #4a4a4a;
                border: none;
                border-radius: 6px;
                color: white;
            }
            #CardEditButton:hover {
                background-color: #555555;
            }
            #CardRemoveButton {
                /* Icon color is set in the get_icon call */
            }
            #CardRemoveButton:hover {
                background-color: #8b3a3a;
            }
            #AddScreenButton {
                background-color: #3a3a3a;
                color: white;
                border: 1px solid #555;
                border-radius: 8px;
                font-weight: 500;
            }
            #AddScreenButton:hover {
                background-color: #4a4a4a;
            }
            #ResetButton {
                background-color: #5a2a2a;
                color: #ffcdd2;
                border: 1px solid #8b3a3a;
                border-radius: 6px;
                padding: 0 12px;
            }
            #ResetButton:hover {
                background-color: #a14444;
                color: white;
            }
            #SecondaryButton {
                background-color: #4a4a4a;
                border: 1px solid #5f5f5f;
                border-radius: 6px;
                color: white;
                padding: 0 12px;
            }
            #SecondaryButton:hover {
                background-color: #555555;
            }
            QToolButton {
                border: none;
                background: transparent;
                color: white;
                padding-top: 4px;
                font-size: 10px;
            }
            QToolButton:hover {
                background-color: rgba(255, 255, 255, 0.05);
                border-radius: 8px;
            }
            QToolButton:checked {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 12px;
            }
        """)

    def exec(self):
        return super().exec() 
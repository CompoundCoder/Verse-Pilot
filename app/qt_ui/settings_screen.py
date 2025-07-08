import logging
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QGroupBox, QFormLayout, QComboBox, QCheckBox,
    QPushButton, QDialogButtonBox, QLabel
)
from app.core.settings.settings_model import SettingsModel
from app.core.audio.audio_devices import get_audio_devices

class SettingsScreen(QDialog):
    def __init__(self, settings: SettingsModel, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Settings")
        self.setMinimumWidth(400)

        # --- Main Layout ---
        layout = QVBoxLayout(self)
        
        # --- Microphone Settings ---
        mic_group = QGroupBox("Microphone")
        mic_layout = QFormLayout(mic_group)
        self.mic_combo = QComboBox()
        self.populate_mic_devices()
        mic_layout.addRow("Input Device:", self.mic_combo)
        layout.addWidget(mic_group)

        # --- AI Settings ---
        ai_group = QGroupBox("AI Configuration")
        ai_layout = QFormLayout(ai_group)
        self.online_ai_checkbox = QCheckBox("Use Online AI (Groq)")
        self.online_ai_checkbox.setToolTip("When checked, uses the Groq API for verse detection.")
        ai_layout.addRow(self.online_ai_checkbox)
        layout.addWidget(ai_group)

        # --- Dialog Buttons ---
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self._load_settings_to_ui()

    def populate_mic_devices(self):
        """Fills the microphone dropdown with available devices."""
        devices = get_audio_devices()
        for i, device in enumerate(devices):
            self.mic_combo.addItem(device["name"], userData=i)
        
    def _load_settings_to_ui(self):
        """Loads settings from the model and applies them to the UI widgets."""
        logging.debug("Loading settings into SettingsScreen UI.")
        idx = self.mic_combo.findData(self.settings.mic_device)
        self.mic_combo.setCurrentIndex(idx if idx != -1 else 0)
        self.online_ai_checkbox.setChecked(self.settings.use_online_ai)

    def _save_settings_from_ui(self):
        """Saves the current state of the UI widgets back to the settings model."""
        logging.debug("Saving settings from SettingsScreen UI.")
        self.settings.mic_device = self.mic_combo.currentData()
        self.settings.use_online_ai = self.online_ai_checkbox.isChecked()
        self.settings.save()
        logging.info("Settings saved successfully.")

    def accept(self):
        """Override accept to save settings before closing."""
        self._save_settings_from_ui()
        super().accept() 
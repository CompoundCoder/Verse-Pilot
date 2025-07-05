import json
import os
import logging
from typing import Optional

# --- Constants ---
# Defines the filename for storing application settings.
SETTINGS_FILE = "versepilot_settings.json"

# --- Setup logging ---
log = logging.getLogger(__name__)

# --- Singleton instance ---
# This holds the single instance of the SettingsModel to ensure that
# all parts of the application are using the same settings state.
_settings_instance: Optional['SettingsModel'] = None

class SettingsModel:
    """
    Manages application settings, including loading from and saving to a JSON file.

    This class provides a centralized way to access and modify user preferences.
    Changes to properties are immediately persisted to disk to ensure they are
    not lost between sessions.
    """
    def __init__(self):
        # // Sets default values for all settings.
        # // These are used if the settings file doesn't exist or a key is missing.
        self._defaults = {
            "require_approval": True,
            "confidence_threshold": 0.6,
            "auto_show_after_delay": True,
            "auto_show_delay_seconds": 30,
            "sidebar_visible": True
        }
        # // Loads the settings from disk when the model is initialized.
        self._settings = self._load()

    def _load(self) -> dict:
        """Loads settings from the JSON file."""
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r') as f:
                    settings = json.load(f)
                    # // Ensure all keys from defaults are present
                    for key, value in self._defaults.items():
                        settings.setdefault(key, value)
                    return settings
            except (json.JSONDecodeError, IOError) as e:
                log.error(f"Error loading settings file: {e}. Using default settings.")
                return self._defaults.copy()
        # // If the file does not exist, return a copy of the defaults.
        return self._defaults.copy()

    def _save(self):
        """Saves the current settings to the JSON file."""
        try:
            with open(SETTINGS_FILE, 'w') as f:
                # // The `indent=4` argument makes the JSON file human-readable.
                json.dump(self._settings, f, indent=4)
        except IOError as e:
            log.error(f"Error saving settings: {e}")

    # --- Properties for accessing settings ---
    # Each property uses a getter and a setter. The setter automatically
    # calls `_save()` to persist the change immediately.

    @property
    def require_approval(self) -> bool:
        return self._settings.get("require_approval", self._defaults["require_approval"])

    @require_approval.setter
    def require_approval(self, value: bool):
        self._settings["require_approval"] = value
        self._save()

    @property
    def confidence_threshold(self) -> float:
        return self._settings.get("confidence_threshold", self._defaults["confidence_threshold"])

    @confidence_threshold.setter
    def confidence_threshold(self, value: float):
        self._settings["confidence_threshold"] = value
        self._save()

    @property
    def auto_show_after_delay(self) -> bool:
        return self._settings.get("auto_show_after_delay", self._defaults["auto_show_after_delay"])

    @auto_show_after_delay.setter
    def auto_show_after_delay(self, value: bool):
        self._settings["auto_show_after_delay"] = value
        self._save()

    @property
    def auto_show_delay_seconds(self) -> int:
        return self._settings.get("auto_show_delay_seconds", self._defaults["auto_show_delay_seconds"])

    @auto_show_delay_seconds.setter
    def auto_show_delay_seconds(self, value: int):
        self._settings["auto_show_delay_seconds"] = value
        self._save()

    @property
    def sidebar_visible(self) -> bool:
        return self._settings.get("sidebar_visible", self._defaults["sidebar_visible"])

    @sidebar_visible.setter
    def sidebar_visible(self, value: bool):
        self._settings["sidebar_visible"] = value
        self._save()

def get_settings() -> SettingsModel:
    """
    Provides access to the singleton SettingsModel instance.

    This function ensures that only one instance of the settings model is
    created and used throughout the application, preventing state conflicts.
    """
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = SettingsModel()
    return _settings_instance 
import json
import logging as log

DEFAULTS = {
    "mic_device": "default",
    "theme": "dark",
    "sidebar_split_sizes": [250, 450],
    "use_online_ai": True,
    "sidebar_visible": True,
    "require_approval": False,
    "confidence_threshold": 0.75,
    "confirmation_popup": False,  # Added safe default
}

SETTINGS_FILE = "settings.json"

class SettingsModel:
    """
    A class to hold application settings, ensuring type safety and
    providing a structured way to manage configuration. It loads from a JSON
    file on initialization and saves back to the file on request.
    """
    def __init__(self):
        """Loads settings from disk after the object is initialized."""
        self._load()

    def save(self):
        """Saves all current settings to the JSON file."""
        settings_to_save = self.to_dict()
        try:
            with open(SETTINGS_FILE, "w") as f:
                json.dump(settings_to_save, f, indent=4)
            log.debug(f"Settings saved to {SETTINGS_FILE}")
        except IOError as e:
            log.error(f"Error saving settings to {SETTINGS_FILE}: {e}")

    def _load(self):
        """Loads settings from the JSON file, applying defaults for missing keys."""
        needs_save = False
        try:
            with open(SETTINGS_FILE, "r") as f:
                settings_dict = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            log.info(f"'{SETTINGS_FILE}' not found or invalid. Using default settings.")
            settings_dict = {}
            needs_save = True # Ensure a default file is created

        # Dynamically assign attributes using DEFAULTS as the source of truth
        for key, default_value in DEFAULTS.items():
            value = settings_dict.get(key, default_value)
            setattr(self, key, value)
            # If a key was missing from the file, add it for the next save
            if key not in settings_dict:
                settings_dict[key] = default_value
                needs_save = True

        # If any keys were missing, save the updated settings file
        if needs_save:
            self.save()

    def restore_defaults(self):
        """Resets all settings to their default values."""
        for key, value in DEFAULTS.items():
            setattr(self, key, value)
        log.info("Settings restored to default values.")
        self.save()

    def to_dict(self):
        """Converts the settings to a dictionary, using DEFAULTS for keys."""
        return {key: getattr(self, key) for key in DEFAULTS}

# --- Singleton Instance Provider ---

_settings_instance: SettingsModel | None = None

def get_settings() -> SettingsModel:
    """
    Provides a global singleton instance of the SettingsModel.
    
    This ensures that all parts of the application share the same settings object,
    maintaining a consistent state. It creates the instance on the first call
    and returns the existing instance on subsequent calls.
    """
    global _settings_instance
    if _settings_instance is None:
        log.info("Creating new global SettingsModel instance.")
        _settings_instance = SettingsModel()
    return _settings_instance 
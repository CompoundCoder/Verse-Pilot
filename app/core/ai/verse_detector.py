import logging
from app.core.ai.detectors.online_groq import OnlineGroqDetector
from app.core.settings.settings_model import get_settings

class VerseDetector:
    def __init__(self):
        self.online_detector = OnlineGroqDetector()
        self.settings = get_settings()
        self.last_detector_used = None

    def detect(self, transcript: str) -> dict | None:
        """
        Performs verse detection using the online detector if enabled in settings.
        """
        if not self.settings.use_online_ai:
            logging.info("[VerseDetector] Online AI is disabled in settings. Skipping detection.")
            self.last_detector_used = None
            return None

        if not self.online_detector.is_available():
            logging.warning("[VerseDetector] Online AI is enabled, but Groq is not available. No detection possible.")
            self.last_detector_used = None
            return None
        
        try:
            logging.info("[VerseDetector] Using online Groq detector.")
            self.last_detector_used = "online"
            return self._safe_detect(self.online_detector, transcript)
        except Exception as e:
            logging.error(f"[VerseDetector] CRITICAL: Unhandled exception during detection: {e}", exc_info=True)
            self.last_detector_used = None
            return None

    def _safe_detect(self, detector, transcript: str) -> dict | None:
        """
        Safely calls the online detector's detect method, handling exceptions.
        """
        try:
            return detector.detect(transcript)
        except Exception as e:
            logging.error(f"[VerseDetector] Online detector failed: {e}", exc_info=True)
            return None

    def get_active_backend(self) -> str | None:
        """Returns the name of the active backend."""
        if self.settings.use_online_ai and self.is_backend_ready("online"):
            return "online"
        return None

    def is_backend_ready(self, name: str) -> bool:
        """Returns True if the specified backend is available."""
        if name == "online":
            return self.online_detector and self.online_detector.is_available()
        return False

    def get_available_backends(self) -> list[str]:
        """Returns a list of all currently available backend names."""
        if self.is_backend_ready("online"):
            return ["online"]
        return [] 
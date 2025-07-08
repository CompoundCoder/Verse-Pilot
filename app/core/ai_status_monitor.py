from PyQt6.QtCore import QObject, pyqtSignal
import time
import logging

class AIStatusMonitor(QObject):
    """
    Monitors the VerseDetector's backend status and emits signals for the UI.
    """
    status_updated = pyqtSignal(str)  # "green", "yellow", "red"
    backend_changed = pyqtSignal(str) # "local", "online", or ""

    def __init__(self, detector, check_interval=2):
        super().__init__()
        self.detector = detector
        self.check_interval = check_interval
        self._running = True
        self._last_backend = None
        self._last_status = None

    def stop(self):
        """Signals the monitoring loop to terminate."""
        self._running = False
        logging.info("AI Status Monitor stop signal received.")

    def run(self):
        """
        The main loop for the monitoring thread. Periodically checks the
        VerseDetector's state and emits status updates.
        """
        logging.info("AI Status Monitor started, now checking detector state.")
        while self._running:
            try:
                # Check which backends are working
                local_ready = self.detector.is_backend_ready("local")
                online_ready = self.detector.is_backend_ready("online")
                active_backend = self.detector.get_active_backend() or ""

                # Emit backend change signal if it has changed
                if active_backend != self._last_backend:
                    self.backend_changed.emit(active_backend)
                    self._last_backend = active_backend

                # Determine and emit color status
                current_status = "red"
                if local_ready or online_ready:
                    # Yellow means a backend is ready, but none have been used yet.
                    # Green means a backend has been successfully used.
                    current_status = "green" if active_backend else "yellow"

                if current_status != self._last_status:
                    self.status_updated.emit(current_status)
                    self._last_status = current_status

            except Exception as e:
                logging.warning(f"[AIStatusMonitor] Error checking backend status: {e}")
                if self._last_status != "red":
                    self.status_updated.emit("red")
                    self._last_status = "red"

            # Responsive sleep that respects the stop signal
            for _ in range(self.check_interval * 4):
                if not self._running:
                    break
                time.sleep(0.25)
        
        logging.info("AI Status Monitor thread finished.") 
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QTimer, QSize
from typing import Callable
from app.qt_ui.resources.icon_provider import get_icon

class VerseConfirmationPopup(QDialog):
    """
    A modal popup to confirm or reject a low-confidence verse, with a timeout.
    """
    def __init__(
        self,
        verse_data: dict,
        timeout_duration_s: int,
        auto_approve: bool,
        parent=None
    ):
        super().__init__(parent)

        self.verse_data = verse_data
        self._auto_approve_enabled = auto_approve
        self.seconds_left = timeout_duration_s

        # --- Window Configuration ---
        self.setWindowTitle("Confirm Verse")
        self.setMinimumWidth(350)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        # --- Layouts ---
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        button_layout = QHBoxLayout()

        # --- Widgets ---
        main_label = QLabel("Low confidence detection. Show this verse?")
        main_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_label.setStyleSheet("font-size: 14pt; font-weight: bold;")

        ref_text = f"{verse_data.get('book')} {verse_data.get('chapter')}:{verse_data.get('verse')}"
        conf_text = f"Confidence: {verse_data.get('confidence', 0.0):.2%}"
        verse_label = QLabel(f"{ref_text} ({conf_text})")
        verse_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.timer_label = QLabel()
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_label.setStyleSheet("color: #888;")

        self.approve_button = QPushButton("Approve")
        self.approve_button.setIcon(get_icon("check"))
        self.approve_button.setIconSize(QSize(16, 16))
        self.approve_button.setObjectName("primaryButton")
        self.approve_button.clicked.connect(self.accept)
        self.approve_button.setDefault(True)

        self.reject_button = QPushButton("Reject")
        self.reject_button.setIcon(get_icon("xmark"))
        self.reject_button.setIconSize(QSize(16, 16))
        self.reject_button.setObjectName("destructiveButton")
        self.reject_button.clicked.connect(self.reject)

        button_layout.addWidget(self.reject_button)
        button_layout.addStretch(1)
        button_layout.addWidget(self.approve_button)

        layout.addWidget(main_label)
        layout.addWidget(verse_label)
        layout.addWidget(self.timer_label)
        layout.addLayout(button_layout)

        # --- Timer ---
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_timer)
        self.timer.start(1000)
        self._update_timer() # Initial call to set text immediately

    def _update_timer(self):
        """Countdown logic, called every second."""
        if self.seconds_left > 0:
            self.timer_label.setText(f"Auto-processing in {self.seconds_left}s...")
            self.seconds_left -= 1
        else:
            self.timer.stop()
            if self._auto_approve_enabled:
                self.accept()
            else:
                self.reject()
    
    def accept(self):
        """Stops timer on manual approval."""
        self.timer.stop()
        super().accept()

    def reject(self):
        """Stops timer on manual rejection."""
        self.timer.stop()
        super().reject() 
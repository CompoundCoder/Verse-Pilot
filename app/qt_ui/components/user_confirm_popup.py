import sys
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QApplication
)
from PyQt6.QtCore import QTimer, Qt, pyqtSignal

class UserConfirmPopup(QDialog):
    """
    A dialog that asks the user to confirm an action, with an auto-dismiss timer.
    """
    def __init__(self, book: str, chapter: int, verse: int, callback, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Confirm Verse")
        self.setModal(True)
        
        self.book = book
        self.chapter = chapter
        self.verse = verse
        self.callback = callback

        # --- Layout ---
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # --- Message ---
        message = (
            f"Show <b>‘{self.book} {self.chapter}:{self.verse}’</b>?"
            "<br><br>This verse is not found in the Bible."
        )
        self.label = QLabel(message)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setWordWrap(True)
        layout.addWidget(self.label)

        # --- Buttons ---
        button_layout = QHBoxLayout()
        
        self.show_button = QPushButton("✅ Show Anyway")
        self.show_button.clicked.connect(self._accept)
        
        self.cancel_button = QPushButton("❌ Cancel")
        self.cancel_button.clicked.connect(self._reject)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addStretch()
        button_layout.addWidget(self.show_button)
        
        layout.addLayout(button_layout)
        
        # --- Timer ---
        self.timeout_seconds = 8
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._reject)
        self.timer.start(self.timeout_seconds * 1000)
        
        # Update cancel button text with countdown
        self._update_cancel_button_text()
        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self._update_cancel_button_text)
        self.countdown_timer.start(1000)

    def _update_cancel_button_text(self):
        if self.timeout_seconds > 0:
            self.cancel_button.setText(f"❌ Cancel ({self.timeout_seconds})")
            self.timeout_seconds -= 1
        else:
            self.countdown_timer.stop()

    def _accept(self):
        self.timer.stop()
        self.countdown_timer.stop()
        self.callback(True)
        self.accept()

    def _reject(self):
        self.timer.stop()
        self.countdown_timer.stop()
        self.callback(False)
        self.reject()

if __name__ == '__main__':
    # Example usage for testing the dialog
    app = QApplication(sys.argv)
    
    def on_result(confirmed):
        print(f"User confirmed: {confirmed}")

    dialog = UserConfirmPopup("Maccabees", 4, 3, on_result)
    dialog.exec()
    sys.exit(app.exec()) 
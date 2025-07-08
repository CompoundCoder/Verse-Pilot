from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton, QDialogButtonBox
from PyQt6.QtCore import pyqtSignal

class DevInputWindow(QDialog):
    """
    A simple dialog for developers to manually enter text and submit it for AI processing,
    simulating a voice transcript.
    """
    text_submitted = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Developer: Manual AI Input")
        self.setMinimumSize(400, 250)

        # --- Layout ---
        layout = QVBoxLayout(self)

        # --- Instructions ---
        instructions = QLabel(
            "Enter a transcript below to simulate voice input. "
            "Click 'Send to AI' to process the text through the verse detection pipeline."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # --- Text Input ---
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("e.g., Let's turn to John chapter 3 verse 16")
        layout.addWidget(self.text_edit)

        # --- Buttons ---
        button_box = QDialogButtonBox()
        send_button = QPushButton("Send to AI")
        send_button.clicked.connect(self._on_submit)
        button_box.addButton(send_button, QDialogButtonBox.ButtonRole.AcceptRole)
        
        layout.addWidget(button_box)
        
        self.setLayout(layout)

    def _on_submit(self):
        """
        Handles the submission, emits the signal, and closes the dialog.
        """
        text = self.text_edit.toPlainText().strip()
        if text:
            self.text_submitted.emit(text)
            self.text_edit.clear()
        self.accept() # Closes the dialog 
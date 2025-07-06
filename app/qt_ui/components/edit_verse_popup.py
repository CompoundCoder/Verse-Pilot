from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QFormLayout, QLineEdit, QLabel
)
from app.core.bible import bible_lookup

class EditVersePopup(QDialog):
    """
    A popup dialog for editing a bible verse's reference.
    """
    def __init__(self, verse_data: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Verse")
        
        self.original_data = verse_data
        self._updated_data = None

        # --- Layouts ---
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        button_layout = QHBoxLayout()

        # --- Form Fields ---
        self.book_entry = QLineEdit(verse_data.get("book", ""))
        self.chapter_entry = QLineEdit(str(verse_data.get("chapter", "")))
        self.verse_entry = QLineEdit(str(verse_data.get("verse", "")))

        form_layout.addRow("Book:", self.book_entry)
        form_layout.addRow("Chapter:", self.chapter_entry)
        form_layout.addRow("Verse:", self.verse_entry)

        # --- Error Label ---
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red;")
        
        # --- Buttons ---
        self.save_button = QPushButton("Save")
        self.save_button.setObjectName("primaryButton")
        self.save_button.clicked.connect(self._on_save)
        self.save_button.setDefault(True)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setObjectName("cancelButton")
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.cancel_button)
        button_layout.addStretch(1)
        button_layout.addWidget(self.save_button)

        layout.addLayout(form_layout)
        layout.addWidget(self.error_label)
        layout.addLayout(button_layout)
    
    def _on_save(self):
        """Validates the new verse and, if valid, accepts the dialog."""
        book = self.book_entry.text().strip()
        chapter_str = self.chapter_entry.text().strip()
        verse_str = self.verse_entry.text().strip()

        if not all([book, chapter_str, verse_str]):
            self.error_label.setText("All fields are required.")
            return

        try:
            chapter = int(chapter_str)
            verse = int(verse_str)
        except ValueError:
            self.error_label.setText("Chapter and Verse must be numbers.")
            return

        verse_text = bible_lookup.get_verse(book, chapter, verse)
        if "not found" in verse_text:
            self.error_label.setText(f"Verse not found: {book} {chapter}:{verse}")
            return
            
        self._updated_data = {
            "book": book,
            "chapter": chapter,
            "verse": verse,
            "text": verse_text,
            "confidence": 1.0, # Edited verses are considered high confidence
            "timestamp": self.original_data.get("timestamp", 0) # Preserve original timestamp
        }
        self.accept()

    def get_updated_verse_data(self) -> dict | None:
        """Returns the new verse data if the dialog was accepted."""
        return self._updated_data 
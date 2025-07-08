from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QAbstractItemView
from PyQt6.QtCore import Qt, pyqtSignal
import logging

class SidebarPanel(QWidget):
    """
    A reusable panel for displaying a list of verses (e.g., Queue or History).
    """
    verse_double_clicked = pyqtSignal(dict)
    verse_right_clicked = pyqtSignal(dict, object) # verse_data, global_pos

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName("SidebarPanel")
        
        self.verses: list[dict] = [] # Store the raw verse data

        # --- Layout ---
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # --- Title ---
        self.title_label = QLabel(title)
        self.title_label.setObjectName("SidebarTitle")
        self.title_label.setStyleSheet("font-weight: bold; padding: 5px;")

        # --- Verse List ---
        self.list_view = QListWidget()
        self.list_view.setObjectName("SidebarListView")
        self.list_view.setAlternatingRowColors(True)
        self.list_view.setWordWrap(False)
        self.list_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_view.setStyleSheet("QListWidget::item { padding: 5px 8px; }")
        
        # --- Configure interaction ---
        self.list_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.list_view.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.list_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_view.customContextMenuRequested.connect(self._on_right_click)

        # Add widgets to layout
        layout.addWidget(self.title_label)
        layout.addWidget(self.list_view)
        
        self.setLayout(layout)

    def update_items(self, verses: list[dict]):
        """
        Updates the list with new verse data.
        """
        self.list_view.clear()
        # Sort by timestamp, newest first
        sorted_verses = sorted(verses, key=lambda v: v.get('timestamp', 0), reverse=True)

        for verse_data in sorted_verses:
            item_text = self._format_verse_display(verse_data)
            item = QListWidgetItem(item_text)
            # Store the raw dictionary in the item for later use (e.g., on click)
            item.setData(Qt.ItemDataRole.UserRole, verse_data)
            self.list_view.addItem(item)
    
    def remove_item(self, verse_key_to_remove: tuple):
        """Removes an item from the list based on its verse key."""
        for i in range(self.list_view.count()):
            item = self.list_view.item(i)
            if item:
                verse_data = item.data(Qt.ItemDataRole.UserRole)
                item_key = (verse_data.get('book'), verse_data.get('chapter'), verse_data.get('verse'))
                if item_key == verse_key_to_remove:
                    self.list_view.takeItem(i)
                    break # Assume unique keys

    def _format_verse_display(self, verse_data: dict) -> str:
        """Formats a verse dict into a user-friendly string for display."""
        book = verse_data.get("book", "Unknown")
        chapter = verse_data.get("chapter", 0)
        verse = verse_data.get("verse", 0)
        
        return f"{book} {chapter}:{verse}"

    def _on_item_double_clicked(self, item: QListWidgetItem):
        """Emits the raw verse data when an item is double-clicked."""
        verse_data = item.data(Qt.ItemDataRole.UserRole)
        self.verse_double_clicked.emit(verse_data)
        
    def _on_right_click(self, pos):
        """Handles the right-click event and emits a signal."""
        item = self.list_view.itemAt(pos)
        if item:
            verse_data = item.data(Qt.ItemDataRole.UserRole)
            global_pos = self.list_view.mapToGlobal(pos)
            self.verse_right_clicked.emit(verse_data, global_pos)

    def add_verse(self, verse_data: dict, is_pending: bool = False):
        """Adds a verse to the sidebar list. Placeholder implementation."""
        # This is a stub to prevent crashes. It can be built out later
        # to visually represent the verse in the list.
        logging.info(f"[SidebarPanel] Received verse: {verse_data.get('reference')} (Pending: {is_pending})")
        # For now, we can just add the reference as a simple list item.
        item = QListWidgetItem(verse_data.get("reference", "Unknown Verse"))
        if is_pending:
            item.setForeground(Qt.GlobalColor.gray) # Example: style pending verses
        self.list_view.insertItem(0, item) 
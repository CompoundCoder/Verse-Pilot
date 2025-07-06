from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QAbstractItemView
from PyQt6.QtCore import Qt, pyqtSignal

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

    def update_verses(self, verses: list[dict]):
        """
        Updates the list with new verse data.
        """
        self.list_view.clear()
        for verse_data in verses:
            item = QListWidgetItem(self._format_verse(verse_data))
            # Store the raw dictionary in the item
            item.setData(Qt.ItemDataRole.UserRole, verse_data)
            self.list_view.addItem(item)

    def _format_verse(self, verse_data: dict) -> str:
        """Formats a verse dict into a user-friendly string."""
        book = verse_data.get("book", "Unknown")
        chapter = verse_data.get("chapter", "?")
        verse = verse_data.get("verse", "?")
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
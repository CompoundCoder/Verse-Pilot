from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
    QStackedWidget, QPushButton, QFormLayout, QCheckBox, QDoubleSpinBox, 
    QSpinBox, QListWidgetItem, QLabel, QSlider, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, QSize
from app.core.settings.settings_model import get_settings, SettingsModel

class SettingsScreen(QDialog):
    """
    A settings dialog with a sidebar for tab navigation.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumSize(600, 400)
        self.settings = get_settings()
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        # Main vertical layout
        self.main_layout = QVBoxLayout(self)

        # Top part with sidebar and stack
        content_layout = QHBoxLayout()
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(120)
        self.sidebar.currentRowChanged.connect(self.change_page)
        self.sidebar.setWordWrap(False)
        self.sidebar.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content_layout.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack)
        self.main_layout.addLayout(content_layout)

        # Add a separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        self.main_layout.addWidget(line)

        # Bottom button layout
        button_layout = QHBoxLayout()
        self.restore_button = QPushButton("Restore Defaults")
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setObjectName("cancelButton")
        self.save_button = QPushButton("Save")
        self.save_button.setObjectName("primaryButton")
        self.save_button.setDefault(True)

        button_layout.addWidget(self.restore_button)
        button_layout.addStretch(1)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)
        self.main_layout.addLayout(button_layout)
        
        # Connections
        self.restore_button.clicked.connect(self._restore_defaults)
        self.cancel_button.clicked.connect(self.reject)
        self.save_button.clicked.connect(self._save_and_accept)

        # Setup Tabs
        self._setup_tabs()

    def _setup_tabs(self):
        self.general_tab = self._create_general_tab()
        self.timing_tab = self._create_timing_tab()

        self._add_tab("General", self.general_tab)
        self._add_tab("Timing", self.timing_tab)

    def _add_tab(self, name: str, widget: QWidget):
        self.sidebar.addItem(name)
        self.stack.addWidget(widget)

    def change_page(self, index):
        self.stack.setCurrentIndex(index)

    def _save_and_accept(self):
        self._save_settings()
        self.accept()

    def _restore_defaults(self):
        # Confirmation dialog
        confirm = QMessageBox.question(self, "Restore Defaults",
                                     "Are you sure you want to restore all settings to their default values?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            self.settings.restore_defaults()
            self._load_settings()

    def _create_general_tab(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        
        self.confidence_threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.confidence_threshold_slider.setRange(0, 100)
        # Add other general settings widgets here...

        layout.addRow("Confidence Threshold:", self.confidence_threshold_slider)
        return widget

    def _create_timing_tab(self):
        widget = QWidget()
        layout = QFormLayout(widget)

        self.timeout_spinbox = QSpinBox()
        self.timeout_spinbox.setRange(1, 60)
        self.timeout_spinbox.setSuffix(" s")

        layout.addRow("Confirmation Timeout:", self.timeout_spinbox)
        return widget

    def _load_settings(self):
        # Load general settings
        self.confidence_threshold_slider.setValue(int(self.settings.confidence_threshold * 100))
        
        # Load timing settings
        self.timeout_spinbox.setValue(self.settings.auto_show_delay_seconds)

    def _save_settings(self):
        # Save general settings
        self.settings.confidence_threshold = self.confidence_threshold_slider.value() / 100.0
        
        # Save timing settings
        self.settings.auto_show_delay_seconds = self.timeout_spinbox.value() 
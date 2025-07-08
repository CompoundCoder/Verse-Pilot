import random
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt, QSize, QTimer, pyqtSignal
from app.qt_ui.resources.icon_provider import get_icon

class MicRippleWidget(QWidget):
    """
    An interactive widget that displays a microphone icon and a subtle, organic
    ripple animation to indicate audio recording.
    """
    listening_state_changed = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_listening = False
        self.is_hovering = False
        
        # --- Animation State ---
        self.ripple_radii = []
        self.max_radius = 80
        self.ripple_timer = QTimer(self)
        self.ripple_timer.timeout.connect(self._animate_ripple)
        
        # --- Icon Resources ---
        self.mic_icon_default = get_icon("mic")
        self.mic_icon_hover = get_icon("mic", color="#CCCCCC")
        self.mic_icon_active = get_icon("mic", color="#007AFF")

        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Click to start or stop listening")
        # NO LAYOUT OR LABELS - This is a custom-painted widget

    def start_animation(self):
        """Starts the ripple animation loop."""
        if not self.ripple_timer.isActive():
            self.ripple_radii.clear()
            self.ripple_timer.start(16) # ~60 FPS

    def stop_animation(self):
        """Stops the ripple animation."""
        self.ripple_timer.stop()
        self.ripple_radii.clear()
        self.update()

    def _animate_ripple(self):
        """Updates the ripple effect animation for each frame."""
        # Move existing ripples outward
        self.ripple_radii = [r + 1 for r in self.ripple_radii if r < self.max_radius]
        
        # Add a new ripple periodically to create a pulsing effect
        if not self.ripple_radii or self.ripple_radii[-1] > 25:
             self.ripple_radii.append(0)

        self.update() # Trigger a repaint

    # --- Event Handlers ---

    def mousePressEvent(self, event):
        """Toggles the listening state on a left-button click."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_listening = not self.is_listening
            
            if self.is_listening:
                self.start_animation()
            else:
                self.stop_animation()
            
            self.listening_state_changed.emit(self.is_listening)
            self.update()
        super().mousePressEvent(event)

    def enterEvent(self, event):
        """Handles the mouse entering the widget area for hover effects."""
        self.is_hovering = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Handles the mouse leaving the widget area."""
        self.is_hovering = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        """Renders the ripples and the central microphone icon."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        center_x, center_y = self.width() // 2, self.height() // 2
        
        # 1. Draw ripples
        if self.is_listening:
            for radius in self.ripple_radii:
                alpha = int(100 * (1 - radius / self.max_radius))
                painter.setPen(QPen(QColor(0, 122, 255, alpha), 2))
                painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)

        # 2. Draw Icon
        icon_size = 48
        current_icon = self._get_current_icon()
        icon_x, icon_y = center_x - icon_size // 2, center_y - icon_size // 2
        current_icon.paint(painter, icon_x, icon_y, icon_size, icon_size)

    def sizeHint(self) -> QSize:
        """Provides a sensible default size for the widget."""
        return QSize(200, 200)

    def set_verse_display(self, verse_data: dict):
        # This method is no longer responsible for display.
        # We keep it to prevent crashes but it does nothing.
        # It will be removed in a future cleanup.
        pass

    def _get_current_icon(self):
        """Returns the current icon based on the listening state."""
        if self.is_listening:
            return self.mic_icon_active
        elif self.is_hovering:
            return self.mic_icon_hover
        else:
            return self.mic_icon_default 
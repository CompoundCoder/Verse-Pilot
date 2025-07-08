from PyQt6.QtWidgets import QComboBox, QWidget, QStyle
from PyQt6.QtCore import Qt, QTimer, QPoint

class UpwardComboBox(QComboBox):
    """
    A QComboBox that always opens its popup view upwards and expands to show all items,
    without flickering.
    """
    def showPopup(self):
        """
        Overrides the default popup behavior to prevent flicker. The popup is
        created, immediately hidden, then repositioned and resized in a separate
        event loop cycle before being shown in its final upward position.
        """
        super().showPopup()
        
        # Hide the popup immediately to prevent it from flashing in the default position.
        popup = self.view().window()
        if popup:
            popup.hide()

        # Use a timer to adjust and show the popup in the next event cycle.
        QTimer.singleShot(0, self._adjust_and_reposition_popup)

    def _adjust_and_reposition_popup(self):
        """
        Calculates the correct size and upward position for the popup,
        then moves and shows it.
        """
        if self.count() == 0:
            return

        popup = self.view().window()
        if not popup:
            return

        # Do not manually resize if the style uses a native popup (e.g., on macOS)
        if not self.style().styleHint(QStyle.StyleHint.SH_ComboBox_Popup):
            view = self.view()
            item_height = view.sizeHintForRow(0) if self.count() > 0 else 0
            frame_width = view.frameWidth() * 2
            
            total_height = (item_height * self.count()) + frame_width
            view.setFixedHeight(total_height)
        
        # Reposition the popup above the combobox
        rect = self.rect()
        popup_height = popup.height()
        
        target_pos = self.mapToGlobal(rect.topLeft())
        target_pos.setY(target_pos.y() - popup_height)
        
        popup.move(target_pos)
        
        # Now, show the popup in its final, correct position.
        popup.show() 
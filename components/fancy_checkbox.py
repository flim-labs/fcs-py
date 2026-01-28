from PyQt6.QtCore import pyqtSignal, Qt, QSize, QEvent
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QMouseEvent, QIcon, QFontMetrics
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

SELECTED_COLOR = "#31c914"
SELECTED_HOVER_COLOR = "#57D33D"
DISABLED_SELECTED_COLOR = "#2E2E2E"
UNSELECTED_COLOR = "#000000"
DISABLED_COLOR = "lightgrey"
TEXT_COLOR = "#FFFFFF"


CHECKED_COLOR = "#31c914"
UNCHECKED_COLOR = "lightgrey"

SELECTED_COLOR_BUTTON = "#31c914"



class FancyCheckbox(QWidget):
    toggled = pyqtSignal(bool)  # Signal to emit when the checkbox state changes
    labelClicked = pyqtSignal()  # Signal to emit when the label is clicked

    def __init__(self, text="", label_custom_part="", label_default_part="", parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(3)

        self.checkbox = Checkbox(self)
        self.checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Label container to manage custom layout
        self.label_container = QWidget(self)
        self.label_layout = QVBoxLayout(self.label_container)
        self.label_layout.setContentsMargins(5, 0, 0, 0)
        self.label_layout.setSpacing(0)
        
        # Single label for the full text
        self.label = QLabel(text, self.label_container)
        self.label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.label_layout.addWidget(self.label)
        
        # Store custom/default parts for dynamic truncation
        self.label_custom_part = label_custom_part
        self.label_default_part = label_default_part
        self.full_text = text
        
        # Install event filter for hover effects
        self.label_container.installEventFilter(self)
        self.is_hovering = False
        
        self.layout.addWidget(self.checkbox)
        self.layout.addWidget(self.label_container, 1)  # Stretch to fill available space
        
        # Connect checkbox toggle
        self.checkbox.toggled.connect(self.emit_toggled_signal)

    def eventFilter(self, obj, event):
        """Handle hover events on label container"""
        if obj == self.label_container:
            if event.type() == QEvent.Type.Enter:
                self.is_hovering = True
                self.label_container.setStyleSheet("background-color: #404040;")
                return True
            elif event.type() == QEvent.Type.Leave:
                self.is_hovering = False
                self.label_container.setStyleSheet("")
                return True
            elif event.type() == QEvent.Type.MouseButtonPress:
                if event.button() == Qt.MouseButton.LeftButton:
                    # Emit signal for label click
                    self.labelClicked.emit()
                    return True
        return super().eventFilter(obj, event)

    def set_text_parts(self, custom_part, default_part):
        """Set custom and default parts of the label text with dynamic truncation"""
        self.label_custom_part = custom_part
        self.label_default_part = default_part
        
        if custom_part:
            self.full_text = f"{custom_part} {default_part}"
        else:
            self.full_text = default_part if default_part else custom_part
        
        self._update_label_text()
    
    def _update_label_text(self):
        """Update label text with dynamic truncation based on available width"""
        if not self.label_custom_part or not self.label_default_part:
            # No custom name, show full text
            self.label.setText(self.full_text)
            return
        
        # Calculate available width for the label
        available_width = self.label_container.width() - self.label_layout.contentsMargins().left() - self.label_layout.contentsMargins().right()
        
        if available_width <= 0:
            # Not yet rendered, use full text
            self.label.setText(self.full_text)
            return
        
        # Get font metrics
        fm = QFontMetrics(self.label.font())
        
        # Calculate width of default part (always visible)
        default_width = fm.horizontalAdvance(f" {self.label_default_part}")
        ellipsis_width = fm.horizontalAdvance("...")
        
        # Available width for custom part
        custom_available = available_width - default_width - ellipsis_width - 10  # 10px safety margin
        
        if custom_available <= 0:
            # Not enough space, show only default part with minimal custom
            truncated_text = f"...{self.label_default_part}"
        else:
            # Truncate custom part to fit
            custom_text = self.label_custom_part
            custom_width = fm.horizontalAdvance(custom_text)
            
            if custom_width <= custom_available:
                # Full custom name fits
                truncated_text = f"{custom_text} {self.label_default_part}"
            else:
                # Need to truncate custom name
                # Binary search for the right length
                left, right = 0, len(custom_text)
                while left < right:
                    mid = (left + right + 1) // 2
                    test_text = custom_text[:mid]
                    if fm.horizontalAdvance(test_text) <= custom_available:
                        left = mid
                    else:
                        right = mid - 1
                
                truncated_custom = custom_text[:left]
                truncated_text = f"{truncated_custom}...{self.label_default_part}"
        
        self.label.setText(truncated_text)
    
    def resizeEvent(self, event):
        """Handle resize to update label text"""
        super().resizeEvent(event)
        self._update_label_text()

    def emit_toggled_signal(self, checked):
        self.toggled.emit(checked)

    def is_checked(self):
        return self.checkbox.is_checked()

    def set_checked(self, checked):
        self.checkbox.set_checked(checked)

    def set_text(self, text):
        self.full_text = text
        self.label.setText(text)

    def setEnabled(self, enabled):
        self.checkbox.setEnabled(enabled)
        self.label.setEnabled(enabled)


class Checkbox(QWidget):
    toggled = pyqtSignal(bool)  # Signal to emit when the checkbox state changes

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(20, 20)  # Set the size of the checkbox
        self.checked = False
        self.enabled = True

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.checked:
            outer_color = QColor(CHECKED_COLOR if self.enabled else DISABLED_COLOR)
        else:
            outer_color = QColor(CHECKED_COLOR if self.enabled else DISABLED_COLOR)
        painter.setPen(QPen(outer_color, 1))
        painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        painter.drawEllipse(1, 1, 18, 18)
        if self.checked:
            inner_color = QColor(CHECKED_COLOR if self.enabled else DISABLED_COLOR)
            painter.setBrush(QBrush(inner_color))
            painter.drawEllipse(4, 4, 12, 12)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self.enabled:
            self.checked = not self.checked
            self.update()  # Trigger a repaint
            self.toggled.emit(self.checked)  # Emit the toggled signal

    def is_checked(self):
        return self.checked

    def set_checked(self, checked):
        if self.checked != checked:
            self.checked = checked
            self.update()  # Trigger a repaint

    def setEnabled(self, enabled):
        if self.enabled != enabled:
            self.enabled = enabled
            self.update()  # Trigger a repaint


class FancyButton(QPushButton):
    def __init__(self, text="", icon_path=None, parent=None):
        super().__init__(text, parent)
        self.selected = False  # Track the selected state
        self.initUI(icon_path)

    def initUI(self, icon_path):
        if icon_path:
            self.setIcon(QIcon(icon_path))
            self.setIconSize(QSize(24, 24))  # Adjust icon size as needed
        self.setFlat(True)  # Set the button to flat style
        self.updateStyleSheet()
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_selected(self, selected):
        self.selected = selected
        self.updateStyleSheet()

    def setEnabled(self, enabled):
        super().setEnabled(enabled)
        self.updateStyleSheet()

    def updateStyleSheet(self):
        bg_color = SELECTED_COLOR_BUTTON if self.selected else UNSELECTED_COLOR
        color = SELECTED_COLOR_BUTTON
        if not self.isEnabled():
            bg_color = "#3c3c3c" if self.selected else "#000000"
            color = "lightgrey"
        hover_color = "#31c914"
        pressed_color = "#7FE777"

        self.setStyleSheet(f"""
            QPushButton {{
                font-family: "Montserrat";
                font-size: 14px;
                font-weight: thin;
                border: 1px solid {color};
                border-radius: 0px;
                color: white;
                padding: 5px;
                background-color: {bg_color};
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:pressed {{
                background-color: {pressed_color};
            }}
        """)
from PyQt6.QtWidgets import QWidget, QGridLayout

class FlexibleGridLayout(QWidget):
    def __init__(self, widgets=[], parent=None):
        super().__init__(parent)

        self.grid_layout = QGridLayout()
        self.setLayout(self.grid_layout)

        self.widgets = widgets

        self.update_layout()

    def set_widgets(self, widgets):
        self.widgets = widgets
        self.update_layout()

    def update_layout(self):
        # Rimuovi tutti i widget precedenti dalla griglia
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            self.grid_layout.removeWidget(widget)
            widget.setParent(None)

        # Aggiungi i widget alla griglia in base alla nuova larghezza della finestra
        num_columns = max(self.width() // 200, 1)  # Si presuppone che la larghezza di ogni widget sia di circa 200 pixel
        row, col = 0, 0
        for widget in self.widgets:
            self.grid_layout.addWidget(widget, row, col)
            col += 1
            if col >= num_columns:
                col = 0
                row += 1

    def resizeEvent(self, event):
        self.update_layout()
        super().resizeEvent(event)

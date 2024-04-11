import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QGridLayout, QPushButton, QWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setWindowTitle("Wrap Layout Example")
        self.setGeometry(100, 100, 600, 200)

        # Creazione del layout della griglia
        self.grid_layout = QGridLayout()

        # Creazione di un widget principale e impostazione del layout
        main_widget = QWidget()
        main_widget.setLayout(self.grid_layout)
        self.setCentralWidget(main_widget)

        # Creazione di alcuni pulsanti di esempio
        self.buttons = []
        for i in range(10):
            button = QPushButton(f"Button {i+1}")
            self.buttons.append(button)

        # Connessione del segnale resizeEvent per gestire il ridimensionamento della finestra
        self.resizeEvent = self.on_resize

        # Esegui il layout iniziale
        self.update_layout()

    def update_layout(self):
        # Rimuovi tutti i widget precedenti dalla griglia
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            self.grid_layout.removeWidget(widget)
            widget.setParent(None)

        # Aggiungi i widget alla griglia in base alla nuova larghezza della finestra
        num_columns = max(self.width() // 200, 1)  # Si presuppone che la larghezza di ogni pulsante sia di circa 200 pixel
        row, col = 0, 0
        for button in self.buttons:
            self.grid_layout.addWidget(button, row, col)
            col += 1
            if col >= num_columns:
                col = 0
                row += 1

    def on_resize(self, event):
        # Aggiorna il layout ogni volta che la finestra viene ridimensionata
        self.update_layout()
        # Chiamare la funzione resizeEvent dell'implementazione base
        super().resizeEvent(event)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

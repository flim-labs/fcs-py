import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QProgressBar, QPushButton
from PyQt6.QtCore import QTimer

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.selected_average = 7
        self.acquisitions_count = 0

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.progress_bar = QProgressBar()
        self.layout.addWidget(self.progress_bar)

        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_acquisition)
        self.layout.addWidget(self.start_button)

        self.acquisition_timer = QTimer()
        self.acquisition_timer.timeout.connect(self.update_acquisition_count)

    def start_acquisition(self):
        if self.acquisitions_count < self.selected_average:
            self.acquisition_timer.start(1000)  # Esegui l'acquisizione ogni secondo
        else:
            self.acquisition_timer.stop()

    def update_acquisition_count(self):
        self.acquisitions_count += 1
        progress_value = (self.acquisitions_count / float(self.selected_average)) * 100
        self.progress_bar.setValue(int(progress_value))  # Converto il valore in intero prima di impostarlo

app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt, QThread
from PyQt6.QtGui import QMovie
from components.resource_path import resource_path

class SpinnerThread(QThread):
    def run(self):
        pass 

class Spinner(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.spinner_label = QLabel(self)
        self.spinner_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.spinner_label)
        self.spinner_thread = SpinnerThread()
        self.start_spinner_animation()

    def start_spinner_animation(self):
        spinner_movie = QMovie(resource_path("assets/spinner.gif"))
        self.spinner_label.setMovie(spinner_movie)
        spinner_movie.start()

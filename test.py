import sys
import time
import numpy as np
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
import pyqtgraph as pg

class LivePlotWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.time_span = 20  # intervallo di tempo da visualizzare in secondi
        self.plot_interval = 0.1  # intervallo di aggiornamento del grafico in secondi
        self.data_len = int(self.time_span / self.plot_interval)  # lunghezza dei dati da memorizzare
        
        self.x_data = np.linspace(0, self.time_span, self.data_len)
        self.y_data = np.zeros(self.data_len)
        
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setLabel('left', 'Conteggi di fotoni')
        self.plot_widget.setLabel('bottom', 'Tempo (s)')
        self.plot_curve = self.plot_widget.plot(pen='r')
        
        layout = QVBoxLayout()
        layout.addWidget(self.plot_widget)
        self.setLayout(layout)
        
        self.timer = pg.QtCore.QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(int(self.plot_interval * 1000))  # Converti il valore in millisecondi
        
        self.last_update_time = time.time()
        
    def update_plot(self):
        current_time = time.time()
        elapsed_time = current_time - self.last_update_time
        
        # Aggiorna i dati solo se è trascorso un tempo sufficiente
        if elapsed_time >= self.plot_interval:
            self.x_data[:-1] = self.x_data[1:]  # sposta tutti i dati a sinistra
            self.x_data[-1] = self.x_data[-2] + self.plot_interval  # aggiorna l'ultimo valore su x
            self.y_data[:-1] = self.y_data[1:]  # sposta tutti i dati a sinistra
            self.y_data[-1] = np.random.randint(0, 10)  # genera un nuovo dato fittizio
            
            self.plot_curve.setData(x=self.x_data, y=self.y_data)
            self.plot_widget.setXRange(self.x_data[0], self.x_data[0] + self.time_span)
            
            self.last_update_time = current_time

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Grafico Live Realtime")
        self.setGeometry(100, 100, 800, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        self.live_plot_widget = LivePlotWidget()
        layout.addWidget(self.live_plot_widget)
        central_widget.setLayout(layout)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

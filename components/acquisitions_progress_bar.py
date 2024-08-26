from PyQt6.QtWidgets import QWidget, QProgressBar, QVBoxLayout, QLabel, QApplication, QHBoxLayout
import time

from components.gui_styles import GUIStyles
from components.settings import ACQUISITION_PROGRESS_BAR_WIDGET, GT_PROGRESS_BAR_WIDGET


class AcquisitionsProgressBar(QWidget):
    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.app = window
        layout = QVBoxLayout()
        label_row = self.create_label_row()
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(15)
        layout.addLayout(label_row)
        layout.addWidget(self.progress_bar)
        self.setLayout(layout)
        self.setContentsMargins(10, 0, 18, 0)
        self.setObjectName("progress_bar_widget")
        self.setStyleSheet(GUIStyles.set_progress_bar_widget(color="#FB8C00"))
        
        
    def create_label_row(self):
        from components.intensity_tracing_controller import IntensityTracingPlot  
        row = QHBoxLayout() 
        # Acquisition countdown label
        countdown_label = IntensityTracingPlot.create_countdown_label()
        countdown_label.setVisible(False)
        self.app.acquisition_time_countdown_widget = countdown_label 
        # Progress bar label
        self.label = QLabel()
        row.addWidget(self.label)
        row.addSpacing(10)
        row.addWidget(countdown_label)
        row.addStretch(1)
        return row

    def update_acquisitions_count(self):
        if self.app.acquisitions_count < self.app.selected_average:
            progress_value = (
                self.app.acquisitions_count / float(self.app.selected_average)
            ) * 100

            self.progress_bar.setValue(int(progress_value))
            self.label.setText(
                f"Acquisition {self.app.acquisitions_count}/{self.app.selected_average} finished"
            )
            QApplication.processEvents()
        else:
            self.progress_bar.setValue(100)
            self.label.setText(
                f"Acquisition {self.app.selected_average}/{self.app.selected_average} finished"
            )
            QApplication.processEvents()
            time.sleep(0.5)
            self.progress_bar.setValue(0)
            self.remove_progress_bar(self.app)
            QApplication.processEvents()

    def clear_acquisition_timer(self, app):
        self.app.acquisitions_count = 0
        self.progress_bar.setValue(0)
        self.remove_progress_bar(self.app)
        QApplication.processEvents()

    def remove_progress_bar(self, app):
        if ACQUISITION_PROGRESS_BAR_WIDGET in app.widgets:
            app.widgets[ACQUISITION_PROGRESS_BAR_WIDGET].setVisible(False)




class GtProgressBar(QWidget):
    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.app = window
        layout = QVBoxLayout()
        self.label = QLabel()
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(15)
        layout.addWidget(self.label)
        layout.addWidget(self.progress_bar)
        self.setLayout(layout)
        self.setContentsMargins(10, 0, 18, 0)
        self.setObjectName("progress_bar_widget")
        self.setStyleSheet(GUIStyles.set_progress_bar_widget(color="#31c914"))

    def update_calculation_count(self, iteration):
        num_acquisitions =  self.app.selected_average if self.app.free_running_acquisition_time == False else 1
        if iteration < num_acquisitions:
            progress_value = (
                iteration / float(num_acquisitions)
            ) * 100

            self.progress_bar.setValue(int(progress_value))
            self.label.setText(
                f"Calculation {iteration}/{num_acquisitions} finished"
            )
            QApplication.processEvents()
        else:
            self.progress_bar.setValue(100)
            self.label.setText(
                f"Calculation {iteration}/{num_acquisitions} finished"
            )
            QApplication.processEvents()
            time.sleep(0.5)
            self.progress_bar.setValue(0)
            self.remove_progress_bar(self.app)
            QApplication.processEvents()

    def clear_acquisition_timer(self, app):
        self.progress_bar.setValue(0)
        self.remove_progress_bar(self.app)
        QApplication.processEvents()

    def remove_progress_bar(self, app):
        if GT_PROGRESS_BAR_WIDGET in app.widgets:
            app.widgets[GT_PROGRESS_BAR_WIDGET].setVisible(False)

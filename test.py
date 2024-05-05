import sys
import time
from flim_labs import flim_labs
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout
from PyQt6.QtCore import QTimer


class FCSWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.enabled_channels = [3, 5, 7]
        self.acquisition_time = 1000
        self.bin_width = 1
        self.firmware = "intensity_tracing_usb.flim"
        self.write_data = True
        self.pull_from_queue_timer = QTimer()
        self.pull_from_queue_timer.timeout.connect(self.pull_from_queue)
        self.selected_average = 30
        self.acquisitions_count = 0

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_button_pressed)
        layout.addWidget(self.start_button)
        self.setLayout(layout)

    def start_photons_tracing(self):
        result = flim_labs.start_intensity_tracing(
            enabled_channels=self.enabled_channels,
            bin_width_micros=self.bin_width,
            write_bin=False,
            write_data=self.write_data,
            acquisition_time_millis=self.acquisition_time,
            firmware_file=self.firmware,
        )
        self.pull_from_queue_timer.start(1)

    def start_button_pressed(self):
        self.start_photons_tracing()

    def pull_from_queue(self):
        val = flim_labs.pull_from_queue()
        if len(val) > 0:
            for v in val:
                if v == ('end',):  # End of acquisition
                    print("Got end of acquisition, stopping")
                    self.stop_button_pressed()
                    if self.acquisitions_count < self.selected_average:
                        time.sleep(0.20)
                        self.start_photons_tracing()
                    break

                ((time_ns), (intensities)) = v
                print(intensities)

    def stop_button_pressed(self, app_close=False):
        self.pull_from_queue_timer.stop()
        try:
            flim_labs.request_stop()
        except Exception as e:
            pass
        if self.acquisitions_count >= self.selected_average:
            self.acquisitions_count = 0
        else:
            self.acquisitions_count += 1
        print("SELECTED AVERAGE")   
        print(self.selected_average) 
        print("ACQUISITIONS COUNT")
        print(self.acquisitions_count)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FCSWindow()
    window.showMaximized()
    window.show()
    exit_code = app.exec()
    window.stop_button_pressed(app_close=True)
    sys.exit(exit_code)

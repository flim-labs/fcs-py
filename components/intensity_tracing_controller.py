import queue
import threading
import time
import numpy as np
import pyqtgraph as pg
from functools import partial
from flim_labs import flim_labs
from components.box_message import BoxMessage
from components.format_utilities import FormatUtils
from components.messages_utilities import MessagesUtilities
from components.gui_styles import GUIStyles
from components.settings import *
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (
    QApplication,
    QMessageBox,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QWidget,
)
from PyQt6.QtGui import QPixmap
from components.resource_path import resource_path

class IntensityTracing:
    @staticmethod
    def start_photons_tracing(app):
        try:
            free_running_mode = app.control_inputs[SETTINGS_FREE_RUNNING_MODE].isChecked()
            acquisition_time_millis = (
                None if app.acquisition_time_millis in (0, None) or
                        free_running_mode
                else app.acquisition_time_millis
            )
            print("Selected firmware: " + (str(app.selected_firmware)))
            print("Free running enabled: " + str(free_running_mode))
            print("Acquisition time (ms): " + str(acquisition_time_millis))
            print("Time span (s): " + str(app.time_span))
            print("Max points: " + str(40 * app.time_span))
            print("Bin width (µs): " + str(app.bin_width_micros))

            result = flim_labs.start_intensity_tracing(
                enabled_channels=app.enabled_channels,
                bin_width_micros=app.bin_width_micros, 
                write_bin=False,  
                write_data=app.write_data,  
                acquisition_time_millis=acquisition_time_millis, 
                firmware_file=app.selected_firmware,
            )

            file_bin = result.bin_file
            if file_bin != "":
                print("File bin written in: " + str(file_bin))
            app.blank_space.hide()
            app.pull_from_queue_timer2.start(1)
           
           

        except Exception as e:
            error_title, error_msg = MessagesUtilities.error_handler(str(e))
            BoxMessage.setup(
                error_title,
                error_msg,
                QMessageBox.Icon.Critical,
                GUIStyles.set_msg_box_style(),
                app.test_mode
            )


    @staticmethod
    def pull_from_queue2(app):
        val = flim_labs.pull_from_queue()
        if len(val) > 0:
            for v in val:
                if v == ('end',):  # End of acquisition
                    IntensityTracing.stop_button_pressed(app)
                    app.control_inputs[START_BUTTON].setEnabled(True)
                    app.control_inputs[STOP_BUTTON].setEnabled(False)
                    break
                ((time_ns), (intensities)) = v
                IntensityTracing.calculate_cps(app, time_ns[0], intensities)
                IntensityTracing.calculate_cps_2(app, time_ns[0], intensities )
                for index, ch in enumerate(app.intensity_plots_to_show):
                    IntensityTracingPlot.update_plots2(app, index, time_ns, intensities[ch])    
            #IntensityTracingPlot.move_plots(app)            



    @staticmethod
    def calculate_cps(app, time_ns, counts):
        if app.update_plots: 
            cps_counts = [0] * 8
            next_second = 1
            seconds = time_ns / NS_IN_S
            for channel in app.intensity_plots_to_show:
                cps_counts[channel] += counts[channel] 
                if seconds >= next_second:
                    app.cps[app.intensity_plots_to_show.index(channel)].setText(
                        FormatUtils.format_cps(round(cps_counts[channel])) + " CPS"
                        )
                    cps_counts[channel] = 0     
            if seconds >= next_second:        
                next_second += 1
                QApplication.processEvents()


    @staticmethod    
    def calculate_cps_2(app, time_ns, counts):
        only_cps_widgets = [item for item in app.enabled_channels if item not in app.intensity_plots_to_show]
        if app.update_plots: 
            cps_counts = [0] * 8
            next_second = 1
            seconds = time_ns / NS_IN_S
            for channel in only_cps_widgets:
                if 0 <= channel < len(app.only_cps):
                    cps_counts[channel] += counts[channel] 
                    if seconds >= next_second:
                        app.only_cps[channel].setText(
                            FormatUtils.format_cps(round(cps_counts[channel])) + " CPS"
                        )
                        cps_counts[channel] = 0     
            if seconds >= next_second:        
                next_second += 1
                QApplication.processEvents()
            


    @staticmethod    
    def stop_button_pressed(app):
        app.update_plots = False
        app.acquisition_stopped = True
        app.current_time = 0 
        app.settings.setValue(SETTINGS_ACQUISITION_STOPPED, True)
        #app.control_inputs[DOWNLOAD_BUTTON].setEnabled(app.write_data and app.acquisition_stopped)
        #self.set_download_button_icon()
        app.control_inputs[START_BUTTON].setEnabled(len(app.enabled_channels) > 0)
        app.control_inputs[STOP_BUTTON].setEnabled(False)
        QApplication.processEvents()
        flim_labs.request_stop()
        app.pull_from_queue_timer2.stop()
        
          


class IntensityTracingPlot:

    @staticmethod
    def generate_chart(channel_index, app):
        intensity_widget = pg.PlotWidget()
        intensity_widget.setLabel('left', 'AVG. Photon counts', units='')
        intensity_widget.setLabel('bottom', 'Time', units='s')
        intensity_widget.setTitle(f'Channel {channel_index + 1}')
        intensity_widget.setBackground('#0E0E0E') 
        intensity_widget.setStyleSheet("border: 1px solid #3b3b3b")
        intensity_widget.plotItem.setContentsMargins(5, 10, 10, 10)  
        x = np.arange(1)
        y = x * 0
        pen = pg.mkPen(color='#FB8C00', width=1)
        intensity_plot = intensity_widget.plot(x, y, pen=pen)
        app.intensity_lines.append(intensity_plot)
        return intensity_widget

    @staticmethod
    def create_cps_label():    
        # cps indicator
        cps_label = QLabel("0 CPS")
        return cps_label   
   
    @staticmethod
    def update_plots2(app, channel_index, time_ns, curve):
        intensity_line = app.intensity_lines[channel_index] if channel_index < len(app.intensity_lines) else None
        if intensity_line is not None:
            if app.update_plots:
                x, y = intensity_line.getData()
                if x is None or (len(x) == 1 and x[0] == 0):
                    x = np.array([time_ns[0] / 1_000_000_000])
                    y = np.array([np.sum(curve)])
                else:
                    x = np.append(x, time_ns[0] / 1_000_000_000)
                    y = np.append(y, np.sum(curve))
                intensity_line.setData(x, y)
        QApplication.processEvents()
        time.sleep(0.01)


    @staticmethod
    def create_chart_widget(app, index):
           chart = IntensityTracingPlot.generate_chart(app.intensity_plots_to_show[index], app)
           cps = IntensityTracingPlot.create_cps_label()
           cps.setStyleSheet(GUIStyles.set_cps_label_style())
           chart_widget = QWidget()
           chart_layout = QVBoxLayout()
           chart_layout.addWidget(cps)
           chart_layout.addWidget(chart)
           chart_widget.setLayout(chart_layout)
           row, col = divmod(index, 2)
           app.layouts[INTENSITY_PLOTS_GRID].addWidget(chart_widget, row, col)
           app.intensity_charts.append(chart)
           app.intensity_charts_wrappers.append(chart_widget)
           app.cps.append(cps)


    @staticmethod 
    def move_plots(app):
        app.current_time += app.move_speed
        start_index = int(app.current_time * 10)
        end_index = start_index + int(app.time_span * 10) 
        for plot_widget in app.intensity_charts:
            plot_widget.setXRange(app.current_time, app.current_time + app.time_span)



class IntensityTracingOnlyCPS:
    @staticmethod
    def create_only_cps_widget(app, index, channel):
        only_cps_widget = QWidget()
        only_cps_widget.setObjectName("container")
        row_cps = QHBoxLayout()
        cps = IntensityTracingPlot.create_cps_label()
        cps.setObjectName("cps")
        channel_label = QLabel(f"Channel {channel + 1}")
        channel_label.setObjectName("ch")
        row_cps.addWidget(channel_label)
        arrow_icon = QLabel()
        arrow_icon.setPixmap(QPixmap(resource_path("assets/arrow-right-grey.png")).scaledToWidth(30))
        row_cps.addWidget(arrow_icon)
        row_cps.addWidget(cps)
        row_cps.addStretch(1)
        app.only_cps.append(cps)
        only_cps_widget.setLayout(row_cps)
        only_cps_widget.setStyleSheet(GUIStyles.only_cps_widget())
        row, col = divmod(index, 2)
        app.layouts[INTENSITY_ONLY_CPS_GRID].addWidget(only_cps_widget, row, col)
        app.only_cps_widgets.append(only_cps_widget)
        app.only_cps.append(cps)

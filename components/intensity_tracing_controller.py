import time
import numpy as np
import pyqtgraph as pg
from flim_labs import flim_labs
from components.animations import VibrantAnimation
from components.data_export_controls import DataExportActions
from components.fcs_controller import FCSPostProcessing
from components.box_message import BoxMessage
from components.format_utilities import FormatUtils
from components.layout_utilities import create_gt_loading_layout, create_gt_wait_layout, insert_widget, remove_widget
from components.messages_utilities import MessagesUtilities
from components.gui_styles import GUIStyles
from components.settings import *
from PyQt6.QtWidgets import (
    QApplication,
    QMessageBox,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QWidget,
    QLabel,
    QHBoxLayout,
   
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QTimer
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
            
            app.cached_time_span_seconds = float(app.settings.value(SETTINGS_TIME_SPAN, DEFAULT_TIME_SPAN))
            
            result = flim_labs.start_intensity_tracing(
                enabled_channels=app.enabled_channels,
                bin_width_micros=app.bin_width_micros, 
                write_bin=False,  
                write_data=True,  
                acquisition_time_millis=acquisition_time_millis, 
                firmware_file=app.selected_firmware,
            )
            if app.acquisitions_count >= app.selected_average:           
                app.widgets[ACQUISITION_PROGRESS_BAR_WIDGET].clear_acquisition_timer(app)
            if not free_running_mode:
                app.widgets[ACQUISITION_PROGRESS_BAR_WIDGET].update_acquisitions_count()
                app.widgets[ACQUISITION_PROGRESS_BAR_WIDGET].setVisible(True)
            file_bin = result.bin_file
            if file_bin != "":
                print("File bin written in: " + str(file_bin))
            app.blank_space.hide()
            app.pull_from_queue_timer.start(1)
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
    def pull_from_queue(app):
        val = flim_labs.pull_from_queue()
        if len(val) > 0:
            for v in val:
                if v == ('end',):  # End of acquisition
                    print("Got end of acquisition, stopping")
                    IntensityTracing.stop_button_pressed(app)
                    if app.acquisitions_count < app.selected_average:
                        time.sleep(0.20)
                        IntensityTracingButtonsActions.start_button_pressed(app)
                    else:
                        app.control_inputs[START_BUTTON].setEnabled(len(app.enabled_channels) > 0)     
                    break       
                    
                ((time_ns), (intensities)) = v
                IntensityTracing.process_data(app, time_ns[0], intensities)
                IntensityTracing.update_acquisition_countdowns(app, time_ns[0])
                app.last_acquisition_ns = time_ns[0]
                
 
   
    @staticmethod
    def process_data(app, time_ns, counts):
        adjustment = REALTIME_ADJUSTMENT / app.bin_width_micros
        for channel, cps in app.cps_ch.items():
            IntensityTracing.update_cps(app, time_ns, counts, channel)
        for i, channel in enumerate(app.intensity_plots_to_show):
            intensity = counts[channel] / adjustment
            IntensityTracingPlot.update_plots2(channel, i, time_ns, intensity, app) 
            

    @staticmethod
    def update_cps(app, time_ns, counts, channel_index):
        if not (channel_index in app.cps_counts):
            return
        cps = app.cps_counts[channel_index]
        if cps["last_time_ns"] == 0:
            cps["last_time_ns"] = time_ns
            cps["last_count"] = counts[channel_index]
            cps["current_count"] = counts[channel_index]
            return
        cps["current_count"] = cps["current_count"] + + counts[channel_index]
        time_elapsed = time_ns - cps["last_time_ns"]
        if time_elapsed > 330_000_000:
            cps_value = (cps["current_count"] - cps["last_count"]) / (
                time_elapsed / 1_000_000_000
            )
            humanized_number = FormatUtils.format_cps(cps_value) + " CPS"
            app.cps_ch[channel_index].setText(humanized_number)
            cps_threshold = app.control_inputs[SETTINGS_CPS_THRESHOLD].value()
            if cps_threshold > 0:
                if cps_value > cps_threshold:
                    if channel_index in app.cps_widgets_animation:
                        app.cps_widgets_animation[channel_index].start()
                else:
                    if channel_index in app.cps_widgets_animation:
                        app.cps_widgets_animation[channel_index].stop()
            cps["last_time_ns"] = time_ns
            cps["last_count"] = cps["current_count"] 
            
            
    @staticmethod        
    def update_acquisition_countdowns(app, time_ns):
        free_running = app.free_running_acquisition_time
        acquisition_time = app.control_inputs[SETTINGS_ACQUISITION_TIME_MILLIS].value()
        if free_running is True or free_running == "true":
            return
        elapsed_time_sec = time_ns / 1_000_000_000
        remaining_time_sec = max(0, acquisition_time - elapsed_time_sec)
        seconds = int(remaining_time_sec)
        milliseconds = int((remaining_time_sec - seconds) * 1000)
        milliseconds = milliseconds // 10
        if not app.acquisition_time_countdown_widget.isVisible():
            app.acquisition_time_countdown_widget.setVisible(True)
        app.acquisition_time_countdown_widget.setText(f"{seconds:02}:{milliseconds:02} (s)")    
    

    @staticmethod    
    def stop_button_pressed(app, app_close = False):
        app.pull_from_queue_timer.stop() 
        try:
            flim_labs.request_stop()
        except Exception as e:
            pass 
        def clear_cps_and_countdown_widgets():
                for _, animation in app.cps_widgets_animation.items():
                    if animation:
                        animation.stop()
                app.acquisition_time_countdown_widget.setVisible(False)    
        if app.acquisitions_count >= app.selected_average:           
            app.acquisitions_count = 0         
        else:    
            app.acquisitions_count = app.acquisitions_count + 1         
        app.widgets[ACQUISITION_PROGRESS_BAR_WIDGET].update_acquisitions_count()        
        app.notes = ""
        app.control_inputs[STOP_BUTTON].setEnabled(False)
        app.cps_counts.clear()
        free_running = app.free_running_acquisition_time
        if not app_close and ((app.acquisitions_count == app.selected_average) or free_running): 
            QTimer.singleShot(400, clear_cps_and_countdown_widgets)
            app.cps_widgets_animation.clear()                 
            remove_widget(app.layouts[PLOT_GRIDS_CONTAINER], app.widgets[GT_WIDGET_WRAPPER])
            gt_widget = create_gt_loading_layout(app)
            insert_widget(app.layouts[PLOT_GRIDS_CONTAINER], gt_widget, 1)  
        QApplication.processEvents()
        app.intensity_lines.clear()                 
        if not app_close: 
            if app.acquisitions_count == app.selected_average:
                FCSPostProcessing.get_input(app)  
                  
      
            
               

class IntensityTracingButtonsActions:
    @staticmethod    
    def start_button_pressed(app):
        IntensityTracingButtonsActions.clear_intensity_widgets(app)  
        app.acquisition_stopped = False
        app.warning_box = None
        app.settings.setValue(SETTINGS_ACQUISITION_STOPPED, False)
        warn_title, warn_msg = MessagesUtilities.invalid_inputs_handler(
            app.bin_width_micros,
            app.time_span,
            app.acquisition_time_millis,
            app.control_inputs[SETTINGS_FREE_RUNNING_MODE],
            app.enabled_channels,
            app.selected_conn_channel,
        )
        if warn_title and warn_msg:
            message_box = BoxMessage.setup(
                warn_title, warn_msg, QMessageBox.Icon.Warning, GUIStyles.set_msg_box_style(), app.test_mode
            )
            app.warning_box = message_box
            return
        app.control_inputs[START_BUTTON].setEnabled(False)
        app.control_inputs[STOP_BUTTON].setEnabled(app.free_running_acquisition_time)   
        app.last_acquisition_ns = 0
        app.gt_charts.clear()
        if app.acquisitions_count == app.selected_average or app.acquisitions_count == 0:    
            remove_widget(app.layouts[PLOT_GRIDS_CONTAINER], app.widgets[GT_WIDGET_WRAPPER])      
            gt_widget = create_gt_wait_layout(app)
            insert_widget(app.layouts[PLOT_GRIDS_CONTAINER], gt_widget, 1)    
        app.gt_lines.clear()    
        QApplication.processEvents()     
        IntensityTracingButtonsActions.intensity_tracing_start(app)
        if not app.widgets[GT_WIDGET_WRAPPER].isVisible():
            IntensityTracingButtonsActions.show_gt_widget(app, True) 
        IntensityTracing.start_photons_tracing(app)
        
    
    @staticmethod
    def intensity_tracing_start(app, read_data=False):
        if not read_data:
            only_cps_widgets = [item for item in app.enabled_channels if item not in app.intensity_plots_to_show]
            only_cps_widgets.sort()
            for ch in app.enabled_channels:
                app.cps_counts[ch] = {
                    "last_time_ns": 0,
                    "last_count": 0,
                    "current_count": 0,
                }    
            if len(only_cps_widgets) > 0:        
                for index, channel in enumerate(only_cps_widgets):
                    IntensityTracingOnlyCPS.create_only_cps_widget(app, index, channel)                    
        for i, channel in enumerate(app.intensity_plots_to_show):
            if i < len(app.intensity_charts):
                app.intensity_charts[i].show()
            else:
                IntensityTracingPlot.create_chart_widget(app, i, channel, read_data)

                
                   
    @staticmethod    
    def stop_button_pressed(app):
        app.pull_from_queue_timer.stop()   
        try:     
            flim_labs.request_stop()
        except:
            pass    
        def clear_cps_and_countdown_widgets():
                for _, animation in app.cps_widgets_animation.items():
                    if animation:
                        animation.stop()
                app.acquisition_time_countdown_widget.setVisible(False)            
        app.widgets[ACQUISITION_PROGRESS_BAR_WIDGET].clear_acquisition_timer(app)   
        app.control_inputs[START_BUTTON].setEnabled(len(app.enabled_channels) > 0)
        app.control_inputs[STOP_BUTTON].setEnabled(False)  
        free_running = app.free_running_acquisition_time
        if ((app.acquisitions_count == app.selected_average) or free_running): 
            QTimer.singleShot(400, clear_cps_and_countdown_widgets)
            app.cps_widgets_animation.clear()                 
            remove_widget(app.layouts[PLOT_GRIDS_CONTAINER], app.widgets[GT_WIDGET_WRAPPER])
            gt_widget = create_gt_loading_layout(app)
            insert_widget(app.layouts[PLOT_GRIDS_CONTAINER], gt_widget, 1)              
        QApplication.processEvents()
        app.intensity_lines.clear()            
        FCSPostProcessing.get_input(app) 
        
               
    @staticmethod    
    def reset_button_pressed(app):
        app.pull_from_queue_timer.stop()
        time.sleep(0.1)
       
        try:
            flim_labs.request_stop()
        except:
            pass    
        app.last_acquisition_ns = 0  
        app.widgets[ACQUISITION_PROGRESS_BAR_WIDGET].clear_acquisition_timer(app)   
        app.blank_space.show()
        app.control_inputs[START_BUTTON].setEnabled(len(app.enabled_channels) > 0)
        app.control_inputs[STOP_BUTTON].setEnabled(False)
        IntensityTracingButtonsActions.clear_intensity_widgets(app)  
        IntensityTracingButtonsActions.show_gt_widget(app, False)
        QApplication.processEvents()  
        
    
    @staticmethod    
    def clear_intensity_widgets(app):
        app.intensity_lines.clear()             
        app.intensity_charts.clear()
        app.cps_ch.clear()
        app.only_cps_widgets.clear()
        app.intensity_charts_wrappers.clear()
        for chart in app.intensity_charts:
            chart.setParent(None)
            chart.deleteLater()
            del chart
        for cps in app.only_cps_widgets:
            cps.setParent(None)  
            cps.deleteLater()  
            del cps
        for wrapper in app.intensity_charts_wrappers:
            wrapper.setParent(None)
            wrapper.deleteLater() 
            del wrapper 
        for i in reversed(range(app.layouts[INTENSITY_ONLY_CPS_GRID].count())):
            widget = app.layouts[INTENSITY_ONLY_CPS_GRID].itemAt(i).widget()
            if widget is not None:
                app.layouts[INTENSITY_ONLY_CPS_GRID].removeWidget(widget)
                widget.deleteLater()
        for i in reversed(range(app.layouts[INTENSITY_PLOTS_GRID].count())):  
            widget = app.layouts[INTENSITY_PLOTS_GRID].itemAt(i).widget()
            if widget is not None:
                app.layouts[INTENSITY_PLOTS_GRID].removeWidget(widget)
                widget.deleteLater()

    @staticmethod
    def show_gt_widget(app, show):
        if GT_WIDGET_WRAPPER in app.widgets and app.widgets[GT_WIDGET_WRAPPER] is not None:
            app.widgets[GT_WIDGET_WRAPPER].setVisible(show)                    
        


class IntensityTracingPlot:
        
    @staticmethod
    def update_plots2(channel_index, plots_to_show_index, time_ns, intensity, app):
        if plots_to_show_index < len(app.intensity_lines):
            intensity_line = app.intensity_lines[channel_index]
            x, y = intensity_line.getData()
            if x is None or (len(x) == 1 and x[0] == 0):
                x = np.array([time_ns / 1_000_000_000])
                y = np.array([np.sum(intensity)])
            else:
                x = np.append(x, time_ns / 1_000_000_000)
                y = np.append(y, np.sum(intensity))
            if len(x) > 2:
                while x[-1] - x[0] > app.cached_time_span_seconds:
                    x = x[1:]
                    y = y[1:]
            intensity_line.setData(x, y)
            QApplication.processEvents()
            time.sleep(0.01)

                       
    
    @staticmethod 
    def generate_chart(channel_index, app):
        x = np.arange(1)
        y = x * 0
        intensity_widget = pg.PlotWidget()
        intensity_widget.setLabel('left', 'AVG. Photon counts', units='')
        intensity_widget.setLabel('bottom', 'Time', units='s')
        intensity_widget.setTitle("Channel " + str(channel_index + 1))
        intensity_plot = intensity_widget.plot(x, y, pen=pg.mkPen(color="#FB8C00", width=2))
        intensity_widget.setStyleSheet("border: 1px solid #3b3b3b")
        intensity_widget.setBackground("#0E0E0E")
        intensity_widget.getAxis('left').setTextPen('#cecece')
        intensity_widget.getAxis('bottom').setTextPen("#cecece")
        return intensity_widget, intensity_plot
    
    

    @staticmethod
    def create_cps_label():    
        # cps indicator
        cps_label = QLabel("0 CPS")
        return cps_label   
    
    @staticmethod
    def create_countdown_label():
        # acquisition countdown
        countdown_label = QLabel("")
        countdown_label.setStyleSheet(GUIStyles.acquisition_time_countdown_style())
        return countdown_label
    
    

    @staticmethod
    def create_chart_widget(app, index, channel, read_data):
        chart, connector = IntensityTracingPlot.generate_chart(
            app.intensity_plots_to_show[index], app
        )
        cps = IntensityTracingPlot.create_cps_label()
        cps.setStyleSheet(GUIStyles.set_cps_label_style())
        app.cps_widgets_animation[channel] = VibrantAnimation(
            cps,
            stop_color="#a877f7",
            bg_color="transparent",
            start_color="#DA1212",
        )
        
        chart_widget = QWidget()
        chart_layout = QVBoxLayout()
        cps_row = QHBoxLayout()
        cps_row.addWidget(cps)
        cps_row.addStretch(1)
        chart_layout.addLayout(cps_row)
        chart_layout.addWidget(chart)
        chart_widget.setLayout(chart_layout)
        cps.setVisible(app.show_cps and not read_data)
        row, col = divmod(index, 2)
        app.layouts[INTENSITY_PLOTS_GRID].addWidget(chart_widget, row, col)
        app.intensity_charts.append(chart)
        app.intensity_lines[app.intensity_plots_to_show[index]] = connector
        app.intensity_charts_wrappers.append(chart_widget)
        app.cps_ch[channel] = cps
           

class IntensityTracingOnlyCPS:
    @staticmethod
    def create_only_cps_widget(app, index, channel):
        only_cps_widget = QWidget()
        only_cps_widget.setObjectName("container")
        layout_type = "vertical" if app.only_cps_shown is True else "horizontal"
        cps_layout = IntensityTracingOnlyCPS.build_cps_layout(app, channel, layout_type)
        only_cps_widget.setLayout(cps_layout)
        only_cps_widget.setStyleSheet(GUIStyles.only_cps_widget())
        row, col = divmod(index, 2)
        app.layouts[INTENSITY_ONLY_CPS_GRID].addWidget(only_cps_widget, row, col)
        app.only_cps_widgets.append(only_cps_widget)
        

    
    def build_cps_layout(app, channel, layout):
        cps_layout = QHBoxLayout() if layout == 'horizontal' else QVBoxLayout()
        cps = IntensityTracingPlot.create_cps_label()
        cps.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cps.setObjectName("vertical_cps" if layout == 'vertical' else "horizontal_cps")
        app.cps_widgets_animation[channel] = VibrantAnimation(
                cps,
                stop_color="#FB8C00",
                bg_color="transparent",
                start_color="#DA1212",
            )           
        channel_label = QLabel(f"Channel {channel + 1}")
        channel_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        channel_label.setObjectName("vertical_ch" if layout == 'vertical' else "horizontal_ch")
        if layout == 'vertical':
            cps_layout.addStretch(1)
        cps_layout.addWidget(channel_label)
        arrow_icon = QLabel()
        icon = resource_path("assets/arrow-right-grey.png")
        arrow_icon.setPixmap(QPixmap(icon).scaledToWidth(30))
        if layout == 'horizontal':
            cps_layout.addWidget(arrow_icon)
        cps_layout.addWidget(cps)
        cps_layout.addStretch(1)
        app.cps_ch[channel] = cps
        return cps_layout
       
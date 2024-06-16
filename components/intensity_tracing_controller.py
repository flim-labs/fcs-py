import time
import numpy as np
import pyqtgraph as pg
from flim_labs import flim_labs
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
from PyQt6.QtCore import Qt
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
            app.last_cps_update_time.start()  
            app.timer_update_intensity_plots.start(1)
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
                app.last_acquisition_ns = time_ns[0]
                IntensityTracing.process_data(app, time_ns[0], intensities)
                
                  
                
 
   
    @staticmethod                
    def process_data(app, time_ns, counts):
        adjustment = REALTIME_ADJUSTMENT / app.bin_width_micros
        if app.last_cps_update_time.elapsed() >= app.cps_update_interval:
            cps_counts = [0] * 8
            for channel, cps in app.cps_ch.items():
                cps_counts[channel] += counts[channel]
                #print(f"{channel} - {cps_counts[channel]}")
                app.cps_ch[channel].setText(FormatUtils.format_cps(round(cps_counts[channel])) + " CPS")
                app.last_cps_update_time.restart()
        
        for i, channel in enumerate(app.intensity_plots_to_show):
            intensity = counts[channel] / adjustment
            IntensityTracingPlot.update_plots2(channel, time_ns, intensity, app)    
        QApplication.processEvents()             

            
    

    @staticmethod    
    def stop_button_pressed(app, app_close = False):
        app.pull_from_queue_timer.stop() 
        app.timer_update_intensity_plots.stop()
        try:
            flim_labs.request_stop()
        except Exception as e:
            pass 
        if app.acquisitions_count >= app.selected_average:           
            app.acquisitions_count = 0
        else:    
            app.acquisitions_count = app.acquisitions_count + 1         
        app.widgets[ACQUISITION_PROGRESS_BAR_WIDGET].update_acquisitions_count()     
        app.last_cps_update_time.invalidate()     
        app.notes = ""
        app.control_inputs[STOP_BUTTON].setEnabled(False)
        if not app_close and app.acquisitions_count == app.selected_average: 
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
        app.control_inputs[DOWNLOAD_BUTTON].setEnabled(app.write_data and app.acquisition_stopped)
        DataExportActions.set_download_button_icon(app)
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
    def intensity_tracing_start(app):
        only_cps_widgets = [item for item in app.enabled_channels if item not in app.intensity_plots_to_show]
        only_cps_widgets.sort()
        for i, channel in enumerate(app.intensity_plots_to_show):
            if i < len(app.intensity_charts):
                intensity_chart = app.intensity_charts[i]
                intensity_chart.show()
            else:
                IntensityTracingPlot.create_chart_widget(app, i, channel)
        if len(only_cps_widgets) > 0:        
            for index, channel in enumerate(only_cps_widgets):
                IntensityTracingOnlyCPS.create_only_cps_widget(app, index, channel) 
                 
                
                   
    @staticmethod    
    def stop_button_pressed(app):
        app.pull_from_queue_timer.stop()   
        app.timer_update_intensity_plots.stop()
        try:     
            flim_labs.request_stop()
        except:
            pass    
        app.last_cps_update_time.invalidate() 
        app.widgets[ACQUISITION_PROGRESS_BAR_WIDGET].clear_acquisition_timer(app)   
        app.control_inputs[START_BUTTON].setEnabled(len(app.enabled_channels) > 0)
        app.control_inputs[STOP_BUTTON].setEnabled(False)  
        if app.acquisitions_count == app.selected_average:
            remove_widget(app.layouts[PLOT_GRIDS_CONTAINER], app.widgets[GT_WIDGET_WRAPPER]) 
            gt_widget = create_gt_loading_layout(app) 
            insert_widget(app.layouts[PLOT_GRIDS_CONTAINER], gt_widget, 1)               
        QApplication.processEvents()
        app.intensity_lines.clear()            
        FCSPostProcessing.get_input(app) 
        
               
    @staticmethod    
    def reset_button_pressed(app):
        app.pull_from_queue_timer.stop()
        app.timer_update_intensity_plots.stop()
        time.sleep(0.1)
       
        try:
            flim_labs.request_stop()
        except:
            pass    
        app.last_cps_update_time.invalidate() 
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
    def update_plots(app):
        for i, channel in enumerate(app.intensity_plots_to_show):
            if channel < len(app.intensity_lines):
                x, y = app.intensity_lines[channel].getData()
        QApplication.processEvents()
        time.sleep(0.01)
        
        
    @staticmethod    
    def update_plots2(channel_index, time_ns, intensity, app):
        if channel_index < len(app.intensity_lines):
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
        intensity_plot = intensity_widget.plot(x, y, pen="#FB8C00")
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
    def create_chart_widget(app, index, channel):
           chart, connector = IntensityTracingPlot.generate_chart(app.intensity_plots_to_show[index], app)
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
       
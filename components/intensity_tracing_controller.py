
import queue
import threading
import time
import pyqtgraph as pg
from flim_labs import flim_labs
from functools import partial
from pglive.kwargs import Axis
from pglive.sources.data_connector import DataConnector
from pglive.sources.live_axis import LiveAxis
from pglive.sources.live_axis_range import LiveAxisRange
from pglive.sources.live_plot import LiveLinePlot
from pglive.sources.live_plot_widget import LivePlotWidget
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
                write_data=True,  
                acquisition_time_millis=acquisition_time_millis, 
                firmware_file=app.selected_firmware,
            )
            if app.acquisitions_count >= app.selected_average:           
                app.widgets[PROGRESS_BAR_WIDGET].clear_acquisition_timer(app)
            if not free_running_mode:
                app.widgets[PROGRESS_BAR_WIDGET].update_acquisitions_count()
                app.widgets[PROGRESS_BAR_WIDGET].setVisible(True)
            file_bin = result.bin_file
            if file_bin != "":
                print("File bin written in: " + str(file_bin))
            app.blank_space.hide()
            app.pull_from_queue_timer.start(1)
            app.last_cps_update_time.start()  
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
                        IntensityTracingButtonsActions.start_button_pressed(app)
                    else:
                        app.control_inputs[START_BUTTON].setEnabled(len(app.enabled_channels) > 0)     
                    break       
                    
                ((time_ns), (intensities)) = v
                IntensityTracing.calculate_cps(app, time_ns[0], intensities)
                
 
                
    @staticmethod            
    def calculate_cps(app, time_ns, counts):
        if app.last_cps_update_time.elapsed() >= app.cps_update_interval:
            cps_counts = [0] * 8
            for channel, cps in app.cps_ch.items():
                cps_counts[channel] += counts[channel]
                #print(f"{channel} - {cps_counts[channel]}")
                app.cps_ch[channel].setText(FormatUtils.format_cps(round(cps_counts[channel])) + " CPS")
                app.last_cps_update_time.restart()
        for channel, curr_conn in app.intensity_connectors.items():
            curr_conn.cb_append_data_point(y=(counts[channel]), x=(time_ns / NS_IN_S))
        QApplication.processEvents()           

            
    

    @staticmethod    
    def stop_button_pressed(app, app_close = False):
        try:
            flim_labs.request_stop()
        except Exception as e:
            pass 
        time.sleep(0.5)
        if app.acquisitions_count >= app.selected_average:           
            app.acquisition_count = 0
        else:    
            app.acquisitions_count = app.acquisitions_count + 1  
        app.widgets[PROGRESS_BAR_WIDGET].update_acquisitions_count()         
        app.last_cps_update_time.invalidate()     
        app.control_inputs[STOP_BUTTON].setEnabled(False)
        if not app_close and app.acquisitions_count == app.selected_average: 
            remove_widget(app.layouts[PLOT_GRIDS_CONTAINER], app.widgets[GT_WIDGET_WRAPPER])
            gt_widget = create_gt_loading_layout(app)
            insert_widget(app.layouts[PLOT_GRIDS_CONTAINER], gt_widget, 1)  
        QApplication.processEvents()
        app.pull_from_queue_timer.stop() 
        for channel, curr_conn in app.intensity_connectors.items():     
            curr_conn.pause()            
        if not app_close: 
            if app.acquisitions_count == app.selected_average:
                FCSPostProcessing.get_input(app)  
                  
      
            
               

class IntensityTracingButtonsActions:
    @staticmethod    
    def start_button_pressed(app):
        IntensityTracingButtonsActions.clear_intensity_grid_widgets(app) 
        app.acquisition_stopped = False
        app.warning_box = None
        app.settings.setValue(SETTINGS_ACQUISITION_STOPPED, False)
        #app.control_inputs[DOWNLOAD_BUTTON].setEnabled(app.write_data and app.acquisition_stopped)
        #self.set_download_button_icon()
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
        app.intensity_charts.clear()
        app.intensity_lines.clear()
        app.last_acquisition_ns = 0
        app.gt_charts.clear()
        app.cps_ch.clear()
        for chart in app.intensity_charts:
            chart.setVisible(False)
        for chart in app.gt_charts:
            chart.setVisible(False)
        for channel, curr_conn in app.intensity_connectors.items():    
            curr_conn.disconnect()
        remove_widget(app.layouts[PLOT_GRIDS_CONTAINER], app.widgets[GT_WIDGET_WRAPPER])      
        gt_widget = create_gt_wait_layout(app)
        insert_widget(app.layouts[PLOT_GRIDS_CONTAINER], gt_widget, 1)    
        app.intensity_connectors.clear()
        app.gt_lines.clear()         
        app.intensity_charts_wrappers.clear()
        QApplication.processEvents()         
        IntensityTracingButtonsActions.intensity_tracing_start(app)
        if not app.widgets[GT_WIDGET_WRAPPER].isVisible():
            IntensityTracingButtonsActions.show_gt_widget(app, True) 
        IntensityTracing.start_photons_tracing(app)
        
        
    
    @staticmethod    
    def intensity_tracing_start(app):
        only_cps_widgets = [item for item in app.enabled_channels if item not in app.intensity_plots_to_show]
        for i, channel in enumerate(app.intensity_plots_to_show):
            if i < len(app.intensity_charts):
                app.intensity_charts[i].show()
            else:
                IntensityTracingPlot.create_chart_widget(app, i, channel)
        if len(only_cps_widgets) > 0:        
            for index, channel in enumerate(only_cps_widgets):
                IntensityTracingOnlyCPS.create_only_cps_widget(app, index, channel) 
                 
                
                   
    @staticmethod    
    def stop_button_pressed(app):
        try:     
            flim_labs.request_stop()
        except:
            pass    
        app.last_cps_update_time.invalidate() 
        app.widgets[PROGRESS_BAR_WIDGET].clear_acquisition_timer(app)   
        app.control_inputs[START_BUTTON].setEnabled(len(app.enabled_channels) > 0)
        app.control_inputs[STOP_BUTTON].setEnabled(False)  
        remove_widget(app.layouts[PLOT_GRIDS_CONTAINER], app.widgets[GT_WIDGET_WRAPPER]) 
        gt_widget = create_gt_loading_layout(app) 
        insert_widget(app.layouts[PLOT_GRIDS_CONTAINER], gt_widget, 1)               
        QApplication.processEvents()
        app.pull_from_queue_timer.stop()  
        for channel, curr_conn in app.intensity_connectors.items():     
            curr_conn.pause()          
        FCSPostProcessing.get_input(app) 
        
               
    @staticmethod    
    def reset_button_pressed(app):
        try:
            flim_labs.request_stop()
        except:
            pass    
        app.last_cps_update_time.invalidate() 
        app.last_acquisition_ns = 0  
        app.widgets[PROGRESS_BAR_WIDGET].clear_acquisition_timer(app)   
        app.blank_space.show()
        app.control_inputs[START_BUTTON].setEnabled(len(app.enabled_channels) > 0)
        app.control_inputs[STOP_BUTTON].setEnabled(False)
        for chart in app.intensity_charts:
            chart.setParent(None)
            chart.deleteLater()
        for wrapper in app.intensity_charts_wrappers:
            wrapper.setParent(None)
            wrapper.deleteLater()  
        app.intensity_connectors.clear()         
        app.intensity_charts.clear()
        app.cps_ch.clear()
        app.intensity_charts_wrappers.clear()
        IntensityTracingButtonsActions.clear_intensity_grid_widgets(app)  
        IntensityTracingButtonsActions.show_gt_widget(app, False)
        QApplication.processEvents()  
        
    
    @staticmethod    
    def clear_intensity_grid_widgets(app):
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
    def generate_chart(channel_index, app):
        left_axis = LiveAxis("left", axisPen="#cecece", textPen="#cecece")
        bottom_axis = LiveAxis(
            "bottom",
            axisPen="#cecece",
            textPen="#cecece",
            tick_angle=-45,
            **{Axis.TICK_FORMAT: Axis.DURATION, Axis.DURATION_FORMAT: Axis.DF_SHORT},
        )
        plot_widget = LivePlotWidget(
            title="Channel " + str(channel_index + 1),
            y_label="AVG. Photon counts",
            orientation='vertical',
            axisItems={"bottom": bottom_axis, "left": left_axis},
            x_range_controller=LiveAxisRange(roll_on_tick=1),
        )
        plot_widget.getAxis('left').setLabel('AVG. Photon counts', color='#cecece', orientation='vertical')
        plot_curve = LiveLinePlot()
        plot_curve.setPen(pg.mkPen(color="#FB8C00"))
        plot_widget.addItem(plot_curve)
        app.time_span = app.control_inputs[SETTINGS_TIME_SPAN].value()
        connector = DataConnector(
            plot_curve,
            update_rate=10,
            max_points=int((14 * app.time_span)/2),
        )
        plot_widget.setBackground("#0E0E0E")
        plot_widget.setStyleSheet("border: 1px solid #3b3b3b;")
        return plot_widget, connector

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
           app.intensity_connectors[app.intensity_plots_to_show[index]] = connector
           app.intensity_charts_wrappers.append(chart_widget)
           app.cps_ch[channel] = cps
         
           

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
        only_cps_widget.setLayout(row_cps)
        only_cps_widget.setStyleSheet(GUIStyles.only_cps_widget())
        app.cps_ch[channel] = cps
        row, col = divmod(index, 2)
        app.layouts[INTENSITY_ONLY_CPS_GRID].addWidget(only_cps_widget, row, col)
        app.only_cps_widgets.append(only_cps_widget)
      




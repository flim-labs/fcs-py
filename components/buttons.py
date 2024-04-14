
import os
import flim_labs
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QSizePolicy, QMessageBox, QLabel
from PyQt6.QtCore import QPropertyAnimation, QSize, QRect, QEasingCurve, QEventLoop, QTimer
from PyQt6.QtGui import QIcon
from components.resource_path import resource_path
from components.gui_styles import GUIStyles
from components.controls_bar_builder import ControlsBarBuilder
from components.intensity_tracing_controller import IntensityTracing, IntensityTracingPlot, IntensityTracingOnlyCPS
from components.messages_utilities import MessagesUtilities
from components.box_message import BoxMessage
from components.settings import *

current_path = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_path))

class CollapseButton(QWidget):
    def __init__(self, collapsible_widget, parent=None):
        super().__init__(parent)
        self.collapsible_widget = collapsible_widget
        self.collapsed = True
        self.toggle_button = QPushButton()
        self.toggle_button.setIcon(QIcon(resource_path("assets/arrow-up-dark-grey.png")))
        self.toggle_button.setFixedSize(30, 30) 
        self.toggle_button.setStyleSheet(GUIStyles.toggle_collapse_button())
        self.toggle_button.clicked.connect(self.toggle_collapsible)
        self.toggle_button.move(self.toggle_button.x(), self.toggle_button.y() -100)
        layout = QHBoxLayout()
        layout.addStretch(1)
        layout.addWidget(self.toggle_button)
        layout.setSpacing(0)
        layout.setContentsMargins(0,0,0,0)
        self.setLayout(layout)
        self.animation = QPropertyAnimation(self.collapsible_widget, b"maximumHeight")
        self.animation.setDuration(300)

    def toggle_collapsible(self):
        self.collapsed = not self.collapsed
        if self.collapsed:
            self.animation.setStartValue(0)
            self.animation.setEndValue(self.collapsible_widget.sizeHint().height())
            self.toggle_button.setIcon(QIcon(resource_path("assets/arrow-up-dark-grey.png")))
        else:
            self.animation.setStartValue(self.collapsible_widget.sizeHint().height())
            self.animation.setEndValue(0)
            self.toggle_button.setIcon(QIcon(resource_path("assets/arrow-down-dark-grey.png")))
        self.animation.start()
       


class ActionButtons(QWidget):
    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.app = window
        
        layout = self.create_buttons()
        self.setLayout(layout)

    def create_buttons(self):        
        buttons_row_layout, start_button, stop_button, reset_button = ControlsBarBuilder.create_buttons(
            self.start_button_pressed,
            self.stop_button_pressed,
            self.reset_button_pressed,
            self.app.enabled_channels
        )
        self.app.control_inputs[START_BUTTON] = start_button
        self.app.control_inputs[STOP_BUTTON] = stop_button
        self.app.control_inputs[RESET_BUTTON] = reset_button
        return buttons_row_layout 

    def start_button_pressed(self):    
        ButtonsActionsController.start_button_pressed(self.app)

    def stop_button_pressed(self):
        ButtonsActionsController.stop_button_pressed(self.app)

    def reset_button_pressed(self):
        ButtonsActionsController.reset_button_pressed(self.app)        
               


class GTModeButtons(QWidget):
    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.app = window
        
        layout = self.create_buttons()
        self.setLayout(layout)

    def create_buttons(self):            
        buttons_row_layout, realtime_button, post_processing_button = ControlsBarBuilder.create_gt_calc_mode_buttons(
            self.realtime_button_pressed,
            self.post_processing_button_pressed,
            self.app.selected_gt_calc_mode,
        )
        self.app.control_inputs[REALTIME_BUTTON] = realtime_button
        self.app.control_inputs[POST_PROCESSING_BUTTON] = post_processing_button
        return buttons_row_layout    

    def realtime_button_pressed(self, checked):    
        self.app.control_inputs[REALTIME_BUTTON].setChecked(checked)
        self.app.control_inputs[POST_PROCESSING_BUTTON].setChecked(not checked)
        self.app.settings.setValue(SETTINGS_GT_CALC_MODE, 'realtime' if checked else 'post-processing') 
       

    def post_processing_button_pressed(self, checked):
        self.app.control_inputs[REALTIME_BUTTON].setChecked(not checked)
        self.app.control_inputs[POST_PROCESSING_BUTTON].setChecked(checked)  
        self.app.settings.setValue(SETTINGS_GT_CALC_MODE, 'post-processing' if checked else 'realtime') 


class ButtonsActionsController:
    @staticmethod
    def start_button_pressed(app):
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
        app.control_inputs[STOP_BUTTON].setEnabled(True)   
        app.intensity_charts.clear()
        app.intensity_lines.clear()
        app.gt_charts.clear()
        app.cps.clear()
        for chart in app.intensity_charts:
            chart.setVisible(False)
        for chart in app.gt_charts:
            chart.setVisible(False)    
        app.intensity_charts_wrappers.clear()
        ButtonsActionsController.clear_intensity_grid_widgets(app) 
        app.update_plots = True
        ButtonsActionsController.intensity_tracing_start(app)
        if not app.widgets[GT_WIDGET_WRAPPER].isVisible():
            ButtonsActionsController.show_gt_widget(app, True)    
        QApplication.processEvents()
        IntensityTracing.start_photons_tracing(app)


    @staticmethod
    def intensity_tracing_start(app):
        only_cps_widgets = [item for item in app.enabled_channels if item not in app.intensity_plots_to_show]
        for i in range(len(app.intensity_plots_to_show)):
            if i < len(app.intensity_charts):
                app.intensity_charts[i].show()
            else:
                IntensityTracingPlot.create_chart_widget(app, i)
        if len(only_cps_widgets) > 0:        
            for index, channel in enumerate(only_cps_widgets):
                IntensityTracingOnlyCPS.create_only_cps_widget(app, index, channel)



    @staticmethod
    def stop_button_pressed(app):
        app.acquisition_stopped = True
        app.update_plots = False
        app.current_time = 0 
        app.settings.setValue(SETTINGS_ACQUISITION_STOPPED, True)
        #app.control_inputs[DOWNLOAD_BUTTON].setEnabled(app.write_data and app.acquisition_stopped)
        #self.set_download_button_icon()
        app.control_inputs[START_BUTTON].setEnabled(len(app.enabled_channels) > 0)
        app.control_inputs[STOP_BUTTON].setEnabled(False)
        QApplication.processEvents()
        flim_labs.request_stop()
        app.pull_from_queue_timer2.stop() 

    @staticmethod
    def reset_button_pressed(app):
        app.update_plots = False  
        flim_labs.request_stop()
        app.pull_from_queue_timer2.stop()
        app.current_time = 0 
        app.blank_space.show()
        app.acquisition_stopped = False
        app.settings.setValue(SETTINGS_ACQUISITION_STOPPED, False)
        #app.control_inputs[DOWNLOAD_BUTTON].setEnabled(app.write_data and app.acquisition_stopped)
        #self.set_download_button_icon()
        app.control_inputs[START_BUTTON].setEnabled(len(app.enabled_channels) > 0)
        app.control_inputs[STOP_BUTTON].setEnabled(False)
        for chart in app.intensity_charts:
            chart.setParent(None)
            chart.deleteLater()
        for wrapper in app.intensity_charts_wrappers:
            wrapper.setParent(None)
            wrapper.deleteLater()   
        app.intensity_charts.clear()
        app.cps.clear()
        app.intensity_charts_wrappers.clear()
        ButtonsActionsController.clear_intensity_grid_widgets(app)  
        ButtonsActionsController.show_gt_widget(app, False)      

    @staticmethod
    def clear_intensity_grid_widgets(app):
        app.only_cps.clear()
        for i in reversed(range(app.layouts[INTENSITY_ONLY_CPS_GRID].count())):
            widget = app.layouts[INTENSITY_ONLY_CPS_GRID].itemAt(i).widget()
            if widget is not None:
                app.layouts[INTENSITY_ONLY_CPS_GRID].removeWidget(widget)
                widget.deleteLater()
                QApplication.processEvents()
        for i in reversed(range(app.layouts[INTENSITY_PLOTS_GRID].count())):  
            widget = app.layouts[INTENSITY_PLOTS_GRID].itemAt(i).widget()
            if widget is not None:
                app.layouts[INTENSITY_PLOTS_GRID].removeWidget(widget)
                widget.deleteLater()
                QApplication.processEvents()   


    @staticmethod
    def show_gt_widget(app, show):
        if GT_WIDGET_WRAPPER in app.widgets and app.widgets[GT_WIDGET_WRAPPER] is not None:
            app.widgets[GT_WIDGET_WRAPPER].setVisible(show)
    






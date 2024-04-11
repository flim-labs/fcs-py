
import os
import json
import queue
import sys
import time
import flim_labs
import numpy as np
import pyqtgraph as pg
from PyQt6.QtCore import QTimer, QSettings, QSize, Qt, QEvent
from PyQt6.QtGui import QPixmap, QIcon, QAction
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QGridLayout, QHBoxLayout, QLayout, QLabel, \
    QSizePolicy, QPushButton, QDialog, QMessageBox, QMainWindow, QMenu, QRadioButton
from components.fancy_checkbox import FancyButton
from components.gradient_text import GradientText
from components.gui_styles import GUIStyles
from components.format_utilities import FormatUtils
from components.input_number_control import InputNumberControl
from components.link_widget import LinkWidget
from components.layout_utilities import init_ui
from components.logo_utilities import LogoOverlay
from components.resource_path import resource_path
from components.select_control import SelectControl
from components.switch_control import SwitchControl
from components.tau_control import TauControl
from components.top_bar import TopBar
from components.controls_bar import ControlsBar
from components.buttons import CollapseButton
from components.settings import *

current_path = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_path))



class FCSWindow(QWidget):
    def __init__(self):
        super().__init__()
        
        # Initialize settings config
        self.settings = self.init_settings()

        ##### GUI PARAMS #####
        self.firmwares = FIRMWARES
        self.selected_firmware = self.settings.value(SETTINGS_FIRMWARE, DEFAULT_FIRMWARE)
        self.conn_channels = CONN_CHANNELS
        self.selected_conn_channel = self.settings.value(SETTINGS_CONN_CHANNEL, DEFAULT_CONN_CHANNEL)
        self.bin_width_micros = int(self.settings.value(SETTINGS_BIN_WIDTH_MICROS, DEFAULT_BIN_WIDTH_MICROS))
        self.time_span = int(self.settings.value(SETTINGS_TIME_SPAN, DEFAULT_TIME_SPAN))
        default_acquisition_time_millis = self.settings.value(SETTINGS_ACQUISITION_TIME_MILLIS)
        self.acquisition_time_millis = int(default_acquisition_time_millis) if default_acquisition_time_millis is not None else DEFAULT_ACQUISITION_TIME_MILLIS
        self.free_running_acquisition_time = self.settings.value(SETTINGS_FREE_RUNNING_MODE, DEFAULT_FREE_RUNNING_MODE) in ['true', True]    
        self.show_cps = True
        self.write_data = self.settings.value(SETTINGS_WRITE_DATA, DEFAULT_WRITE_DATA) in ['true', True]
        self.acquisition_stopped = False
        default_enabled_channels = self.settings.value(SETTINGS_ENABLED_CHANNELS, DEFAULT_ENABLED_CHANNELS)
        self.enabled_channels = json.loads(default_enabled_channels) if default_enabled_channels is not None else []

        default_taus = self.settings.value(SETTINGS_TAUS_INPUTS, TAUS_INPUTS)
        self.taus = json.loads(default_taus) if default_taus is not None else []

        default_enabled_tau = self.settings.value(SETTINGS_TAU, DEFAULT_TAU)
        self.selected_tau = json.loads(default_enabled_tau) if default_enabled_tau is not None else []
        self.control_inputs = {}
        self.widgets = {}
        self.layouts = {}
        self.bin_file_size = ''
        self.bin_file_size_label = QLabel("")
        self.selected_gt_calc_mode = self.settings.value(SETTINGS_GT_CALC_MODE, DEFAULT_GT_CALC_MODE).strip('"')

        self.warning_box = None

        #### LAYOUT ###
        self.channel_checkboxes = []
        self.logo_overlay = LogoOverlay(self)
        self.installEventFilter(self)

        GUIStyles.set_fonts()
        self.top_utilities_layout = QVBoxLayout()
        self.blank_space = QWidget()

        self.main_layout, self.charts_grid = self.init_ui()
        

    @staticmethod    
    def init_settings():
        settings = QSettings('settings.ini', QSettings.Format.IniFormat)
        return settings    

    def init_ui(self):
        self.create_top_utilities_layout()
        main_layout, charts_grid = init_ui(self, self.top_utilities_layout)
        return main_layout, charts_grid
       

    def create_top_utilities_layout(self):    
        self.top_utilities_layout = QVBoxLayout()
        header_layout = self.create_header_layout()
        self.top_utilities_layout.addLayout(header_layout)
        channel_checkbox_layout = self.create_channels_grid()
        tau_component = self.create_tau_inputs_grid()
        self.widgets[TAU_COMPONENT] = tau_component
        ch_and_tau_widget = QWidget()
        ch_and_tau_box = QVBoxLayout()
        ch_and_tau_widget.setLayout(ch_and_tau_box)
        ch_and_tau_box.addLayout(channel_checkbox_layout)
        ch_and_tau_box.addWidget(tau_component)
        self.widgets[CHECKBOX_CONTROLS] = ch_and_tau_widget
        self.top_utilities_layout.addWidget(ch_and_tau_widget)
        controls_layout = self.create_controls_layout()
        self.top_utilities_layout.addLayout(controls_layout)
        self.top_utilities_layout.addWidget(self.blank_space)  

    def create_header_layout(self):   
        title_row = self.create_logo_and_title()
        gt_calc_mode_buttons_row_layout = self.create_gt_calc_mode_buttons()
        info_link_widget, export_data_control = self.create_export_data_input()
        file_size_info_layout = self.create_file_size_info_row()
        download_button, download_menu = self.create_download_files_menu()
        header_layout = TopBar.create_header_layout(
            title_row,
            file_size_info_layout,
            info_link_widget,
            export_data_control,
            download_button,
            download_menu,
            gt_calc_mode_buttons_row_layout
        )
        return header_layout 

    def create_logo_and_title(self):   
        title_row = TopBar.create_logo_and_title(self)
        return title_row    

    def create_export_data_input(self):    
        info_link_widget, export_data_control, inp = TopBar.create_export_data_input(self.write_data, self.toggle_export_data)
        self.control_inputs[SETTINGS_WRITE_DATA] = inp
        return info_link_widget, export_data_control

    def create_file_size_info_row(self):
        file_size_info_layout = TopBar.create_file_size_info_row(
            self.bin_file_size,
            self.bin_file_size_label,
            self.write_data,
            self.calc_exported_file_size)
        return file_size_info_layout

    def create_download_files_menu(self):
        download_button, download_menu = TopBar.create_download_files_menu(
            self,
            self.write_data,
            self.acquisition_stopped,
            self.show_download_options,
            self.download_matlab,
            self.download_python
        )
        self.control_inputs[DOWNLOAD_BUTTON] = download_button
        self.control_inputs[DOWNLOAD_MENU] = download_menu
        self.set_download_button_icon()
        return download_button, download_menu
        
    def create_channels_grid(self):          
        ch_grid = QHBoxLayout()
        for i in range(MAX_CHANNELS):
            from components.fancy_checkbox import FancyCheckbox
            fancy_checkbox_wrapper = QWidget()  
            fancy_checkbox_wrapper.setObjectName(f"fancy_checkbox_wrapper")
            fancy_checkbox = FancyCheckbox(text=f"Channel {i + 1}")
            checked = any(channel.get("ch") == i for channel in self.enabled_channels)
            fancy_checkbox.set_checked(checked)
            fancy_checkbox.toggled.connect(lambda checked, index=i: self.on_channel_selected(checked, index))
            row = QHBoxLayout()
            row.addWidget(fancy_checkbox)
            fancy_checkbox_wrapper.setLayout(row)
            fancy_checkbox_wrapper.setStyleSheet(GUIStyles.checkbox_wrapper_style())
            ch_grid.addWidget(fancy_checkbox_wrapper)
            self.channel_checkboxes.append(fancy_checkbox)
        return ch_grid  



    def create_tau_inputs_grid(self):
        tau_component = TauControl(self)
        return tau_component

    def create_controls_layout(self):    
        controls_row = self.create_controls()
        buttons_row_layout = self.create_buttons()
        collapse_button = CollapseButton(self.widgets[CHECKBOX_CONTROLS])
        buttons_row_layout.addWidget(collapse_button)
        blank_space, controls_layout = ControlsBar.init_gui_controls_layout(controls_row, buttons_row_layout)
        self.blank_space = blank_space
        return controls_layout


    def create_controls(self):    
        controls_row = QHBoxLayout()
        self.create_channel_type_control(controls_row)
        self.create_bin_width_control(controls_row)
        running_mode_control = self.create_running_mode_control()
        controls_row.addLayout(running_mode_control)
        controls_row.addSpacing(15)
        self.create_time_span_control(controls_row)
        self.create_acquisition_time_control(controls_row)
        return controls_row


    def create_buttons(self):    
        buttons_row_layout, start_button, stop_button, reset_button = ControlsBar.create_buttons(
            self.start_button_pressed,
            self.stop_button_pressed,
            self.reset_button_pressed,
            self.channel_checkboxes
        )
        self.control_inputs[START_BUTTON] = start_button
        self.control_inputs[STOP_BUTTON] = stop_button
        self.control_inputs[RESET_BUTTON] = reset_button
        return buttons_row_layout


    def create_gt_calc_mode_buttons(self):        
        buttons_row_layout, realtime_button, post_processing_button = ControlsBar.create_gt_calc_mode_buttons(
            self.realtime_button_pressed,
            self.post_processing_button_pressed,
            self.selected_gt_calc_mode,
        )
        self.control_inputs[REALTIME_BUTTON] = realtime_button
        self.control_inputs[POST_PROCESSING_BUTTON] = post_processing_button
        return buttons_row_layout    

    def create_channel_type_control(self, controls_row):    
        inp = ControlsBar.create_channel_type_control(
            controls_row,
            self.selected_conn_channel,
            self.conn_channel_type_value_change,
            self.conn_channels)
        self.control_inputs[SETTINGS_CONN_CHANNEL] = inp

    def create_bin_width_control(self, controls_row):    
        inp = ControlsBar.create_bin_width_control(
            controls_row,
            self.bin_width_micros,
            self.bin_width_micros_value_change, )
        self.control_inputs[SETTINGS_BIN_WIDTH_MICROS] = inp

    def create_running_mode_control(self):    
        running_mode_control, inp = ControlsBar.create_running_mode_control(
            self.free_running_acquisition_time,
            self.toggle_acquisition_time_mode,
        )
        self.control_inputs[SETTINGS_FREE_RUNNING_MODE] = inp
        return running_mode_control

    def create_time_span_control(self, controls_row):    
        inp = ControlsBar.create_time_span_control(
            controls_row,
            self.time_span,
            self.time_span_value_change, )
        self.control_inputs[SETTINGS_TIME_SPAN] = inp 

    def create_acquisition_time_control(self, controls_row):    
        inp = ControlsBar.create_acquisition_time_control(
            controls_row,
            self.acquisition_time_millis,
            self.acquisition_time_value_change,
            self.control_inputs[SETTINGS_FREE_RUNNING_MODE]
        )
        self.control_inputs[SETTINGS_ACQUISITION_TIME_MILLIS] = inp  


    def toggle_export_data(self, state):    
        if state:
            self.write_data = True
            self.control_inputs[DOWNLOAD_BUTTON].setEnabled(self.write_data and self.acquisition_stopped)
            self.set_download_button_icon()
            self.settings.setValue(SETTINGS_WRITE_DATA, True)
            self.bin_file_size_label.show()
            self.calc_exported_file_size()
        else:
            self.write_data = False
            self.control_inputs[DOWNLOAD_BUTTON].setEnabled(self.write_data and self.acquisition_stopped)
            self.set_download_button_icon()
            self.settings.setValue(SETTINGS_WRITE_DATA, False)
            self.bin_file_size_label.hide()
            
    def on_channel_selected(self, checked: bool, index: int):
        found = any(channel.get("ch") == index for channel in self.enabled_channels) 
        if checked:
            if not found:
                self.enabled_channels.append({"ch": index, "auto_corr" : False, "cross_corr": False  })
        else:
            self.enabled_channels = [ch for ch in self.enabled_channels if ch.get("ch") != index]
        self.settings.setValue(SETTINGS_ENABLED_CHANNELS, json.dumps(self.enabled_channels)) 

    def toggle_acquisition_time_mode(self, state):    
        if state:
            self.control_inputs[SETTINGS_ACQUISITION_TIME_MILLIS].setEnabled(False)
            self.free_running_acquisition_time = True
            self.settings.setValue(SETTINGS_FREE_RUNNING_MODE, True)
        else:
            self.control_inputs[SETTINGS_ACQUISITION_TIME_MILLIS].setEnabled(True)
            self.free_running_acquisition_time = False
            self.settings.setValue(SETTINGS_FREE_RUNNING_MODE, False)




    def conn_channel_type_value_change(self, index):   
        self.selected_conn_channel = self.sender().currentText()
        if self.selected_conn_channel == "USB":
            self.selected_firmware = self.firmwares[0]
        else:
            self.selected_firmware = self.firmwares[1]
        self.settings.setValue(SETTINGS_FIRMWARE, self.selected_firmware)
        self.settings.setValue(SETTINGS_CONN_CHANNEL, self.selected_conn_channel) 


    def acquisition_time_value_change(self, value):    
        self.control_inputs[START_BUTTON].setEnabled(value != 0)
        self.acquisition_time_millis = value * 1000  # convert s to ms
        self.settings.setValue(SETTINGS_ACQUISITION_TIME_MILLIS, self.acquisition_time_millis)
        self.calc_exported_file_size()


    def time_span_value_change(self, value):    
        self.control_inputs[START_BUTTON].setEnabled(value != 0)
        self.time_span = value
        self.settings.setValue(SETTINGS_TIME_SPAN, value) 


    def bin_width_micros_value_change(self, value):    
        self.control_inputs[START_BUTTON].setEnabled(value != 0)
        self.bin_width_micros = value
        self.settings.setValue(SETTINGS_BIN_WIDTH_MICROS, value)
        self.calc_exported_file_size()


    def realtime_button_pressed(self, checked):
        self.control_inputs[REALTIME_BUTTON].setChecked(checked)
        self.control_inputs[POST_PROCESSING_BUTTON].setChecked(not checked)
        self.settings.setValue(SETTINGS_GT_CALC_MODE, 'realtime' if checked else 'post-processing') 
       

    def post_processing_button_pressed(self, checked):
        self.control_inputs[REALTIME_BUTTON].setChecked(not checked)
        self.control_inputs[POST_PROCESSING_BUTTON].setChecked(checked)  
        self.settings.setValue(SETTINGS_GT_CALC_MODE, 'post-processing' if checked else 'realtime') 


    def start_button_pressed(self):
        return

    def stop_button_pressed(self):
        return

    def reset_button_pressed(self):
        return        

    def calc_exported_file_size(self):
        return

    def show_download_options(self):    
        self.control_inputs[DOWNLOAD_MENU].exec_(self.control_inputs[DOWNLOAD_BUTTON].mapToGlobal(QPoint(0, self.control_inputs[DOWNLOAD_BUTTON].height())))

    def download_matlab(self):
        MatlabScriptUtils.download_matlab(self)
        self.control_inputs[DOWNLOAD_BUTTON].setEnabled(False)
        self.control_inputs[DOWNLOAD_BUTTON].setEnabled(True)

    def download_python(self):
        PythonScriptUtils.download_python(self)
        self.control_inputs[DOWNLOAD_BUTTON].setEnabled(False)
        self.control_inputs[DOWNLOAD_BUTTON].setEnabled(True)

    def set_download_button_icon(self):
        if self.control_inputs[DOWNLOAD_BUTTON].isEnabled():
            icon = resource_path("assets/arrow-down-icon-white.png")
            self.control_inputs[DOWNLOAD_BUTTON].setIcon(QIcon(icon))
        else:
            icon = resource_path("assets/arrow-down-icon-grey.png")
            self.control_inputs[DOWNLOAD_BUTTON].setIcon(QIcon(icon)) 


    def resizeEvent(self, event):  
        super(FCSWindow, self).resizeEvent(event)
        self.logo_overlay.update_position(self)
        self.logo_overlay.update_visibility(self) 
        self.widgets[TAU_COMPONENT].update_layout()  


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FCSWindow()
    window.show()
    sys.exit(app.exec())

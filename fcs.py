
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
from components.channels_control import ChannelsControl
from components.top_bar_builder import TopBarBuilder
from components.controls_bar_builder import ControlsBarBuilder
from components.buttons import CollapseButton, ActionButtons, GTModeButtons
from components.input_params_controls import InputParamsControls
from components.data_export_controls import ExportDataControl, DownloadDataControl
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
        
        self.taus = TAUS_INPUTS
        self.selected_tau = self.settings.value(SETTINGS_TAU, DEFAULT_TAU)

        default_ch_correlations = self.settings.value(SETTINGS_CH_CORRELATIONS, DEFAULT_CH_CORRELATIONS)
        self.ch_correlations = json.loads(default_ch_correlations) if default_ch_correlations is not None else []

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
        channels_component = self.create_channels_grid()
        self.widgets[CHANNELS_COMPONENT] = channels_component
        ch_and_tau_widget = QWidget()
        ch_and_tau_box = QVBoxLayout()
        ch_and_tau_box.setSpacing(0)
        ch_and_tau_widget.setLayout(ch_and_tau_box)
        ch_and_tau_box.addWidget(channels_component)
        self.widgets[CHECKBOX_CONTROLS] = ch_and_tau_widget
        self.top_utilities_layout.addWidget(ch_and_tau_widget)
        controls_layout = self.create_controls_layout()
        self.top_utilities_layout.addLayout(controls_layout)
        self.top_utilities_layout.addWidget(self.blank_space)  

    def create_header_layout(self):   
        title_row = self.create_logo_and_title()
        gt_calc_mode_buttons_row_layout = self.create_gt_calc_mode_buttons()
        export_data_widget = ExportDataControl(self)
        download_button = self.create_download_files_menu()
        header_layout = TopBarBuilder.create_header_layout(
            title_row,
            export_data_widget,
            download_button,
            gt_calc_mode_buttons_row_layout
        )
        return header_layout 

    def create_logo_and_title(self):   
        title_row = TopBarBuilder.create_logo_and_title(self)
        return title_row    


    def create_download_files_menu(self):
        download_button = DownloadDataControl(self)
        return download_button
        
    def create_channels_grid(self):          
        channels_component = ChannelsControl(self)
        return channels_component


    def create_controls_layout(self):    
        controls_row = self.create_controls()
        buttons_row_layout = QHBoxLayout()
        buttons_widget = self.create_buttons()
        buttons_row_layout.addStretch(1)
        buttons_row_layout.addWidget(buttons_widget)
        collapse_button = CollapseButton(self.widgets[CHECKBOX_CONTROLS])
        buttons_row_layout.addWidget(collapse_button)
        blank_space, controls_layout = ControlsBarBuilder.init_gui_controls_layout(controls_row, buttons_row_layout)
        self.blank_space = blank_space
        return controls_layout


    def create_controls(self):    
        controls_row = InputParamsControls(self)
        return controls_row


    def create_buttons(self):    
        buttons_row_layout = ActionButtons(self)
        return buttons_row_layout

    def create_gt_calc_mode_buttons(self):        
        buttons_row_layout = GTModeButtons(self)
        return buttons_row_layout    


    def calc_exported_file_size(self):
        return


    def resizeEvent(self, event):  
        super(FCSWindow, self).resizeEvent(event)
        self.logo_overlay.update_position(self)
        self.logo_overlay.update_visibility(self) 
    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FCSWindow()
    window.show()
    sys.exit(app.exec())

import os
from PyQt6.QtWidgets import QWidget, QHBoxLayout
from components.controls_bar_builder import ControlsBarBuilder
from components.data_export_controls import DataExportActions
from components.settings import *

current_path = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_path))


class InputParamsControls(QWidget):
    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.app = window
        layout = QHBoxLayout()
        self.setLayout(layout)
        self.create_bin_width_control(layout)
        self.create_tau_scale_control(layout)
        self.create_fcs_algorithm_control(layout)
        running_mode_control = self.create_running_mode_control()
        layout.addLayout(running_mode_control)
        layout.addSpacing(15)
        self.create_time_span_control(layout)
        self.create_acquisition_time_control(layout)
        self.create_averages_control(layout)
        self.create_cps_threshold_control(layout)


    def create_tau_control(self, layout):
        inp = ControlsBarBuilder.create_tau_control(
            layout, self.app.selected_tau, self.tau_value_change, self.app.taus
        )
        self.app.control_inputs[SETTINGS_TAU] = inp

    def create_averages_control(self, layout):
        inp = ControlsBarBuilder.create_averages_control(
            layout,
            self.app.selected_average,
            self.averages_value_change,
            self.app.averages_inputs,
            self.app.control_inputs[SETTINGS_FREE_RUNNING_MODE],
        )
        self.app.control_inputs[SETTINGS_AVERAGES] = inp

    def create_bin_width_control(self, layout):
        inp = ControlsBarBuilder.create_bin_width_control(
            layout,
            self.app.bin_width_micros,
            self.bin_width_micros_value_change,
            self.app.bin_width_inputs,
        )
        self.app.control_inputs[SETTINGS_BIN_WIDTH_MICROS] = inp

    def create_running_mode_control(self):
        running_mode_control, inp = ControlsBarBuilder.create_running_mode_control(
            self.app.free_running_acquisition_time,
            self.toggle_acquisition_time_mode,
        )
        self.app.control_inputs[SETTINGS_FREE_RUNNING_MODE] = inp
        return running_mode_control

    def create_time_span_control(self, layout):
        inp = ControlsBarBuilder.create_time_span_control(
            layout,
            self.app.time_span,
            self.time_span_value_change,
        )
        self.app.control_inputs[SETTINGS_TIME_SPAN] = inp

    def create_acquisition_time_control(self, layout):
        inp = ControlsBarBuilder.create_acquisition_time_control(
            layout,
            self.app.acquisition_time_millis,
            self.acquisition_time_value_change,
            self.app.control_inputs[SETTINGS_FREE_RUNNING_MODE],
        )
        self.app.control_inputs[SETTINGS_ACQUISITION_TIME_MILLIS] = inp

    def toggle_acquisition_time_mode(self, state):
        if state:
            self.app.control_inputs[SETTINGS_ACQUISITION_TIME_MILLIS].setEnabled(False)
            self.app.control_inputs[SETTINGS_AVERAGES].setEnabled(False)
            self.app.free_running_acquisition_time = True
            self.app.settings.setValue(SETTINGS_FREE_RUNNING_MODE, True)
        else:
            self.app.control_inputs[SETTINGS_ACQUISITION_TIME_MILLIS].setEnabled(True)
            self.app.control_inputs[SETTINGS_AVERAGES].setEnabled(True)
            self.app.free_running_acquisition_time = False
            self.app.settings.setValue(SETTINGS_FREE_RUNNING_MODE, False)
        DataExportActions.calc_exported_file_size(self.app)    
            
    def create_cps_threshold_control(self, layout):
            value = int(self.app.settings.value(SETTINGS_CPS_THRESHOLD, DEFAULT_CPS_THRESHOLD))
            inp = ControlsBarBuilder.create_cps_threshold_control(
                layout,
                value,
                self.cps_threshold_value_change,
                self.app.show_cps  
            )
            self.app.control_inputs[SETTINGS_CPS_THRESHOLD] = inp            
            

    def acquisition_time_value_change(self, value):
        self.app.control_inputs[START_BUTTON].setEnabled(value != 0)
        self.app.acquisition_time_millis = value * 1000  # convert s to ms
        self.app.settings.setValue(
            SETTINGS_ACQUISITION_TIME_MILLIS, self.app.acquisition_time_millis
        )
        DataExportActions.calc_exported_file_size(self.app)

    def time_span_value_change(self, value):
        self.app.control_inputs[START_BUTTON].setEnabled(value != 0)
        self.app.time_span = value
        self.app.settings.setValue(SETTINGS_TIME_SPAN, value)
        
    def cps_threshold_value_change(self, value):
        self.app.cps_threshold = value
        self.app.settings.setValue(SETTINGS_CPS_THRESHOLD, value)          

    def tau_value_change(self, index):
        value = self.sender().currentText()
        self.app.selected_tau = value
        self.app.settings.setValue(SETTINGS_TAU, self.app.selected_tau)

    def bin_width_micros_value_change(self, value):
        value = self.sender().currentText()
        self.app.bin_width_micros = int(value)
        self.app.settings.setValue(SETTINGS_BIN_WIDTH_MICROS, int(value))
        DataExportActions.calc_exported_file_size(self.app)
        
    def averages_value_change(self, value):
        value = self.sender().currentText()
        self.app.selected_average = int(value)
        self.app.settings.setValue(SETTINGS_AVERAGES, int(value))
        self.app.acquisitions_count = 0
        DataExportActions.calc_exported_file_size(self.app)

    def create_tau_scale_control(self, layout):
        options = self.app.tau_axis_scales
        inp = ControlsBarBuilder.create_tau_scale_control(
            layout,
            self.app.tau_axis_scale,
            self.tau_scale_value_change,
            options,
        )
        self.app.control_inputs["tau_scale"] = inp
        
    def create_fcs_algorithm_control(self, layout):    
        options = self.app.fcs_algorithms
        inp = ControlsBarBuilder.create_fcs_algorithm_control(
            layout,
            self.app.fcs_algorithm,
            self.fcs_algorithm_value_change,
            options,
        )
        self.app.control_inputs["fcs_algorithm"] = inp 
        

    def tau_scale_value_change(self, idx):
        options = self.app.tau_axis_scales
        self.app.tau_axis_scale = options[idx]
        self.app.settings.setValue(SETTINGS_TAU_AXIS_SCALE, self.app.tau_axis_scale)
        DataExportActions.calc_exported_file_size(self.app)
        

    def fcs_algorithm_value_change(self, idx):
        options = self.app.fcs_algorithms
        self.app.fcs_algorithm = options[idx]
        self.app.settings.setValue(SETTINGS_FCS_ALGORITHM, self.app.fcs_algorithm)
          


import os
from PyQt6.QtWidgets import QWidget, QHBoxLayout
from components.controls_bar_builder import ControlsBarBuilder
from components.settings import *
current_path = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_path))


class InputParamsControls(QWidget):
    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.app = window
        layout = QHBoxLayout()
        self.setLayout(layout)
        self.create_channel_type_control(layout)
        self.create_bin_width_control(layout)
        running_mode_control = self.create_running_mode_control()
        layout.addLayout(running_mode_control)
        layout.addSpacing(15)
        self.create_time_span_control(layout)
        self.create_acquisition_time_control(layout)


    def create_channel_type_control(self, layout):        
        inp = ControlsBarBuilder.create_channel_type_control(
            layout,
            self.app.selected_conn_channel,
            self.conn_channel_type_value_change,
            self.app.conn_channels)
        self.app.control_inputs[SETTINGS_CONN_CHANNEL] = inp


    def create_tau_control(self, layout):            
        inp = ControlsBarBuilder.create_tau_control(
            layout,
            self.app.selected_tau,
            self.tau_value_change,
            self.app.taus)
        self.app.control_inputs[SETTINGS_TAU] = inp


    def create_bin_width_control(self, layout):        
        inp = ControlsBarBuilder.create_bin_width_control(
            layout,
            self.app.bin_width_micros,
             self.bin_width_micros_value_change,
            self.app.bin_width_inputs, )
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
            self.time_span_value_change, )
        self.app.control_inputs[SETTINGS_TIME_SPAN] = inp 


    def create_acquisition_time_control(self, layout):        
        inp = ControlsBarBuilder.create_acquisition_time_control(
            layout,
            self.app.acquisition_time_millis,
            self.acquisition_time_value_change,
            self.app.control_inputs[SETTINGS_FREE_RUNNING_MODE]
        )
        self.app.control_inputs[SETTINGS_ACQUISITION_TIME_MILLIS] = inp   

    def toggle_acquisition_time_mode(self, state):       
        if state:
            self.app.control_inputs[SETTINGS_ACQUISITION_TIME_MILLIS].setEnabled(False)
            self.app.free_running_acquisition_time = True
            self.app.settings.setValue(SETTINGS_FREE_RUNNING_MODE, True)
        else:
            self.app.control_inputs[SETTINGS_ACQUISITION_TIME_MILLIS].setEnabled(True)
            self.app.free_running_acquisition_time = False
            self.app.settings.setValue(SETTINGS_FREE_RUNNING_MODE, False)

    def conn_channel_type_value_change(self, index):       
        self.app.selected_conn_channel = self.sender().currentText()
        if self.app.selected_conn_channel == "USB":
            self.app.selected_firmware = self.app.firmwares[0]
        else:
            self.app.selected_firmware = self.app.firmwares[1]
        self.app.settings.setValue(SETTINGS_FIRMWARE, self.app.selected_firmware)
        self.app.settings.setValue(SETTINGS_CONN_CHANNEL, self.app.selected_conn_channel) 

    def acquisition_time_value_change(self, value):        
        self.app.control_inputs[START_BUTTON].setEnabled(value != 0)
        self.app.acquisition_time_millis = value * 1000  # convert s to ms
        self.app.settings.setValue(SETTINGS_ACQUISITION_TIME_MILLIS, self.app.acquisition_time_millis)
        #self.calc_exported_file_size()    

    def time_span_value_change(self, value):        
        self.app.control_inputs[START_BUTTON].setEnabled(value != 0)
        self.app.time_span = value
        self.app.settings.setValue(SETTINGS_TIME_SPAN, value)

    def tau_value_change(self, index):
        value = self.sender().currentText()
        self.app.selected_tau = value
        self.app.settings.setValue(SETTINGS_TAU, self.app.selected_tau)    

    def bin_width_micros_value_change(self, value):
        value = self.sender().currentText()   
        self.app.bin_width_micros = int(value)   
        self.app.settings.setValue(SETTINGS_BIN_WIDTH_MICROS, int(value)) 
        #self.calc_exported_file_size()         




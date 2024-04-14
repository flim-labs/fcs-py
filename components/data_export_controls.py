import os
import json
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QGridLayout, QSizePolicy, QCheckBox, QLabel, QLineEdit
from PyQt6.QtCore import QPropertyAnimation, QSize, QRect, QEasingCurve, Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QColor, QIntValidator
from components.resource_path import resource_path
from components.gui_styles import GUIStyles
from components.logo_utilities import LogoOverlay, TitlebarIcon
from components.top_bar_builder import TopBarBuilder
from components.settings import *

current_path = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_path))


class ExportDataControl(QWidget):
    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.app = window
        self.info_link_widget, self.export_data_control = self.create_export_data_input()
        self.file_size_info_layout = self.create_file_size_info_row()
        layout = QHBoxLayout()
        layout.addWidget(self.info_link_widget)
        layout.addLayout(self.export_data_control)
        self.export_data_control.addSpacing(10)
        layout.addLayout(self.file_size_info_layout)

        self.setLayout(layout)

    def create_export_data_input(self):        
        info_link_widget, export_data_control, inp = TopBarBuilder.create_export_data_input(self.app.write_data, self.toggle_export_data)
        self.app.control_inputs[SETTINGS_WRITE_DATA] = inp
        return info_link_widget, export_data_control 

    def create_file_size_info_row(self):    
        file_size_info_layout = TopBarBuilder.create_file_size_info_row(
            self.app.bin_file_size,
            self.app.bin_file_size_label,
            self.app.write_data,
            self.app.calc_exported_file_size)
        return file_size_info_layout 

    def toggle_export_data(self, state):        
        if state:
            self.app.write_data = True
            self.app.control_inputs[DOWNLOAD_BUTTON].setEnabled(self.app.write_data and self.app.acquisition_stopped)
            #self.set_download_button_icon()
            self.app.settings.setValue(SETTINGS_WRITE_DATA, True)
            self.app.bin_file_size_label.show()
            self.app.calc_exported_file_size()
        else:
            self.app.write_data = False
            self.app.control_inputs[DOWNLOAD_BUTTON].setEnabled(self.app.write_data and self.app.acquisition_stopped)
            #self.set_download_button_icon()
            self.app.settings.setValue(SETTINGS_WRITE_DATA, False)
            self.app.bin_file_size_label.hide()          



class DownloadDataControl(QWidget):
    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.app = window
        self.download_button, self.download_menu = self.create_download_files_menu()
        layout = QHBoxLayout()
        layout.addWidget(self.download_button)

        self.setLayout(layout)

    def create_download_files_menu(self):    
        download_button, download_menu = TopBarBuilder.create_download_files_menu(
            self.app,
            self.app.write_data,
            self.app.acquisition_stopped,
            self.show_download_options,
            self.download_matlab,
            self.download_python
        )
        self.app.control_inputs[DOWNLOAD_BUTTON] = download_button
        self.app.control_inputs[DOWNLOAD_MENU] = download_menu
        self.set_download_button_icon()
        return download_button, download_menu 

    def show_download_options(self):    
        self.app.control_inputs[DOWNLOAD_MENU].exec_(self.app.control_inputs[DOWNLOAD_BUTTON].mapToGlobal(QPoint(0, self.app.control_inputs[DOWNLOAD_BUTTON].height())))
       
    def download_matlab(self):    
        #MatlabScriptUtils.download_matlab(self)
        self.app.control_inputs[DOWNLOAD_BUTTON].setEnabled(False)
        self.app.control_inputs[DOWNLOAD_BUTTON].setEnabled(True)

    def download_python(self):
        #PythonScriptUtils.download_python(self)
        self.app.control_inputs[DOWNLOAD_BUTTON].setEnabled(False)
        self.app.control_inputs[DOWNLOAD_BUTTON].setEnabled(True) 

    def set_download_button_icon(self):
        if self.app.control_inputs[DOWNLOAD_BUTTON].isEnabled():
            icon = resource_path("assets/arrow-down-icon-white.png")
            self.app.control_inputs[DOWNLOAD_BUTTON].setIcon(QIcon(icon))
        else:
            icon = resource_path("assets/arrow-down-icon-grey.png")
            self.app.control_inputs[DOWNLOAD_BUTTON].setIcon(QIcon(icon))       
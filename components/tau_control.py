
import os
import json
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QGridLayout, QSizePolicy, QCheckBox, QLabel, QLineEdit
from PyQt6.QtCore import QPropertyAnimation, QSize, QRect, QEasingCurve, Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QColor, QIntValidator
from components.resource_path import resource_path
from components.gui_styles import GUIStyles
from components.logo_utilities import LogoOverlay, TitlebarIcon
from components.settings import *

current_path = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_path))

class TauControl(QWidget):
    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.main_window = window
        layout = QVBoxLayout()
        self.tau_grid = QGridLayout()
        layout.addLayout(self.tau_grid)
        self.setLayout(layout)
        self.tau_checkboxes = []
        self.add_tau_btn = QPushButton("ADD TAU +")
        self.add_tau_btn.setFixedWidth(100) 
        self.add_tau_btn.setStyleSheet(GUIStyles.add_tau_btn_style())
        self.add_tau_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_tau_btn.clicked.connect(self.open_add_tau_popup)
        self.widgets = [self.add_tau_btn] + self.tau_checkboxes
        self.init_tau_grid()


    def init_tau_grid(self):
        self.tau_grid.addWidget(self.add_tau_btn)
        self.update_tau_checkboxes()        
        self.update_layout()

    def update_tau_checkboxes(self):
        for tau in self.main_window.taus:
            tau_checkbox_wrapper = QWidget() 
            tau_checkbox_wrapper.setObjectName(f"tau_checkbox_wrapper")
            tau_row = QHBoxLayout()
            checkbox = QCheckBox(str(tau)+ 'us')
            checkbox.setStyleSheet(GUIStyles.set_tau_checkbox_style())
            checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
            checkbox.setChecked(True) if tau in self.main_window.selected_tau else checkbox.setChecked(False)
            checkbox.toggled.connect(lambda state, tau=tau: self.on_tau_toggled(state, tau))
            remove_btn = QPushButton()
            remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            remove_btn.setIcon(QIcon(resource_path("assets/close-icon-white.png")))
            remove_btn.setFixedSize(20, 20) 
            remove_btn.setStyleSheet(GUIStyles.remove_tau_button())
            remove_btn.clicked.connect(lambda state, tau=tau: self.on_remove_tau(state, tau))
            tau_row.addWidget(checkbox)
            tau_row.addWidget(remove_btn)
            tau_checkbox_wrapper.setLayout(tau_row)
            tau_checkbox_wrapper.setStyleSheet(GUIStyles.checkbox_wrapper_style())
            self.tau_checkboxes.append(tau_checkbox_wrapper)
            self.widgets = [self.add_tau_btn] + self.tau_checkboxes
        for checkbox in  self.tau_checkboxes:            
            self.tau_grid.addWidget(checkbox)     

        
    def on_tau_toggled(self, state, tau):  
        if state:
            self.main_window.selected_tau.append(int(tau))
        else:
            self.main_window.selected_tau.remove(int(tau))
        self.main_window.settings.setValue(SETTINGS_TAU, json.dumps(self.main_window.selected_tau))

    def open_add_tau_popup(self):    
        self.popup = AddTauPopup(self.main_window)
        self.popup.save_tau_clicked.connect(self.on_add_tau)
        self.popup.show()

    def on_add_tau(self, tau):  
        self.main_window.taus.append(tau)
        self.main_window.taus.sort()
        self.main_window.settings.setValue(SETTINGS_TAUS_INPUTS, json.dumps(self.main_window.taus))
        while self.tau_checkboxes:
            checkbox = self.tau_checkboxes.pop() 
            checkbox.deleteLater() 
        self.widgets = [self.add_tau_btn] + self.tau_checkboxes     
        while self.tau_grid.count():
            widget = self.tau_grid.takeAt(0).widget()
        if widget:
            widget.deleteLater()
        self.update_tau_checkboxes()  
        self.update_layout()

    def on_remove_tau(self, state, tau):      
        self.main_window.taus.remove(tau)
        self.main_window.taus.sort()
        self.main_window.settings.setValue(SETTINGS_TAUS_INPUTS, json.dumps(self.main_window.taus))
        if tau in self.main_window.selected_tau:
            self.main_window.selected_tau.remove(tau)
            self.main_window.settings.setValue(SETTINGS_TAU, json.dumps(self.main_window.selected_tau))
        while self.tau_checkboxes:
            checkbox = self.tau_checkboxes.pop() 
            checkbox.deleteLater() 
        self.widgets = [self.add_tau_btn] + self.tau_checkboxes     
        while self.tau_grid.count():
            widget = self.tau_grid.takeAt(0).widget()
        if widget:
            widget.deleteLater()
        self.update_tau_checkboxes()  
        self.update_layout()
    

    def update_layout(self):    
        screen_width = self.main_window.width()
        if screen_width < 500:
            num_columns = 4
        elif 500 <= screen_width <= 1200:
            num_columns = 6
        elif 1201 <= screen_width <= 1450:
            num_columns = 10
        else:
            num_columns = 12
        for i, widget in enumerate(self.widgets):
            row, col = divmod(i, num_columns)
            self.tau_grid.addWidget(widget, row, col)



class AddTauPopup(QWidget):
    save_tau_clicked = pyqtSignal(int)

    def __init__(self, window):
        super().__init__()
        self.main_window = window
        self.setWindowTitle("FCS - Add tau")
        TitlebarIcon.setup(self)
        GUIStyles.customize_theme(self, bg= QColor(20, 20, 20))
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(layout)
        popup_desc_1 = "Enter the tau value you wish to add, following these guidelines:"
        popup_desc_2 = "1. Value must be between 1 and 1,000,000 us."
        popup_desc_3 = "2. Avoid duplicates."
        popup_desc_4 = "3. Ensure the value is not smaller than the selected bin-width, if configured."
        self.label_1 = QLabel(popup_desc_1)
        self.label_2 = QLabel(popup_desc_2)
        self.label_3 = QLabel(popup_desc_3)
        self.label_4 = QLabel(popup_desc_4)
        self.input_field = QLineEdit()
        self.input_field.setStyleSheet(GUIStyles.set_input_number_style())
        validator = QIntValidator(1, 1000000) 
        self.input_field.setValidator(validator)
        self.input_field.textChanged.connect(self.on_tau_value_changed)
        self.buttons_row = QHBoxLayout()
        self.apply_btn = QPushButton("APPLY")
        self.apply_btn.setEnabled(False)
        self.apply_btn.setStyleSheet(GUIStyles.add_tau_btn_style())
        self.apply_btn.clicked.connect(self.on_apply_clicked)
        self.buttons_row.addStretch(1)
        self.buttons_row.addWidget(self.apply_btn)
        layout.addWidget(self.label_1)
        layout.addWidget(self.label_2)
        layout.addWidget(self.label_3)
        layout.addWidget(self.label_4)
        layout.addSpacing(10) 
        layout.addWidget(self.input_field)
        layout.addSpacing(20) 
        layout.addStretch(1) 
        layout.addLayout(self.buttons_row)
        self.setLayout(layout)
        self.main_window.widgets[ADD_TAU_POPUP] = self

    def on_tau_value_changed(self, text):
        value_valid = self.is_tau_value_valid(text)
        self.apply_btn.setEnabled(value_valid)

    def is_tau_value_valid(self, tau):
        if not tau or not tau.isdigit():
            return False
        tau_int = int(tau)    
        return (
            tau_int >= 1 
            and tau_int <= 1000000 
            and tau_int not in self.main_window.taus
            and tau_int >= self.main_window.bin_width_micros
            ) 


    def on_apply_clicked(self):        
        tau_value = int(self.input_field.text())
        self.save_tau_clicked.emit(tau_value)  
        self.close()
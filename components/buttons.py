
import os
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QSizePolicy
from PyQt6.QtCore import QPropertyAnimation, QSize, QRect, QEasingCurve
from PyQt6.QtGui import QIcon
from components.resource_path import resource_path
from components.gui_styles import GUIStyles
from components.controls_bar_builder import ControlsBarBuilder
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
            self.app.channel_checkboxes
        )
        self.app.control_inputs[START_BUTTON] = start_button
        self.app.control_inputs[STOP_BUTTON] = stop_button
        self.app.control_inputs[RESET_BUTTON] = reset_button
        return buttons_row_layout 

    def start_button_pressed(self):    
        return

    def stop_button_pressed(self):
        return

    def reset_button_pressed(self):
        return        
               



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
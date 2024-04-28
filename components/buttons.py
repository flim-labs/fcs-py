import os
import re
import json
import flim_labs
from PyQt6.QtWidgets import  QWidget, QPushButton, QCheckBox, QHBoxLayout, QGridLayout, QVBoxLayout, QLabel
from PyQt6.QtCore import QPropertyAnimation, Qt
from PyQt6.QtGui import QIcon, QPixmap, QColor
from components.intensity_tracing_controller import IntensityTracingButtonsActions
from components.logo_utilities import TitlebarIcon
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
            self.app.enabled_channels
        )
        self.app.control_inputs[START_BUTTON] = start_button
        self.app.control_inputs[STOP_BUTTON] = stop_button
        self.app.control_inputs[RESET_BUTTON] = reset_button
        return buttons_row_layout 

    def start_button_pressed(self):
        open_popup = len(self.app.intensity_plots_to_show) == 0
        if open_popup: 
            popup = PlotsConfigPopup(self.app, start_acquisition=True)
            popup.show()
        else: 
            IntensityTracingButtonsActions.start_button_pressed(self.app)       

    def stop_button_pressed(self):
        IntensityTracingButtonsActions.stop_button_pressed(self.app)

    def reset_button_pressed(self):
        IntensityTracingButtonsActions.reset_button_pressed(self.app)        
               


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



class PlotsConfigPopup(QWidget):
    def __init__(self, window, start_acquisition = False):
        super().__init__()
        self.app = window
        self.setWindowTitle("FCS - Plots config")
        TitlebarIcon.setup(self)
        GUIStyles.customize_theme(self, bg= QColor(20, 20, 20))
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        desc = QLabel("To avoid cluttering the interface, only a maximum of 4 intensity tracing charts and 4 G(t) curves will be displayed. However, all charts can be reconstructed by exporting the acquired data. Please select the intensity tracing charts and G(t) curves you would like to be shown.")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        layout.addSpacing(20)
        intensity_prompt = QLabel("INTENSITY TRACING PLOTS (MAX 4):")
        intensity_prompt.setObjectName("prompt_text")
        gt_prompt = QLabel("G(T) PLOTS (MAX 4):")
        gt_prompt.setObjectName("prompt_text")
        self.intensity_ch_grid = QGridLayout()
        self.intensity_checkboxes = []
        self.intensity_checkboxes_wrappers = []
        self.gt_corr_grid = QGridLayout()
        self.gt_checkboxes = []
        self.gt_checkboxes_wrappers = []
        layout.addWidget(intensity_prompt)
        if len(self.app.enabled_channels) == 0:
            layout.addLayout(self.set_data_empty_row("No channels enabled."))
        else:
            self.init_intensity_grid()
            layout.addLayout(self.intensity_ch_grid) 
        layout.addSpacing(20)       
        layout.addWidget(gt_prompt)
        if all(any(value is False for value in sublist) for sublist in self.app.ch_correlations):
            layout.addLayout(self.set_data_empty_row("No channels correlations configured."))
        else:
            self.init_gt_grid() 
            layout.addLayout(self.gt_corr_grid) 
        
        self.start_btn = QPushButton("START")
        self.start_btn.setEnabled(len(self.app.intensity_plots_to_show) > 0)
        self.start_btn.setStyleSheet(GUIStyles.channels_btn_style(base="#FB8C00", hover="#FFA726", pressed="#FB8C00", text="white")) 
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_btn.clicked.connect(self.start_acquisition)  
        
        if start_acquisition is True:
            layout.addSpacing(20)
            row_btn = QHBoxLayout()
            row_btn.addStretch(1)
            row_btn.addWidget(self.start_btn)
            layout.addLayout(row_btn)
            
              
        self.setLayout(layout)
        self.setStyleSheet(GUIStyles.plots_config_popup_style())
        self.app.widgets[PLOTS_CONFIG_POPUP] = self

    def init_gt_grid(self):
        corr_data = self.get_cleaned_correlations()
        for index, (ch1, ch2) in enumerate(corr_data):
            checkbox = self.set_checkboxes(f"Channel {ch1 + 1} - Channel {ch2 + 1}", "gt")
            gt_plot_to_show = [tuple(item) if isinstance(item, list) else item for item in self.app.gt_plots_to_show]
            isChecked = (ch1, ch2) in gt_plot_to_show
            checkbox.setChecked(isChecked)
        self.update_layout(self.gt_checkboxes_wrappers, self.gt_corr_grid, "gt")     


    def init_intensity_grid(self):
        self.app.enabled_channels.sort()
        for ch in self.app.enabled_channels:
            checkbox = self.set_checkboxes(f"Channel {ch + 1}", "intensity")
            isChecked = ch in self.app.intensity_plots_to_show
            checkbox.setChecked(isChecked)
            if len(self.app.intensity_plots_to_show) >=4 and ch not in self.app.intensity_plots_to_show:
                checkbox.setEnabled(False)
        self.update_layout(self.intensity_checkboxes_wrappers, self.intensity_ch_grid, "intensity")        


    def set_checkboxes(self, text, typology):
        checkbox_wrapper = QWidget()
        checkbox_wrapper.setObjectName(f"tau_checkbox_wrapper")
        row = QHBoxLayout()
        checkbox = QCheckBox(text)
        checkbox.setStyleSheet(GUIStyles.set_tau_checkbox_style(color = "#FB8C00" if typology == 'intensity' else "#31c914" ))
        checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
        checkbox.toggled.connect(lambda state, checkbox=checkbox: self.on_ch_intensity_toggled(state, checkbox) if typology == 'intensity' else self.on_ch_gt_toggled(state, checkbox) )
        row.addWidget(checkbox)
        checkbox_wrapper.setLayout(row)
        checkbox_wrapper.setStyleSheet(GUIStyles.checkbox_wrapper_style())
        if typology == 'intensity':
            self.intensity_checkboxes_wrappers.append(checkbox_wrapper)
            self.intensity_checkboxes.append(checkbox)
        else:
            self.gt_checkboxes_wrappers.append(checkbox_wrapper)
            self.gt_checkboxes.append(checkbox)
        return checkbox  

    def set_data_empty_row(self, text):    
        row = QHBoxLayout()
        remove_icon_label = QLabel()
        remove_icon_label.setPixmap(QPixmap(resource_path("assets/close-icon-red.png")).scaledToWidth(15))
        label = QLabel(text)
        label.setStyleSheet("color: #c90404;")
        row.addWidget(remove_icon_label)
        row.addWidget(label)
        row.addStretch(1)
        return row

    def update_layout(self, widgets, grid, typology):       
        screen_width = self.width()
        if screen_width < 500:
            num_columns = 4 if typology == 'intensity' else 2
        elif 500 <= screen_width <= 1200:
            num_columns = 6 if typology == 'intensity' else 4
        elif 1201 <= screen_width <= 1450:
            num_columns = 8 if typology == 'intensity' else 6
        else:
            num_columns = 12 if typology == 'intensity' else 7
        for i, widget in enumerate(widgets):
            row, col = divmod(i, num_columns)
            grid.addWidget(widget, row, col)

    def on_ch_intensity_toggled(self, state, checkbox):
        label_text = checkbox.text() 
        ch_num_index = self.extract_channel_from_label(label_text) 
        if state:
            if ch_num_index not in self.app.intensity_plots_to_show:
                self.app.intensity_plots_to_show.append(ch_num_index)
        else:
            if ch_num_index in self.app.intensity_plots_to_show:
                self.app.intensity_plots_to_show.remove(ch_num_index) 
        self.app.intensity_plots_to_show.sort()        
        self.app.settings.setValue(SETTINGS_INTENSITY_PLOTS_TO_SHOW, json.dumps(self.app.intensity_plots_to_show)) 
        if len(self.app.intensity_plots_to_show) >= 4:
            for checkbox in self.intensity_checkboxes:
                if checkbox.text() != label_text and not checkbox.isChecked():
                    checkbox.setEnabled(False)
        else:
            for checkbox in self.intensity_checkboxes:
                checkbox.setEnabled(True)
        if hasattr(self, 'start_btn'):        
            start_btn_enabled = len(self.app.intensity_plots_to_show) > 0
            self.start_btn.setEnabled(start_btn_enabled)


    def on_ch_gt_toggled(self, state, checkbox):    
        label_text = checkbox.text() 
        gt_plot_to_show = [tuple(item) if isinstance(item, list) else item for item in self.app.gt_plots_to_show]
        corr_tuple = self.extract_correlation_from_label(label_text) 
        if state:
            if corr_tuple not in gt_plot_to_show:
                gt_plot_to_show.append(corr_tuple)
        else:
            if corr_tuple in gt_plot_to_show:
                gt_plot_to_show.remove(corr_tuple) 
        self.app.gt_plots_to_show = gt_plot_to_show        
        self.app.settings.setValue(SETTINGS_GT_PLOTS_TO_SHOW, json.dumps(gt_plot_to_show)) 
        if len(gt_plot_to_show) >= 4:
            for checkbox in self.gt_checkboxes:
                if checkbox.text() != label_text and not checkbox.isChecked():
                    checkbox.setEnabled(False)
        else:
            for checkbox in self.gt_checkboxes:
                checkbox.setEnabled(True) 
        if hasattr(self, 'start_btn'):        
            start_btn_enabled = len(self.app.intensity_plots_to_show) > 0       
            self.start_btn.setEnabled(start_btn_enabled)        
                    
                           
    def start_acquisition(self):
        self.close()
        IntensityTracingButtonsActions.start_button_pressed(self.app)
       


    def extract_channel_from_label(self,text):
        ch = re.search(r'\d+', text).group()  
        ch_num = int(ch) 
        ch_num_index = ch_num - 1 
        return ch_num_index

    def extract_correlation_from_label(self, text):
        numbers = re.findall(r'\d+', text)
        corr_tuples = tuple(int(num) - 1 for num in numbers)
        return corr_tuples
    
    
    def get_cleaned_correlations(self):
        filtered_corr = sorted([(x, y) if x < y else (y, x) for x, y, boolean in self.app.ch_correlations if boolean])
        unique_filtered_data = []
        seen_pairs = set()
        for pair in filtered_corr:
            if pair not in seen_pairs:
                unique_filtered_data.append(pair)
                seen_pairs.add(pair)
        return unique_filtered_data      
        

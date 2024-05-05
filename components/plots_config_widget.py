from functools import partial
import os
import re
import json
from PyQt6.QtWidgets import  QWidget, QPushButton, QCheckBox, QHBoxLayout, QGridLayout, QVBoxLayout, QLabel, QScrollArea, QApplication
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QColor
from components.correlations_matrix import ChCorrelationsMatrix
from components.intensity_tracing_controller import IntensityTracingButtonsActions
from components.logo_utilities import TitlebarIcon
from components.resource_path import resource_path
from components.gui_styles import GUIStyles
from components.settings import *
current_path = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_path))



class PlotsConfigPopup(QWidget):
    def __init__(self, window, start_acquisition=False):
        super().__init__()
        self.app = window
        self.setWindowTitle("FCS - Plots config")
        TitlebarIcon.setup(self)
        GUIStyles.customize_theme(self, bg=QColor(20, 20, 20))
        
        scroll_area = QScrollArea()  
        scroll_area.setWidgetResizable(True) 
        inner_widget = QWidget()  
        
        self.layout = QVBoxLayout(inner_widget)  
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.layouts = {}

        corr_matrix_prompt = QLabel("CHANNELS CORRELATIONS:")
        corr_matrix_prompt.setObjectName("prompt_text")
        self.correlations_matrix = ChCorrelationsMatrix(self.app)
        self.correlations_matrix.correlations_saved.connect(partial(self.init_gt_grid, update= True))
        
        desc = QLabel("To avoid cluttering the interface, only a maximum of 4 intensity tracing charts and 4 G(t) curves will be displayed. However, all charts can be reconstructed by exporting the acquired data. Please select the intensity tracing charts and G(t) curves you would like to be shown.")
        desc.setWordWrap(True)
        if start_acquisition:
            self.layout.addWidget(corr_matrix_prompt)
            self.layout.addWidget(self.correlations_matrix)
        self.layout.addWidget(desc)
        self.layout.addSpacing(20)
        intensity_prompt = QLabel("INTENSITY TRACING PLOTS (MAX 4):")
        intensity_prompt.setObjectName("prompt_text")
        intensity_prompt_note = QLabel("Note: For optimization purposes, if multiple acquisitions are chosen to be executed, the layout will be automatically reconfigured to display only CPS per channel, regardless of the selected number of graphs to be shown.")
        intensity_prompt_note.setWordWrap(True)
        gt_prompt = QLabel("G(T) PLOTS (MAX 4):")
        gt_prompt.setObjectName("prompt_text")
        self.intensity_ch_grid = QGridLayout()
        self.intensity_checkboxes = []
        self.intensity_checkboxes_wrappers = []
        self.gt_corr_grid = QGridLayout()
        self.gt_checkboxes = []
        self.gt_checkboxes_wrappers = []
        self.layout.addWidget(intensity_prompt)
        self.layout.addWidget(intensity_prompt_note)
        if len(self.app.enabled_channels) == 0:
            self.layout.addLayout(self.set_data_empty_row("No channels enabled."))
        else:
            self.init_intensity_grid()
            self.layout.addLayout(self.intensity_ch_grid)
        self.layout.addSpacing(20)
        self.layout.addWidget(gt_prompt)
        if all(any(value is False for value in sublist) for sublist in self.app.ch_correlations) and start_acquisition is False:
            row = self.set_data_empty_row("No channels correlations configured.")
            self.layout.addLayout(row)
        else:
            self.init_gt_grid(update=False)
            self.layout.addLayout(self.gt_corr_grid)

        self.start_btn = QPushButton("START")
        self.start_btn.setEnabled(len(self.app.gt_plots_to_show) > 0)
        self.start_btn.setStyleSheet(GUIStyles.channels_btn_style(base="#FB8C00", hover="#FFA726", pressed="#FB8C00", text="white"))
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_btn.clicked.connect(self.start_acquisition)

        if start_acquisition:
            self.layout.addSpacing(20)
            row_btn = QHBoxLayout()
            row_btn.addStretch(1)
            row_btn.addWidget(self.start_btn)
            self.layout.addLayout(row_btn)

        inner_widget.setLayout(self.layout)
        scroll_area.setWidget(inner_widget)
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)
        self.setStyleSheet(GUIStyles.plots_config_popup_style())
        self.app.widgets[PLOTS_CONFIG_POPUP] = self
        self.resize(self.app.settings.value("size", QSize(CORR_POPUP_WIDTH, CORR_POPUP_HEIGHT)))
        self.move(self.app.settings.value("pos", QApplication.primaryScreen().geometry().center() - self.frameGeometry().center()))
        
        
        
    def init_gt_grid(self, update=False):
        if update is True:
            self.gt_checkboxes.clear()
            self.gt_checkboxes_wrappers.clear()
            for i in reversed(range(self.gt_corr_grid.count())):
                widget = self.gt_corr_grid.itemAt(i).widget()
                if widget is not None:
                    widget.setParent(None)
                    widget.deleteLater()  
        QApplication.processEvents()            
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
        checkbox.toggled.connect(partial(self.on_ch_intensity_toggled, checkbox=checkbox) if typology == 'intensity' else partial(self.on_ch_gt_toggled, checkbox=checkbox))
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
            start_btn_enabled = len(self.app.gt_plots_to_show) > 0
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
            start_btn_enabled = len(self.app.gt_plots_to_show) > 0    
            self.start_btn.setEnabled(start_btn_enabled)        
                    
                           
    def start_acquisition(self):
        self.close()
        if self.start_acquisition is True:
            self.correlations_matrix.save_correlations()
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
        filtered_corr = [(x, y) for x, y, boolean in self.app.ch_correlations if boolean]
        return filtered_corr      
        
